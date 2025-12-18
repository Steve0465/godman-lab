"""Vision AI integration for image and video analysis using GPT-4V, Claude, and Gemini."""

import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

import requests

logger = logging.getLogger(__name__)


class VisionError(Exception):
    """Base exception for vision analysis errors."""
    pass


class VisionAnalyzer:
    """Universal vision analyzer supporting multiple providers.
    
    Supports:
    - OpenAI GPT-4V (gpt-4-vision-preview, gpt-4o) - images only
    - Anthropic Claude 3 (opus, sonnet, haiku) - images only
    - Google Gemini 1.5 (pro, flash) - images and native video
    
    Attributes:
        provider: Vision API provider ('openai', 'claude', or 'gemini')
        api_key: API key for the provider
        model: Specific model to use
    """
    
    def __init__(
        self,
        provider: Literal["openai", "claude", "gemini"] = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize vision analyzer.
        
        Args:
            provider: 'openai', 'claude', or 'gemini'
            api_key: API key (reads from env if not provided)
            model: Specific model name (uses best default if not provided)
        """
        self.provider = provider.lower()
        
        if self.provider == "openai":
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            self.model = model or "gpt-4o"  # Latest GPT-4 with vision
            self.api_url = "https://api.openai.com/v1/chat/completions"
            if not self.api_key:
                raise VisionError("Missing OPENAI_API_KEY environment variable")
        
        elif self.provider == "claude":
            self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            self.model = model or "claude-3-opus-20240229"  # Best accuracy
            self.api_url = "https://api.anthropic.com/v1/messages"
            if not self.api_key:
                raise VisionError("Missing ANTHROPIC_API_KEY environment variable")
        
        elif self.provider == "gemini":
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
            self.model = model or "gemini-1.5-pro-latest"  # Best for video
            if not self.api_key:
                raise VisionError("Missing GEMINI_API_KEY environment variable")
            
            # Initialize Gemini client
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.genai = genai
                self.gemini_model = genai.GenerativeModel(self.model)
            except ImportError:
                raise VisionError("google-generativeai package not installed. Run: pip install google-generativeai")
        
        else:
            raise VisionError(f"Unsupported provider: {provider}")
        
        logger.info(f"VisionAnalyzer initialized: {self.provider} / {self.model}")
    
    def analyze(
        self,
        image: Union[Path, str, bytes],
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Analyze an image with a text prompt.
        
        Args:
            image: Path to image file, URL, or raw bytes
            prompt: Text prompt describing what to analyze
            max_tokens: Maximum response length
            temperature: Sampling temperature (0.0-1.0, lower = more deterministic)
            
        Returns:
            Dictionary with analysis results:
                - content: The AI's response text
                - raw_response: Full API response
                
        Raises:
            VisionError: If analysis fails
            
        Example:
            >>> analyzer = VisionAnalyzer(provider="openai")
            >>> result = analyzer.analyze(
            ...     "pool_part.jpg",
            ...     "Identify this pool part. Return part number, manufacturer, confidence."
            ... )
            >>> print(result["content"])
        """
        if self.provider == "openai":
            return self._analyze_openai(image, prompt, max_tokens, temperature)
        elif self.provider == "claude":
            return self._analyze_claude(image, prompt, max_tokens, temperature)
        else:
            return self._analyze_gemini(image, prompt, max_tokens, temperature)
    
    def _analyze_openai(
        self,
        image: Union[Path, str, bytes],
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Analyze with OpenAI GPT-4V."""
        # Prepare image
        image_data = self._prepare_image(image)
        
        # Build request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data if image_data.startswith("http") 
                                       else f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            logger.info(f"Sending request to OpenAI ({self.model})")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            logger.info(f"OpenAI analysis complete ({len(content)} chars)")
            
            return {
                "content": content,
                "raw_response": data,
                "provider": "openai",
                "model": self.model
            }
            
        except requests.RequestException as e:
            logger.error(f"OpenAI API error: {e}")
            raise VisionError(f"OpenAI API request failed: {e}")
    
    def _analyze_claude(
        self,
        image: Union[Path, str, bytes],
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Analyze with Anthropic Claude 3."""
        # Prepare image
        image_data = self._prepare_image(image)
        
        # Claude doesn't support URLs, needs base64
        if image_data.startswith("http"):
            # Download and convert
            img_response = requests.get(image_data, timeout=30)
            img_response.raise_for_status()
            image_data = base64.b64encode(img_response.content).decode()
        
        # Build request
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        try:
            logger.info(f"Sending request to Claude ({self.model})")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["content"][0]["text"]
            
            logger.info(f"Claude analysis complete ({len(content)} chars)")
            
            return {
                "content": content,
                "raw_response": data,
                "provider": "claude",
                "model": self.model
            }
            
        except requests.RequestException as e:
            logger.error(f"Claude API error: {e}")
            raise VisionError(f"Claude API request failed: {e}")
    
    def _analyze_gemini(
        self,
        image: Union[Path, str, bytes],
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Analyze with Google Gemini."""
        try:
            # Prepare image file
            if isinstance(image, bytes):
                # Write bytes to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(image)
                    image_path = Path(tmp.name)
            elif isinstance(image, str) and image.startswith("http"):
                # Download URL to temp file
                import tempfile
                response = requests.get(image, timeout=30)
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(response.content)
                    image_path = Path(tmp.name)
            else:
                image_path = Path(image)
                if not image_path.exists():
                    raise VisionError(f"Image file not found: {image_path}")
            
            # Upload file to Gemini
            logger.info(f"Uploading image to Gemini: {image_path}")
            uploaded_file = self.genai.upload_file(str(image_path))
            
            # Generate content
            logger.info(f"Generating content with Gemini ({self.model})")
            response = self.gemini_model.generate_content(
                [prompt, uploaded_file],
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            content = response.text
            logger.info(f"Gemini analysis complete ({len(content)} chars)")
            
            return {
                "content": content,
                "raw_response": {"text": content, "usage": response.usage_metadata},
                "provider": "gemini",
                "model": self.model
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise VisionError(f"Gemini API request failed: {e}")
    
    def _prepare_image(self, image: Union[Path, str, bytes]) -> str:
        """Prepare image for API request.
        
        Args:
            image: Path, URL, or bytes
            
        Returns:
            Base64 encoded string or URL
        """
        # If it's a URL, return as-is
        if isinstance(image, str) and image.startswith("http"):
            return image
        
        # If it's bytes, encode to base64
        if isinstance(image, bytes):
            return base64.b64encode(image).decode()
        
        # If it's a path, read and encode
        image_path = Path(image)
        if not image_path.exists():
            raise VisionError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        return base64.b64encode(image_bytes).decode()
    
    def analyze_pool_part(
        self,
        image: Union[Path, str, bytes],
        include_alternatives: bool = True
    ) -> Dict[str, Any]:
        """Specialized method for pool part identification.
        
        Args:
            image: Image of pool part
            include_alternatives: Whether to suggest alternative parts
            
        Returns:
            Structured part information:
                - part_number: Primary part number
                - manufacturer: Manufacturer name
                - confidence: Confidence score (0-1)
                - description: Part description
                - alternatives: List of alternative matches (if requested)
                
        Example:
            >>> analyzer = VisionAnalyzer()
            >>> result = analyzer.analyze_pool_part("pump_housing.jpg")
            >>> print(f"Part: {result['part_number']} ({result['confidence']:.1%})")
        """
        prompt = """Analyze this pool equipment part image.

Identify:
1. Part number (exact alphanumeric code visible on the part)
2. Manufacturer (Hayward, Pentair, Jandy, Sta-Rite, etc.)
3. Part description (what it is)
4. Your confidence in this identification (0.0 to 1.0)
"""
        
        if include_alternatives:
            prompt += """5. Alternative part numbers that might match
6. Compatible cross-reference parts from other manufacturers
"""
        
        prompt += """
Return ONLY valid JSON in this exact format:
{
    "part_number": "SPX1091Z2",
    "manufacturer": "Hayward",
    "description": "Super Pump Housing Assembly",
    "confidence": 0.95,
    "alternatives": [
        {"part_number": "SPX1091Z1", "confidence": 0.75, "description": "Older model"}
    ],
    "equivalents": ["PEN-355331", "JAC-39310700"]
}

If you cannot identify the part, set confidence to 0.0 and explain why in the description.
"""
        
        result = self.analyze(image, prompt, max_tokens=500, temperature=0.1)
        
        # Parse JSON from response
        import json
        try:
            # Extract JSON from markdown code blocks if present
            content = result["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            parsed["raw_response"] = result["raw_response"]
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw content: {result['content']}")
            raise VisionError(f"Invalid JSON response from vision API: {e}")
    
    def analyze_video(
        self,
        video: Union[Path, str],
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Analyze a video file (Gemini only).
        
        Args:
            video: Path to video file or URL
            prompt: Text prompt describing what to analyze
            max_tokens: Maximum response length
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Dictionary with analysis results:
                - content: The AI's response text
                - raw_response: Full API response
                
        Raises:
            VisionError: If provider doesn't support video or analysis fails
            
        Example:
            >>> analyzer = VisionAnalyzer(provider="gemini")
            >>> result = analyzer.analyze_video(
            ...     "pool_inspection.mp4",
            ...     "Identify all pool equipment visible in this video"
            ... )
            >>> print(result["content"])
        """
        if self.provider != "gemini":
            raise VisionError(f"Video analysis only supported by Gemini provider (current: {self.provider})")
        
        try:
            # Prepare video file
            if isinstance(video, str) and video.startswith("http"):
                # Download URL to temp file
                import tempfile
                response = requests.get(video, timeout=120, stream=True)
                response.raise_for_status()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp.write(chunk)
                    video_path = Path(tmp.name)
            else:
                video_path = Path(video)
                if not video_path.exists():
                    raise VisionError(f"Video file not found: {video_path}")
            
            # Upload video to Gemini
            logger.info(f"Uploading video to Gemini: {video_path} (this may take a while)")
            uploaded_file = self.genai.upload_file(str(video_path))
            
            # Wait for processing
            logger.info("Waiting for video processing...")
            import time
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = self.genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise VisionError("Video processing failed on Gemini servers")
            
            # Generate content
            logger.info(f"Generating content with Gemini ({self.model})")
            response = self.gemini_model.generate_content(
                [prompt, uploaded_file],
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            content = response.text
            logger.info(f"Gemini video analysis complete ({len(content)} chars)")
            
            return {
                "content": content,
                "raw_response": {"text": content, "usage": response.usage_metadata},
                "provider": "gemini",
                "model": self.model,
                "video_duration": uploaded_file.video_metadata.duration if hasattr(uploaded_file, 'video_metadata') else None
            }
            
        except Exception as e:
            logger.error(f"Gemini video analysis error: {e}")
            raise VisionError(f"Gemini video analysis failed: {e}")
    
    def extract_frames(
        self,
        video: Union[Path, str],
        interval_seconds: int = 5,
        max_frames: Optional[int] = None
    ) -> List[bytes]:
        """Extract frames from video at regular intervals.
        
        Args:
            video: Path to video file
            interval_seconds: Extract one frame every N seconds
            max_frames: Maximum number of frames to extract (None = all)
            
        Returns:
            List of frame images as JPEG bytes
            
        Raises:
            VisionError: If extraction fails
            
        Example:
            >>> analyzer = VisionAnalyzer()
            >>> frames = analyzer.extract_frames("video.mp4", interval=5)
            >>> for i, frame in enumerate(frames):
            ...     result = analyzer.analyze(frame, "Describe this frame")
        """
        try:
            import cv2
        except ImportError:
            raise VisionError("opencv-python package required for frame extraction. Run: pip install opencv-python")
        
        video_path = Path(video)
        if not video_path.exists():
            raise VisionError(f"Video file not found: {video_path}")
        
        logger.info(f"Extracting frames from: {video_path}")
        cap = cv2.VideoCapture(str(video_path))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frames = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            
            # Extract frame at intervals
            if frame_num % (fps * interval_seconds) == 0:
                _, buffer = cv2.imencode('.jpg', frame)
                frames.append(buffer.tobytes())
                logger.debug(f"Extracted frame {len(frames)} at {frame_num / fps:.1f}s")
                
                if max_frames and len(frames) >= max_frames:
                    break
        
        cap.release()
        logger.info(f"Extracted {len(frames)} frames from video")
        return frames


__all__ = ["VisionAnalyzer", "VisionError"]

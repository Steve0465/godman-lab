"""Video Tool - Process and analyze video files."""
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil


class VideoTool:
    """Base video processing tool using ffmpeg."""
    
    name = "video"
    description = "Process video files with ffmpeg"
    
    def execute(self, action: str, video_path: str, **kwargs) -> Dict[str, Any]:
        """
        Execute video processing action.
        
        Args:
            action: Action to perform (extract_frames, get_info, convert, etc.)
            video_path: Path to video file
            **kwargs: Action-specific parameters
        
        Returns:
            Dictionary with results
        """
        video_file = Path(video_path)
        
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if action == "get_info":
            return self._get_video_info(video_file)
        elif action == "extract_frames":
            return self._extract_frames(video_file, **kwargs)
        elif action == "create_thumbnail":
            return self._create_thumbnail(video_file, **kwargs)
        elif action == "extract_audio":
            return self._extract_audio(video_file, **kwargs)
        elif action == "convert":
            return self._convert_video(video_file, **kwargs)
        elif action == "trim":
            return self._trim_video(video_file, **kwargs)
        elif action == "get_metadata":
            return self._get_metadata(video_file)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def _get_video_info(self, video_file: Path) -> Dict[str, Any]:
        """Get detailed video information using ffprobe."""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Extract key information
            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                {}
            )
            audio_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "audio"),
                {}
            )
            
            format_info = data.get("format", {})
            
            return {
                "file": str(video_file),
                "duration": float(format_info.get("duration", 0)),
                "size_bytes": int(format_info.get("size", 0)),
                "size_mb": round(int(format_info.get("size", 0)) / (1024 * 1024), 2),
                "format": format_info.get("format_name"),
                "video": {
                    "codec": video_stream.get("codec_name"),
                    "width": video_stream.get("width"),
                    "height": video_stream.get("height"),
                    "fps": eval(video_stream.get("r_frame_rate", "0/1")),
                    "bitrate": video_stream.get("bit_rate")
                },
                "audio": {
                    "codec": audio_stream.get("codec_name"),
                    "sample_rate": audio_stream.get("sample_rate"),
                    "channels": audio_stream.get("channels")
                } if audio_stream else None
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffprobe failed: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Failed to get video info: {e}")
    
    def _extract_frames(self, video_file: Path, **kwargs) -> Dict[str, Any]:
        """Extract frames from video."""
        output_dir = Path(kwargs.get("output_dir", video_file.parent / f"{video_file.stem}_frames"))
        output_dir.mkdir(exist_ok=True)
        
        fps = kwargs.get("fps", 1)  # Extract 1 frame per second by default
        start_time = kwargs.get("start_time")  # Optional start time in seconds
        duration = kwargs.get("duration")  # Optional duration in seconds
        max_frames = kwargs.get("max_frames")  # Optional max number of frames
        
        output_pattern = output_dir / "frame_%04d.jpg"
        
        cmd = ["ffmpeg", "-i", str(video_file)]
        
        if start_time:
            cmd.extend(["-ss", str(start_time)])
        
        if duration:
            cmd.extend(["-t", str(duration)])
        
        cmd.extend([
            "-vf", f"fps={fps}",
            "-q:v", "2",  # High quality JPEG
        ])
        
        if max_frames:
            cmd.extend(["-frames:v", str(max_frames)])
        
        cmd.append(str(output_pattern))
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Count extracted frames
            frames = list(output_dir.glob("frame_*.jpg"))
            
            return {
                "success": True,
                "output_dir": str(output_dir),
                "frames_extracted": len(frames),
                "frames": [str(f) for f in sorted(frames)]
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Frame extraction failed: {e.stderr.decode()}")
    
    def _create_thumbnail(self, video_file: Path, **kwargs) -> Dict[str, Any]:
        """Create thumbnail from video."""
        output_path = kwargs.get("output_path")
        if not output_path:
            output_path = video_file.parent / f"{video_file.stem}_thumb.jpg"
        
        timestamp = kwargs.get("timestamp", "00:00:01")  # Default to 1 second
        
        cmd = [
            "ffmpeg",
            "-ss", timestamp,
            "-i", str(video_file),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path),
            "-y"  # Overwrite
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return {
                "success": True,
                "thumbnail": str(output_path)
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Thumbnail creation failed: {e.stderr.decode()}")
    
    def _extract_audio(self, video_file: Path, **kwargs) -> Dict[str, Any]:
        """Extract audio from video."""
        output_path = kwargs.get("output_path")
        if not output_path:
            output_path = video_file.parent / f"{video_file.stem}.mp3"
        
        format = kwargs.get("format", "mp3")
        bitrate = kwargs.get("bitrate", "192k")
        
        cmd = [
            "ffmpeg",
            "-i", str(video_file),
            "-vn",  # No video
            "-acodec", "libmp3lame" if format == "mp3" else format,
            "-ab", bitrate,
            str(output_path),
            "-y"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return {
                "success": True,
                "audio_file": str(output_path),
                "format": format
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio extraction failed: {e.stderr.decode()}")
    
    def _convert_video(self, video_file: Path, **kwargs) -> Dict[str, Any]:
        """Convert video to different format."""
        output_format = kwargs.get("format", "mp4")
        output_path = kwargs.get("output_path")
        if not output_path:
            output_path = video_file.parent / f"{video_file.stem}_converted.{output_format}"
        
        codec = kwargs.get("codec", "libx264")
        quality = kwargs.get("quality", "medium")  # ultrafast, fast, medium, slow
        
        cmd = [
            "ffmpeg",
            "-i", str(video_file),
            "-c:v", codec,
            "-preset", quality,
            "-c:a", "aac",
            str(output_path),
            "-y"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return {
                "success": True,
                "output_file": str(output_path),
                "format": output_format
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Video conversion failed: {e.stderr.decode()}")
    
    def _trim_video(self, video_file: Path, **kwargs) -> Dict[str, Any]:
        """Trim video to specified duration."""
        start_time = kwargs.get("start_time", 0)
        duration = kwargs.get("duration")
        end_time = kwargs.get("end_time")
        
        output_path = kwargs.get("output_path")
        if not output_path:
            output_path = video_file.parent / f"{video_file.stem}_trimmed{video_file.suffix}"
        
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", str(video_file),
        ]
        
        if duration:
            cmd.extend(["-t", str(duration)])
        elif end_time:
            cmd.extend(["-to", str(end_time)])
        
        cmd.extend([
            "-c", "copy",  # Copy without re-encoding (fast)
            str(output_path),
            "-y"
        ])
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return {
                "success": True,
                "output_file": str(output_path)
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Video trimming failed: {e.stderr.decode()}")
    
    def _get_metadata(self, video_file: Path) -> Dict[str, Any]:
        """Get video metadata using exiftool."""
        if not shutil.which("exiftool"):
            return {"error": "exiftool not installed"}
        
        try:
            cmd = ["exiftool", "-json", str(video_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)[0]
            
            return {
                "file": str(video_file),
                "create_date": data.get("CreateDate"),
                "modify_date": data.get("ModifyDate"),
                "duration": data.get("Duration"),
                "image_size": data.get("ImageSize"),
                "video_frame_rate": data.get("VideoFrameRate"),
                "file_type": data.get("FileType"),
                "mime_type": data.get("MIMEType"),
                "gps": {
                    "latitude": data.get("GPSLatitude"),
                    "longitude": data.get("GPSLongitude")
                } if data.get("GPSLatitude") else None,
                "camera": {
                    "make": data.get("Make"),
                    "model": data.get("Model"),
                    "software": data.get("Software")
                } if data.get("Make") else None
            }
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"exiftool failed: {e.stderr}")


class VideoBatchProcessor:
    """Batch process multiple video files."""
    
    name = "video_batch"
    description = "Batch process multiple video files"
    
    def execute(self, action: str, input_dir: str, **kwargs) -> Dict[str, Any]:
        """
        Batch process videos in directory.
        
        Args:
            action: Action to perform on all videos
            input_dir: Directory containing videos
            **kwargs: Action-specific parameters
        
        Returns:
            Dictionary with batch results
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Directory not found: {input_dir}")
        
        # Find all video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.flv', '.wmv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(input_path.glob(f"*{ext}"))
            video_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        if not video_files:
            return {
                "success": False,
                "message": "No video files found",
                "files_processed": 0
            }
        
        results = {
            "total_files": len(video_files),
            "processed": 0,
            "failed": 0,
            "results": []
        }
        
        video_tool = VideoTool()
        
        for video_file in video_files:
            try:
                result = video_tool.execute(action, str(video_file), **kwargs)
                results["results"].append({
                    "file": str(video_file),
                    "status": "success",
                    "result": result
                })
                results["processed"] += 1
            except Exception as e:
                results["results"].append({
                    "file": str(video_file),
                    "status": "failed",
                    "error": str(e)
                })
                results["failed"] += 1
        
        return results


class VideoAnalyzer:
    """Analyze video content using frame extraction and Vision API."""
    
    name = "video_analyzer"
    description = "Analyze video content using AI vision"
    
    def execute(self, video_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze video content.
        
        Args:
            video_path: Path to video file
            **kwargs: Analysis parameters
        
        Returns:
            Dictionary with analysis results
        """
        video_file = Path(video_path)
        
        if not video_file.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Step 1: Get video info
        video_tool = VideoTool()
        info = video_tool.execute("get_info", video_path)
        
        # Step 2: Extract sample frames
        fps = kwargs.get("fps", 0.2)  # Extract 1 frame every 5 seconds
        max_frames = kwargs.get("max_frames", 10)
        
        frames_result = video_tool.execute(
            "extract_frames",
            video_path,
            fps=fps,
            max_frames=max_frames
        )
        
        # Step 3: Analyze frames (placeholder - would use Vision API)
        # In real implementation, would call OpenAI Vision API on each frame
        
        analysis = {
            "video_info": info,
            "frames_analyzed": len(frames_result.get("frames", [])),
            "frame_dir": frames_result.get("output_dir"),
            "content_summary": "Video analysis placeholder - integrate Vision API",
            "key_scenes": [],
            "objects_detected": [],
            "text_detected": [],
            "suggested_tags": []
        }
        
        return analysis

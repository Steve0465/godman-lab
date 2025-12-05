"""Video Workflow - End-to-end video processing and organization."""
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from engine import BaseWorkflow


class VideoOrganizerWorkflow(BaseWorkflow):
    """
    Organize videos by analyzing metadata and content.
    
    Steps:
    1. Scan directory for videos
    2. Extract metadata (date, location, camera)
    3. Create thumbnail for each video
    4. Analyze content with Vision API (sample frames)
    5. Categorize and tag videos
    6. Organize into folders by date/category
    7. Generate index/catalog
    """
    
    name = "video_organizer"
    description = "Analyze and organize video files intelligently"
    
    def __init__(self, engine):
        """Initialize workflow with engine reference."""
        self.engine = engine
    
    def run(self, input_dir: str, **kwargs) -> Dict[str, Any]:
        """
        Run the video organizer workflow.
        
        Args:
            input_dir: Directory containing videos
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with workflow results
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all video files
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.flv', '.wmv']
        video_files = []
        for ext in video_extensions:
            video_files.extend(input_path.glob(f"**/*{ext}"))
            video_files.extend(input_path.glob(f"**/*{ext.upper()}"))
        
        if not video_files:
            return {
                "status": "no_files",
                "message": "No video files found",
                "files_processed": 0
            }
        
        results = {
            "total_files": len(video_files),
            "processed": 0,
            "failed": 0,
            "videos": [],
            "categories": {}
        }
        
        # Process each video
        for video_file in video_files:
            try:
                video_data = self._process_single_video(video_file, **kwargs)
                results["videos"].append(video_data)
                results["processed"] += 1
                
                # Track categories
                category = video_data.get("category", "uncategorized")
                results["categories"][category] = results["categories"].get(category, 0) + 1
                
            except Exception as e:
                results["failed"] += 1
                results["videos"].append({
                    "file": str(video_file),
                    "error": str(e),
                    "status": "failed"
                })
        
        # Generate summary
        if results["processed"] > 0:
            results["summary"] = self._generate_summary(results["videos"])
        
        # Organize files if requested
        if kwargs.get("organize_files", False):
            results["organization"] = self._organize_files(results["videos"], input_path, **kwargs)
        
        # Generate catalog
        if kwargs.get("create_catalog", True):
            results["catalog"] = self._create_catalog(results["videos"], input_path)
        
        return results
    
    def _process_single_video(self, video_file: Path, **kwargs) -> Dict[str, Any]:
        """Process a single video file."""
        
        # Step 1: Get video info
        info = self.engine.call_tool("video", action="get_info", video_path=str(video_file))
        
        # Step 2: Get metadata
        try:
            metadata = self.engine.call_tool("video", action="get_metadata", video_path=str(video_file))
        except:
            metadata = {}
        
        # Step 3: Create thumbnail
        try:
            thumbnail = self.engine.call_tool(
                "video",
                action="create_thumbnail",
                video_path=str(video_file)
            )
        except:
            thumbnail = None
        
        # Step 4: Analyze content (if enabled)
        analysis = None
        if kwargs.get("analyze_content", False):
            try:
                analysis = self.engine.call_tool(
                    "video_analyzer",
                    video_path=str(video_file),
                    fps=0.2,
                    max_frames=5
                )
            except:
                pass
        
        # Step 5: Categorize
        category = self._categorize_video(info, metadata, analysis)
        
        video_data = {
            "file": str(video_file),
            "filename": video_file.name,
            "info": info,
            "metadata": metadata,
            "thumbnail": thumbnail.get("thumbnail") if thumbnail else None,
            "category": category,
            "analysis": analysis,
            "status": "success"
        }
        
        return video_data
    
    def _categorize_video(self, info: Dict, metadata: Dict, analysis: Dict = None) -> str:
        """Categorize video based on metadata and analysis."""
        filename = info.get("file", "").lower()
        
        # Check filename for hints
        if any(word in filename for word in ["receipt", "scan", "document"]):
            return "documents"
        elif any(word in filename for word in ["pool", "service", "cleaning"]):
            return "pool_work"
        elif any(word in filename for word in ["family", "vacation", "trip"]):
            return "personal"
        elif any(word in filename for word in ["meeting", "presentation", "zoom"]):
            return "work"
        elif any(word in filename for word in ["tutorial", "howto", "demo"]):
            return "educational"
        
        # Check duration - very short videos might be clips
        duration = info.get("duration", 0)
        if duration < 30:
            return "clips"
        elif duration > 1800:  # 30 minutes
            return "long_form"
        
        # Check resolution
        width = info.get("video", {}).get("width", 0)
        if width >= 3840:
            return "4k_video"
        
        # Default
        return "uncategorized"
    
    def _generate_summary(self, videos: list) -> Dict[str, Any]:
        """Generate summary of processed videos."""
        successful = [v for v in videos if v.get("status") == "success"]
        
        total_duration = sum(v.get("info", {}).get("duration", 0) for v in successful)
        total_size = sum(v.get("info", {}).get("size_bytes", 0) for v in successful)
        
        # Resolution distribution
        resolutions = {}
        for video in successful:
            width = video.get("info", {}).get("video", {}).get("width")
            height = video.get("info", {}).get("video", {}).get("height")
            if width and height:
                res = f"{width}x{height}"
                resolutions[res] = resolutions.get(res, 0) + 1
        
        # Format distribution
        formats = {}
        for video in successful:
            fmt = video.get("info", {}).get("format")
            if fmt:
                formats[fmt] = formats.get(fmt, 0) + 1
        
        return {
            "total_videos": len(successful),
            "total_duration_seconds": round(total_duration, 2),
            "total_duration_hours": round(total_duration / 3600, 2),
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 2),
            "avg_duration": round(total_duration / len(successful), 2) if successful else 0,
            "resolutions": resolutions,
            "formats": formats
        }
    
    def _organize_files(self, videos: list, base_path: Path, **kwargs) -> Dict[str, Any]:
        """Organize video files into folders."""
        output_dir = Path(kwargs.get("output_dir", base_path / "organized_videos"))
        output_dir.mkdir(exist_ok=True)
        
        organize_by = kwargs.get("organize_by", "category")  # category, date, or size
        
        moved_files = 0
        
        for video in videos:
            if video.get("status") != "success":
                continue
            
            source = Path(video["file"])
            
            # Determine target folder
            if organize_by == "category":
                subfolder = video.get("category", "uncategorized")
            elif organize_by == "date":
                create_date = video.get("metadata", {}).get("create_date", "")
                if create_date:
                    # Parse date and create YYYY-MM folder
                    try:
                        date_obj = datetime.strptime(create_date.split()[0], "%Y:%m:%d")
                        subfolder = date_obj.strftime("%Y-%m")
                    except:
                        subfolder = "unknown_date"
                else:
                    subfolder = "unknown_date"
            elif organize_by == "size":
                size_mb = video.get("info", {}).get("size_mb", 0)
                if size_mb < 10:
                    subfolder = "small"
                elif size_mb < 100:
                    subfolder = "medium"
                else:
                    subfolder = "large"
            else:
                subfolder = "other"
            
            # Create target folder
            target_folder = output_dir / subfolder
            target_folder.mkdir(exist_ok=True)
            
            # Move or copy file
            target_file = target_folder / source.name
            
            if kwargs.get("copy_files", False):
                import shutil
                shutil.copy2(source, target_file)
            else:
                source.rename(target_file)
            
            moved_files += 1
        
        return {
            "organized": True,
            "output_dir": str(output_dir),
            "files_moved": moved_files,
            "organize_by": organize_by
        }
    
    def _create_catalog(self, videos: list, base_path: Path) -> Dict[str, Any]:
        """Create a catalog/index of all videos."""
        catalog_file = base_path / "video_catalog.json"
        
        catalog = {
            "created_at": datetime.now().isoformat(),
            "total_videos": len([v for v in videos if v.get("status") == "success"]),
            "videos": []
        }
        
        for video in videos:
            if video.get("status") != "success":
                continue
            
            catalog["videos"].append({
                "filename": video.get("filename"),
                "path": video.get("file"),
                "duration": video.get("info", {}).get("duration"),
                "size_mb": video.get("info", {}).get("size_mb"),
                "resolution": f"{video.get('info', {}).get('video', {}).get('width')}x{video.get('info', {}).get('video', {}).get('height')}",
                "category": video.get("category"),
                "thumbnail": video.get("thumbnail"),
                "create_date": video.get("metadata", {}).get("create_date")
            })
        
        # Write catalog
        import json
        with open(catalog_file, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        return {
            "catalog_created": True,
            "catalog_file": str(catalog_file),
            "videos_cataloged": len(catalog["videos"])
        }


class VideoToFramesWorkflow(BaseWorkflow):
    """Extract frames from videos for analysis."""
    
    name = "video_to_frames"
    description = "Extract frames from videos and analyze with Vision API"
    
    def __init__(self, engine):
        self.engine = engine
    
    def run(self, video_path: str, **kwargs) -> Dict[str, Any]:
        """
        Extract frames and analyze.
        
        Args:
            video_path: Path to video file
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with results
        """
        # Extract frames
        frames_result = self.engine.call_tool(
            "video",
            action="extract_frames",
            video_path=video_path,
            fps=kwargs.get("fps", 1),
            max_frames=kwargs.get("max_frames", 20)
        )
        
        # Analyze each frame if Vision API enabled
        if kwargs.get("analyze_frames", False):
            frame_analyses = []
            for frame_path in frames_result.get("frames", [])[:10]:  # Limit to 10
                try:
                    analysis = self.engine.call_tool(
                        "vision",
                        image_path=frame_path,
                        prompt="Describe what you see in this frame"
                    )
                    frame_analyses.append({
                        "frame": frame_path,
                        "analysis": analysis
                    })
                except:
                    pass
            
            frames_result["frame_analyses"] = frame_analyses
        
        return frames_result

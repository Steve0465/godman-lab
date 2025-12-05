"""
Personal Data Collector - Learns about you from your system and files.
Ethical collection with full transparency and user control.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class PersonalDataCollector:
    """
    Collects data about the user to build a comprehensive profile.
    Everything is stored locally and under user control.
    """
    
    def __init__(self, profile_dir: Path = None):
        self.profile_dir = profile_dir or Path.home() / ".godman" / "profile"
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path = self.profile_dir / "profile.json"
        self.profile = self._load_profile()
    
    def _load_profile(self) -> Dict:
        """Load existing profile or create new one."""
        if self.profile_path.exists():
            with open(self.profile_path) as f:
                return json.load(f)
        return {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "user": {},
            "preferences": {},
            "business": {},
            "relationships": {},
            "communication_style": {},
            "habits": {},
            "goals": {},
            "data_sources": []
        }
    
    def save_profile(self):
        """Save profile to disk."""
        self.profile["last_updated"] = datetime.now().isoformat()
        with open(self.profile_path, 'w') as f:
            json.dump(self.profile, f, indent=2)
        logger.info(f"Profile saved to {self.profile_path}")
    
    def analyze_filesystem(self, paths: List[Path] = None) -> Dict:
        """
        Analyze filesystem structure and file patterns.
        Learn about projects, organization style, work habits.
        """
        if paths is None:
            paths = [
                Path.home() / "Desktop",
                Path.home() / "Documents",
                Path.home() / "Downloads",
                Path("/Users/stephengodman/godman-lab")
            ]
        
        analysis = {
            "directories": {},
            "file_types": {},
            "projects": [],
            "organization_patterns": []
        }
        
        for path in paths:
            if not path.exists():
                continue
            
            logger.info(f"Analyzing {path}...")
            
            for root, dirs, files in os.walk(path):
                root_path = Path(root)
                
                # Skip hidden and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = root_path / file
                    ext = file_path.suffix.lower()
                    
                    # Count file types
                    analysis["file_types"][ext] = analysis["file_types"].get(ext, 0) + 1
                    
                    # Detect projects
                    if file in ['package.json', 'requirements.txt', 'Dockerfile', 'README.md']:
                        analysis["projects"].append({
                            "path": str(root_path),
                            "type": self._detect_project_type(root_path),
                            "marker": file
                        })
        
        self.profile["data_sources"].append({
            "type": "filesystem",
            "timestamp": datetime.now().isoformat(),
            "paths": [str(p) for p in paths]
        })
        
        return analysis
    
    def _detect_project_type(self, path: Path) -> str:
        """Detect what kind of project this is."""
        if (path / "package.json").exists():
            return "node"
        if (path / "requirements.txt").exists():
            return "python"
        if (path / "Dockerfile").exists():
            return "docker"
        if (path / "README.md").exists():
            return "documented"
        return "unknown"
    
    def analyze_documents(self, docs_dir: Path = None) -> Dict:
        """
        Analyze documents to understand business, interests, relationships.
        """
        if docs_dir is None:
            docs_dir = Path.home() / "Documents"
        
        analysis = {
            "business_docs": [],
            "personal_docs": [],
            "topics": {}
        }
        
        if not docs_dir.exists():
            return analysis
        
        logger.info(f"Analyzing documents in {docs_dir}...")
        
        # Look for key business/personal indicators
        for file_path in docs_dir.rglob("*"):
            if not file_path.is_file():
                continue
            
            name_lower = file_path.name.lower()
            
            # Business indicators
            if any(word in name_lower for word in ['invoice', 'receipt', 'contract', 'estimate', 'pool', 'truck']):
                analysis["business_docs"].append(str(file_path))
            
            # Personal indicators
            if any(word in name_lower for word in ['family', 'personal', 'medical', 'tax']):
                analysis["personal_docs"].append(str(file_path))
        
        self.profile["data_sources"].append({
            "type": "documents",
            "timestamp": datetime.now().isoformat(),
            "path": str(docs_dir)
        })
        
        return analysis
    
    def learn_communication_style(self, messages_dir: Path = None) -> Dict:
        """
        Analyze communication patterns from messages, emails, etc.
        NOTE: Requires local backups - won't access iCloud directly.
        """
        analysis = {
            "tone": "unknown",
            "common_phrases": [],
            "response_patterns": [],
            "contact_frequency": {}
        }
        
        logger.info("Communication style analysis requires local message backups")
        logger.info("Export messages from Messages.app or email client first")
        
        # This is a placeholder - actual implementation would parse message exports
        
        return analysis
    
    def identify_goals_and_interests(self) -> Dict:
        """
        Identify user goals from project names, document titles, etc.
        """
        goals = {
            "business": [],
            "personal": [],
            "technical": [],
            "learning": []
        }
        
        # Analyze project names
        if "projects" in self.profile.get("filesystem_analysis", {}):
            for project in self.profile["filesystem_analysis"]["projects"]:
                path_str = project["path"].lower()
                
                if "godman-lab" in path_str or "automation" in path_str:
                    goals["technical"].append("Build automation systems")
                if "pool" in path_str:
                    goals["business"].append("Manage pool business operations")
                if "truck" in path_str or "f250" in path_str:
                    goals["business"].append("Track vehicle maintenance")
        
        return goals
    
    def generate_questions(self) -> List[str]:
        """
        Generate questions to fill gaps in understanding.
        """
        questions = []
        
        # Basic info
        if not self.profile["user"].get("name"):
            questions.append("What's your full name?")
        if not self.profile["user"].get("occupation"):
            questions.append("What's your primary occupation?")
        
        # Business
        if not self.profile["business"].get("type"):
            questions.append("What type of business do you run? (I see pool-related files)")
        if not self.profile["business"].get("pain_points"):
            questions.append("What are your biggest business challenges right now?")
        
        # Preferences
        if not self.profile["preferences"].get("work_hours"):
            questions.append("What are your typical work hours?")
        if not self.profile["preferences"].get("communication"):
            questions.append("How do you prefer to be notified? (email, text, dashboard)")
        
        # Goals
        if not self.profile["goals"].get("automation"):
            questions.append("What tasks would you most like to automate?")
        if not self.profile["goals"].get("timeline"):
            questions.append("What's your timeline for getting this system fully operational?")
        
        # AI preferences
        questions.append("How autonomous should I be? (ask permission vs. just do it)")
        questions.append("What information should I never touch without asking?")
        questions.append("Should I wake you up for urgent issues, or queue them for morning?")
        
        return questions
    
    def update_from_answers(self, answers: Dict[str, str]):
        """Update profile with user-provided answers."""
        for key, value in answers.items():
            # Smart routing to correct profile section
            if key in ["name", "occupation", "location"]:
                self.profile["user"][key] = value
            elif "business" in key or "company" in key:
                self.profile["business"][key] = value
            elif "prefer" in key or "like" in key:
                self.profile["preferences"][key] = value
            elif "goal" in key or "want" in key:
                self.profile["goals"][key] = value
            else:
                self.profile[key] = value
        
        self.save_profile()
    
    def full_analysis_report(self) -> str:
        """Generate comprehensive report."""
        report = []
        report.append("=" * 60)
        report.append("PERSONAL AI PROFILE ANALYSIS")
        report.append("=" * 60)
        report.append("")
        
        # Filesystem
        if "filesystem_analysis" in self.profile:
            fs = self.profile["filesystem_analysis"]
            report.append("📁 FILESYSTEM ANALYSIS:")
            report.append(f"  - Projects found: {len(fs.get('projects', []))}")
            report.append(f"  - File types: {len(fs.get('file_types', {}))}")
            report.append("")
        
        # Documents
        if "document_analysis" in self.profile:
            docs = self.profile["document_analysis"]
            report.append("📄 DOCUMENT ANALYSIS:")
            report.append(f"  - Business documents: {len(docs.get('business_docs', []))}")
            report.append(f"  - Personal documents: {len(docs.get('personal_docs', []))}")
            report.append("")
        
        # Questions
        questions = self.generate_questions()
        if questions:
            report.append("❓ QUESTIONS TO IMPROVE UNDERSTANDING:")
            for i, q in enumerate(questions[:10], 1):
                report.append(f"  {i}. {q}")
            report.append("")
        
        report.append("=" * 60)
        report.append(f"Profile saved to: {self.profile_path}")
        report.append("=" * 60)
        
        return "\n".join(report)

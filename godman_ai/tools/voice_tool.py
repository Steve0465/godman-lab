"""
Voice Tool - Speech-to-text and text-to-speech
"""
from ..engine import BaseTool
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VoiceTool(BaseTool):
    """Handle voice input/output"""
    
    name = "voice"
    description = "Speech-to-text and text-to-speech capabilities"
    
    def run(self, action: str, **kwargs):
        """
        Voice operations
        
        Args:
            action: 'listen' or 'speak'
        """
        if action == "listen":
            return self.speech_to_text(**kwargs)
        elif action == "speak":
            return self.text_to_speech(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def speech_to_text(self, audio_file: str = None, duration: int = 5):
        """Convert speech to text"""
        try:
            import speech_recognition as sr
        except ImportError:
            return {"error": "speech_recognition not installed. Run: pip install SpeechRecognition pyaudio"}
        
        recognizer = sr.Recognizer()
        
        if audio_file:
            # Process audio file
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
        else:
            # Listen from microphone
            with sr.Microphone() as source:
                logger.info(f"Listening for {duration} seconds...")
                audio = recognizer.listen(source, timeout=duration)
        
        try:
            text = recognizer.recognize_google(audio)
            return {"status": "success", "text": text}
        except sr.UnknownValueError:
            return {"error": "Could not understand audio"}
        except sr.RequestError as e:
            return {"error": f"Recognition error: {e}"}
    
    def text_to_speech(self, text: str, output_file: str = None):
        """Convert text to speech"""
        try:
            import pyttsx3
        except ImportError:
            return {"error": "pyttsx3 not installed. Run: pip install pyttsx3"}
        
        engine = pyttsx3.init()
        
        if output_file:
            engine.save_to_file(text, output_file)
            engine.runAndWait()
            return {"status": "success", "file": output_file}
        else:
            engine.say(text)
            engine.runAndWait()
            return {"status": "success", "spoken": True}

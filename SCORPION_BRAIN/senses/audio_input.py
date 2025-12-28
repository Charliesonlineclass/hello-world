"""
SCORPION_BRAIN Audio Input
==========================
Audio perception capabilities: transcription, microphone capture.

Features:
- Audio recording from microphone
- Speech-to-text transcription
- Audio file processing
"""

import subprocess
import wave
import struct
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioSegment:
    """A segment of audio with metadata."""
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Result from audio transcription."""
    text: str
    segments: List[AudioSegment] = field(default_factory=list)
    language: str = "en"
    duration: float = 0.0
    confidence: float = 0.0


@dataclass
class AudioRecording:
    """A recorded audio file."""
    path: str
    duration: float
    sample_rate: int
    channels: int
    format: str
    timestamp: datetime


def record_audio(
    output_path: str = None,
    duration: float = 5.0,
    sample_rate: int = 16000,
    device: str = None
) -> Dict[str, Any]:
    """
    Record audio from microphone.

    Args:
        output_path: Path to save recording (auto-generated if None)
        duration: Recording duration in seconds
        sample_rate: Audio sample rate
        device: Specific audio device to use

    Returns:
        Dict with recording info
    """
    timestamp = datetime.now()

    if output_path is None:
        output_path = f"/tmp/recording_{timestamp.strftime('%Y%m%d_%H%M%S')}.wav"

    result = {
        "status": "pending",
        "path": output_path,
        "duration_requested": duration,
        "sample_rate": sample_rate,
        "timestamp": timestamp.isoformat()
    }

    try:
        # Try different recording methods
        if _has_command("arecord"):
            # ALSA recorder (Linux)
            cmd = [
                "arecord",
                "-d", str(int(duration)),
                "-r", str(sample_rate),
                "-f", "S16_LE",
                "-c", "1",
                output_path
            ]
            if device:
                cmd.extend(["-D", device])

        elif _has_command("rec"):
            # SoX recorder
            cmd = [
                "rec",
                "-r", str(sample_rate),
                "-c", "1",
                output_path,
                "trim", "0", str(duration)
            ]

        elif _has_command("ffmpeg"):
            # FFmpeg (cross-platform)
            cmd = [
                "ffmpeg",
                "-f", "alsa" if _is_linux() else "avfoundation",
                "-i", device or "default",
                "-t", str(duration),
                "-ar", str(sample_rate),
                "-ac", "1",
                "-y",  # Overwrite output
                output_path
            ]

        else:
            # No recorder available - create placeholder
            result["status"] = "simulated"
            result["message"] = "No audio recorder available"
            result["duration"] = duration
            _create_silent_wav(output_path, duration, sample_rate)
            return result

        # Execute recording
        proc = subprocess.run(cmd, capture_output=True, timeout=duration + 5)

        if proc.returncode == 0 and Path(output_path).exists():
            result["status"] = "success"
            result["duration"] = _get_wav_duration(output_path)
        else:
            result["status"] = "error"
            result["error"] = proc.stderr.decode() if proc.stderr else "Recording failed"

    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "Recording timed out"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def transcribe_audio(
    audio_path: str,
    language: str = "en",
    model: str = "base"
) -> Dict[str, Any]:
    """
    Transcribe audio to text.

    Args:
        audio_path: Path to audio file
        language: Language code
        model: Transcription model (base, small, medium, large)

    Returns:
        Dict with transcription results
    """
    result = {
        "status": "pending",
        "audio": audio_path,
        "language": language,
        "model": model
    }

    if not Path(audio_path).exists():
        result["status"] = "error"
        result["error"] = f"Audio file not found: {audio_path}"
        return result

    try:
        # Try Whisper (if available)
        if _has_python_module("whisper"):
            result = _transcribe_with_whisper(audio_path, language, model)

        # Try vosk (if available)
        elif _has_python_module("vosk"):
            result = _transcribe_with_vosk(audio_path, language)

        # Try external whisper.cpp
        elif _has_command("whisper"):
            proc = subprocess.run(
                ["whisper", audio_path, "--language", language, "--output_format", "txt"],
                capture_output=True,
                timeout=120
            )
            if proc.returncode == 0:
                result["status"] = "success"
                result["text"] = proc.stdout.decode('utf-8', errors='ignore').strip()
            else:
                result["status"] = "error"
                result["error"] = proc.stderr.decode() if proc.stderr else "Transcription failed"

        else:
            # Fallback: simulate transcription
            result["status"] = "simulated"
            result["text"] = "[Transcription not available - install whisper or vosk]"
            result["message"] = "No transcription engine installed"

    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "Transcription timed out"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _transcribe_with_whisper(audio_path: str, language: str, model: str) -> Dict:
    """Transcribe using OpenAI Whisper."""
    try:
        import whisper

        model_obj = whisper.load_model(model)
        result = model_obj.transcribe(audio_path, language=language)

        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "confidence": seg.get("avg_logprob", 0)
            })

        return {
            "status": "success",
            "text": result["text"],
            "language": result.get("language", language),
            "segments": segments,
            "engine": "whisper"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _transcribe_with_vosk(audio_path: str, language: str) -> Dict:
    """Transcribe using Vosk."""
    try:
        from vosk import Model, KaldiRecognizer
        import json

        # Would need model path configuration
        model = Model(lang=language)

        with wave.open(audio_path, "rb") as wf:
            recognizer = KaldiRecognizer(model, wf.getframerate())
            recognizer.SetWords(True)

            text_parts = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    res = json.loads(recognizer.Result())
                    text_parts.append(res.get("text", ""))

            final = json.loads(recognizer.FinalResult())
            text_parts.append(final.get("text", ""))

            return {
                "status": "success",
                "text": " ".join(text_parts),
                "language": language,
                "engine": "vosk"
            }

    except Exception as e:
        return {"status": "error", "error": str(e)}


# Helper functions

def _has_command(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _has_python_module(module: str) -> bool:
    """Check if a Python module is available."""
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def _is_linux() -> bool:
    """Check if running on Linux."""
    import platform
    return platform.system() == "Linux"


def _get_wav_duration(path: str) -> float:
    """Get duration of a WAV file."""
    try:
        with wave.open(path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate)
    except Exception:
        return 0.0


def _create_silent_wav(path: str, duration: float, sample_rate: int):
    """Create a silent WAV file for testing."""
    try:
        num_samples = int(duration * sample_rate)
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            # Write silence
            for _ in range(num_samples):
                wf.writeframes(struct.pack('<h', 0))
    except Exception as e:
        logger.error(f"Failed to create silent WAV: {e}")


class AudioInput:
    """
    High-level interface for audio input.

    Usage:
        audio = AudioInput()
        recording = audio.record(duration=5)
        text = audio.transcribe(recording.path)
    """

    def __init__(self, output_dir: str = "/tmp/scorpion_audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recording_count = 0

    def record(self, duration: float = 5.0) -> AudioRecording:
        """Record audio from microphone."""
        self.recording_count += 1
        path = str(self.output_dir / f"recording_{self.recording_count}.wav")

        result = record_audio(path, duration)

        return AudioRecording(
            path=result.get("path", path),
            duration=result.get("duration", duration),
            sample_rate=result.get("sample_rate", 16000),
            channels=1,
            format="wav",
            timestamp=datetime.now()
        )

    def transcribe(self, audio_path: str, language: str = "en") -> str:
        """Transcribe audio file to text."""
        result = transcribe_audio(audio_path, language)
        return result.get("text", "")

    def record_and_transcribe(self, duration: float = 5.0) -> TranscriptionResult:
        """Record audio and transcribe in one step."""
        recording = self.record(duration)
        result = transcribe_audio(recording.path)

        segments = []
        for seg in result.get("segments", []):
            segments.append(AudioSegment(
                start_time=seg.get("start", 0),
                end_time=seg.get("end", 0),
                text=seg.get("text", ""),
                confidence=seg.get("confidence", 0)
            ))

        return TranscriptionResult(
            text=result.get("text", ""),
            segments=segments,
            language=result.get("language", "en"),
            duration=recording.duration,
            confidence=result.get("confidence", 0)
        )


if __name__ == "__main__":
    # Demo
    audio = AudioInput()

    print("=== Audio Recording (simulated) ===")
    result = record_audio(duration=2.0)
    print(f"Status: {result['status']}")
    print(f"Path: {result['path']}")

    print("\n=== Transcription (simulated) ===")
    trans_result = transcribe_audio("/tmp/test.wav")
    print(f"Status: {trans_result['status']}")
    print(f"Text: {trans_result.get('text', 'N/A')[:100]}")

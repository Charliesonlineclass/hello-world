"""
SCORPION_BRAIN Ears - Audio Processing
======================================
Audio processing capabilities for SCORPION.

Features:
- Audio transcription (via Whisper/Otter)
- Speech detection
- Audio stream processing
- Voice activity detection
"""

import subprocess
import wave
import struct
import os
from typing import Dict, List, Any, Optional, Generator
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class AudioInfo:
    """Information about an audio file."""
    path: str
    duration: float
    sample_rate: int
    channels: int
    format: str
    size_bytes: int


@dataclass
class TranscriptionSegment:
    """A segment of transcribed audio."""
    start: float
    end: float
    text: str
    confidence: float
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    text: str
    segments: List[TranscriptionSegment]
    duration: float
    language: str
    confidence: float


def transcribe_audio(path: str, language: str = "en") -> Dict[str, Any]:
    """
    Transcribe audio file to text.

    Tries multiple backends:
    1. OpenAI Whisper (local)
    2. whisper.cpp
    3. Otter integration (placeholder)
    4. Vosk (offline)

    Args:
        path: Path to audio file
        language: Language code

    Returns:
        Dict with transcription results
    """
    result = {
        "path": path,
        "status": "pending",
        "language": language,
        "timestamp": datetime.now().isoformat()
    }

    if not Path(path).exists():
        result["status"] = "error"
        result["error"] = "Audio file not found"
        return result

    # Get audio info
    info = _get_audio_info(path)
    result["audio_info"] = info

    try:
        # Try whisper (Python library)
        try:
            import whisper

            model = whisper.load_model("base")
            whisper_result = model.transcribe(path, language=language)

            segments = []
            for seg in whisper_result.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                    "confidence": 0.9
                })

            result["status"] = "success"
            result["text"] = whisper_result["text"].strip()
            result["segments"] = segments
            result["engine"] = "whisper"
            result["confidence"] = 0.9
            return result

        except ImportError:
            pass

        # Try whisper.cpp via command line
        if _has_command("whisper"):
            proc = subprocess.run(
                ["whisper", path, "--language", language, "--output_format", "json"],
                capture_output=True,
                timeout=300
            )

            if proc.returncode == 0:
                # Parse JSON output
                try:
                    output = json.loads(proc.stdout.decode())
                    result["status"] = "success"
                    result["text"] = output.get("text", "")
                    result["segments"] = output.get("segments", [])
                    result["engine"] = "whisper.cpp"
                    return result
                except json.JSONDecodeError:
                    result["text"] = proc.stdout.decode().strip()
                    result["status"] = "success"
                    result["engine"] = "whisper.cpp"
                    return result

        # Try vosk (offline)
        try:
            from vosk import Model, KaldiRecognizer

            model = Model(lang=language)
            wf = wave.open(path, "rb")

            recognizer = KaldiRecognizer(model, wf.getframerate())
            recognizer.SetWords(True)

            text_parts = []
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    part = json.loads(recognizer.Result())
                    text_parts.append(part.get("text", ""))

            final = json.loads(recognizer.FinalResult())
            text_parts.append(final.get("text", ""))

            result["status"] = "success"
            result["text"] = " ".join(text_parts).strip()
            result["engine"] = "vosk"
            result["confidence"] = 0.8
            return result

        except ImportError:
            pass

        # Otter.ai placeholder
        result = _transcribe_with_otter(path, language)
        if result.get("status") == "success":
            return result

        # No engine available
        result["status"] = "unavailable"
        result["text"] = ""
        result["message"] = "No transcription engine available. Install: whisper, vosk, or configure Otter"

    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "Transcription timed out"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _transcribe_with_otter(path: str, language: str) -> Dict[str, Any]:
    """
    Transcribe using Otter.ai (placeholder for API integration).

    In production, this would:
    1. Upload audio to Otter API
    2. Poll for completion
    3. Return transcription

    For now, returns placeholder.
    """
    result = {
        "status": "unavailable",
        "engine": "otter",
        "message": "Otter.ai integration requires API key configuration"
    }

    # Check for Otter configuration
    otter_key = os.environ.get("OTTER_API_KEY")
    if not otter_key:
        return result

    # Placeholder for actual Otter API call
    # In production:
    # 1. POST audio to https://otter.ai/api/v1/speech
    # 2. Poll for transcription completion
    # 3. Return result

    result["message"] = "Otter API configured but not yet implemented"
    return result


def detect_speech(path: str) -> Dict[str, Any]:
    """
    Detect if audio contains speech.

    Args:
        path: Path to audio file

    Returns:
        Dict with detection results
    """
    result = {
        "path": path,
        "status": "pending",
        "has_speech": False,
        "confidence": 0.0
    }

    if not Path(path).exists():
        result["status"] = "error"
        result["error"] = "Audio file not found"
        return result

    try:
        # Try webrtcvad for voice activity detection
        try:
            import webrtcvad

            vad = webrtcvad.Vad(2)  # Aggressiveness 0-3

            # Read audio
            audio_data, sample_rate = _read_audio_for_vad(path)

            if audio_data is None:
                raise ValueError("Could not read audio")

            # Check frames for speech
            frame_duration = 30  # ms
            frame_size = int(sample_rate * frame_duration / 1000) * 2  # 2 bytes per sample

            speech_frames = 0
            total_frames = 0

            for i in range(0, len(audio_data) - frame_size, frame_size):
                frame = audio_data[i:i + frame_size]
                if len(frame) == frame_size:
                    total_frames += 1
                    if vad.is_speech(frame, sample_rate):
                        speech_frames += 1

            if total_frames > 0:
                speech_ratio = speech_frames / total_frames
                result["has_speech"] = speech_ratio > 0.1
                result["confidence"] = min(0.95, speech_ratio * 2)
                result["speech_ratio"] = speech_ratio
                result["status"] = "success"
                return result

        except ImportError:
            pass

        # Fallback: energy-based detection
        result = _detect_speech_energy(path)

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _detect_speech_energy(path: str) -> Dict[str, Any]:
    """Simple energy-based speech detection."""
    result = {
        "path": path,
        "status": "pending",
        "has_speech": False,
        "method": "energy"
    }

    try:
        with wave.open(path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            samples = struct.unpack(f"{len(frames)//2}h", frames)

            # Calculate RMS energy
            rms = (sum(s**2 for s in samples) / len(samples)) ** 0.5

            # Threshold for speech (adjust based on your needs)
            threshold = 500
            result["has_speech"] = rms > threshold
            result["energy_rms"] = rms
            result["confidence"] = min(0.8, rms / 2000)
            result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _read_audio_for_vad(path: str) -> tuple:
    """Read audio file for VAD processing."""
    try:
        with wave.open(path, 'rb') as wf:
            sample_rate = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            return frames, sample_rate
    except Exception:
        return None, None


def audio_to_text_stream(audio_source: str = "default") -> Generator[str, None, None]:
    """
    Stream audio to text (placeholder for real-time transcription).

    This is a placeholder for real-time streaming transcription.
    In production, would use:
    - Whisper streaming
    - Google Speech-to-Text streaming
    - Azure Speech Services

    Args:
        audio_source: Audio input source

    Yields:
        Transcribed text chunks
    """
    logger.info(f"Starting audio stream from: {audio_source}")

    # Placeholder implementation
    # In production, this would:
    # 1. Open audio stream from microphone/source
    # 2. Buffer audio chunks
    # 3. Send to streaming transcription API
    # 4. Yield partial results

    yield "[Streaming transcription not yet implemented]"
    yield "[Configure Whisper streaming or cloud API]"
    yield "[End of placeholder stream]"


def _get_audio_info(path: str) -> Dict:
    """Get audio file information."""
    info = {
        "path": path,
        "exists": Path(path).exists()
    }

    if not info["exists"]:
        return info

    try:
        with wave.open(path, 'rb') as wf:
            info["channels"] = wf.getnchannels()
            info["sample_rate"] = wf.getframerate()
            info["sample_width"] = wf.getsampwidth()
            info["frames"] = wf.getnframes()
            info["duration"] = wf.getnframes() / wf.getframerate()
            info["format"] = "wav"

        info["size_bytes"] = Path(path).stat().st_size

    except Exception as e:
        # Try ffprobe for other formats
        if _has_command("ffprobe"):
            try:
                proc = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", "-show_streams", path],
                    capture_output=True,
                    timeout=10
                )
                if proc.returncode == 0:
                    data = json.loads(proc.stdout.decode())
                    fmt = data.get("format", {})
                    info["duration"] = float(fmt.get("duration", 0))
                    info["format"] = fmt.get("format_name", "unknown")

                    for stream in data.get("streams", []):
                        if stream.get("codec_type") == "audio":
                            info["sample_rate"] = int(stream.get("sample_rate", 0))
                            info["channels"] = stream.get("channels", 0)
                            break
            except Exception:
                pass

        info["error"] = str(e)

    return info


def _has_command(cmd: str) -> bool:
    """Check if command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class Ears:
    """
    High-level interface for audio processing.

    Usage:
        ears = Ears()
        text = ears.listen("audio.wav")
        has_speech = ears.detect_speech("audio.wav")
    """

    def __init__(self):
        self.cache: Dict[str, Dict] = {}

    def listen(self, path: str, language: str = "en") -> str:
        """Transcribe audio file."""
        result = transcribe_audio(path, language)
        return result.get("text", "")

    def transcribe(self, path: str, language: str = "en") -> Dict:
        """Get full transcription result."""
        return transcribe_audio(path, language)

    def has_speech(self, path: str) -> bool:
        """Check if audio contains speech."""
        result = detect_speech(path)
        return result.get("has_speech", False)

    def get_info(self, path: str) -> Dict:
        """Get audio file information."""
        return _get_audio_info(path)

    def stream_listen(self, source: str = "default") -> Generator[str, None, None]:
        """Stream transcription from audio source."""
        return audio_to_text_stream(source)


if __name__ == "__main__":
    # Demo
    ears = Ears()

    print("=== Ears Module Demo ===")
    print("This module provides audio processing capabilities.")
    print("\nMethods available:")
    print("  ears.listen(path) -> transcribed text")
    print("  ears.transcribe(path) -> full result with segments")
    print("  ears.has_speech(path) -> bool")
    print("  ears.get_info(path) -> audio info")
    print("  ears.stream_listen() -> streaming transcription")

    # Test with sample path
    test_path = "/tmp/test_audio.wav"
    print(f"\nTesting with: {test_path}")

    info = ears.get_info(test_path)
    print(f"Audio info: {info}")

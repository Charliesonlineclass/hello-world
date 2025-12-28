"""
SCORPION_BRAIN Speech Output
============================
Text-to-speech with baby voice profiles.

Features:
- TTS generation
- Baby-specific voice profiles
- Audio playback
- Voice customization
"""

import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class VoiceProfile:
    """Voice settings for a baby."""
    name: str
    pitch: float  # 0.5 - 2.0 (1.0 = normal)
    speed: float  # 0.5 - 2.0 (1.0 = normal)
    voice_id: str  # System voice ID
    personality: str  # Description of speaking style


# Baby voice profiles
BABY_VOICE_PROFILES: Dict[str, VoiceProfile] = {
    "MARCUS": VoiceProfile(
        name="MARCUS",
        pitch=0.9,  # Slightly deeper
        speed=0.85,  # Thoughtful, slower
        voice_id="en-us",
        personality="Calm, methodical, pauses for emphasis"
    ),
    "VULCAN": VoiceProfile(
        name="VULCAN",
        pitch=0.95,
        speed=1.1,  # Faster, efficient
        voice_id="en-us",
        personality="Precise, technical, to-the-point"
    ),
    "HERMES": VoiceProfile(
        name="HERMES",
        pitch=1.1,  # Slightly higher
        speed=1.0,
        voice_id="en-us",
        personality="Expressive, friendly, engaging"
    ),
    "ATHENA": VoiceProfile(
        name="ATHENA",
        pitch=1.05,
        speed=0.95,
        voice_id="en-us",
        personality="Confident, strategic, commanding"
    ),
    "PHOENIX": VoiceProfile(
        name="PHOENIX",
        pitch=1.15,  # Higher, youthful
        speed=1.05,
        voice_id="en-us",
        personality="Curious, enthusiastic, energetic"
    )
}


@dataclass
class SpeechResult:
    """Result from speech generation."""
    text: str
    audio_path: Optional[str]
    duration: float
    voice_profile: str
    played: bool = False


def speak_text(
    text: str,
    baby_name: str = "HERMES",
    output_path: str = None,
    play_audio: bool = True
) -> Dict[str, Any]:
    """
    Convert text to speech.

    Args:
        text: Text to speak
        baby_name: Baby whose voice to use
        output_path: Path to save audio (optional)
        play_audio: Whether to play audio immediately

    Returns:
        Dict with speech result
    """
    # Get voice profile
    profile = BABY_VOICE_PROFILES.get(baby_name.upper(), BABY_VOICE_PROFILES["HERMES"])

    result = {
        "status": "pending",
        "text": text[:200],
        "baby": baby_name,
        "voice_profile": profile.name,
        "personality": profile.personality
    }

    if output_path is None:
        output_path = f"/tmp/speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

    try:
        # Try different TTS engines
        if _has_command("espeak-ng"):
            success = _speak_with_espeak_ng(text, output_path, profile)
        elif _has_command("espeak"):
            success = _speak_with_espeak(text, output_path, profile)
        elif _has_command("say"):  # macOS
            success = _speak_with_say(text, output_path, profile)
        elif _has_command("pico2wave"):  # SVOX
            success = _speak_with_pico(text, output_path, profile)
        elif _has_command("festival"):
            success = _speak_with_festival(text, output_path, profile)
        else:
            result["status"] = "simulated"
            result["message"] = "No TTS engine available"
            result["would_say"] = _format_for_baby(text, profile)
            return result

        if success and Path(output_path).exists():
            result["status"] = "success"
            result["audio_path"] = output_path

            # Play audio if requested
            if play_audio:
                played = _play_audio(output_path)
                result["played"] = played

            # Estimate duration (roughly 150 words per minute)
            word_count = len(text.split())
            result["estimated_duration"] = (word_count / 150) * 60 / profile.speed

        else:
            result["status"] = "error"
            result["error"] = "TTS generation failed"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _speak_with_espeak_ng(text: str, output_path: str, profile: VoiceProfile) -> bool:
    """Generate speech using espeak-ng."""
    try:
        # Convert pitch/speed to espeak parameters
        pitch = int(profile.pitch * 50)  # espeak uses 0-99
        speed = int(profile.speed * 175)  # espeak default is 175 wpm

        cmd = [
            "espeak-ng",
            "-v", profile.voice_id,
            "-p", str(pitch),
            "-s", str(speed),
            "-w", output_path,
            text
        ]

        proc = subprocess.run(cmd, capture_output=True, timeout=30)
        return proc.returncode == 0

    except Exception as e:
        logger.error(f"espeak-ng failed: {e}")
        return False


def _speak_with_espeak(text: str, output_path: str, profile: VoiceProfile) -> bool:
    """Generate speech using espeak."""
    try:
        pitch = int(profile.pitch * 50)
        speed = int(profile.speed * 175)

        cmd = [
            "espeak",
            "-v", profile.voice_id,
            "-p", str(pitch),
            "-s", str(speed),
            "-w", output_path,
            text
        ]

        proc = subprocess.run(cmd, capture_output=True, timeout=30)
        return proc.returncode == 0

    except Exception as e:
        logger.error(f"espeak failed: {e}")
        return False


def _speak_with_say(text: str, output_path: str, profile: VoiceProfile) -> bool:
    """Generate speech using macOS 'say' command."""
    try:
        speed = int(profile.speed * 200)  # say default is ~200 wpm

        cmd = [
            "say",
            "-o", output_path,
            "-r", str(speed),
            text
        ]

        proc = subprocess.run(cmd, capture_output=True, timeout=30)
        return proc.returncode == 0

    except Exception as e:
        logger.error(f"say failed: {e}")
        return False


def _speak_with_pico(text: str, output_path: str, profile: VoiceProfile) -> bool:
    """Generate speech using SVOX pico2wave."""
    try:
        cmd = [
            "pico2wave",
            "-l", "en-US",
            "-w", output_path,
            text
        ]

        proc = subprocess.run(cmd, capture_output=True, timeout=30)
        return proc.returncode == 0

    except Exception as e:
        logger.error(f"pico2wave failed: {e}")
        return False


def _speak_with_festival(text: str, output_path: str, profile: VoiceProfile) -> bool:
    """Generate speech using Festival."""
    try:
        # Write text to temp file
        temp_text = "/tmp/festival_input.txt"
        with open(temp_text, 'w') as f:
            f.write(text)

        cmd = f'festival --tts {temp_text} -o {output_path}'
        proc = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
        return proc.returncode == 0

    except Exception as e:
        logger.error(f"festival failed: {e}")
        return False


def _play_audio(audio_path: str) -> bool:
    """Play an audio file."""
    try:
        if _has_command("aplay"):
            subprocess.run(["aplay", audio_path], capture_output=True, timeout=60)
        elif _has_command("paplay"):
            subprocess.run(["paplay", audio_path], capture_output=True, timeout=60)
        elif _has_command("afplay"):  # macOS
            subprocess.run(["afplay", audio_path], capture_output=True, timeout=60)
        elif _has_command("play"):  # SoX
            subprocess.run(["play", audio_path], capture_output=True, timeout=60)
        else:
            return False
        return True
    except Exception:
        return False


def _format_for_baby(text: str, profile: VoiceProfile) -> str:
    """Format text according to baby's speaking style."""
    # Add personality-based formatting
    if profile.name == "MARCUS":
        # Add thoughtful pauses
        text = text.replace(". ", "... ")
    elif profile.name == "VULCAN":
        # More terse
        text = text.replace("  ", " ")
    elif profile.name == "HERMES":
        # Add enthusiasm
        if not text.endswith(("!", "?")):
            text = text.rstrip(".") + "!"
    elif profile.name == "PHOENIX":
        # Add curiosity
        text = text + " Interesting, right?"

    return text


def _has_command(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class SpeechOutput:
    """
    High-level interface for speech output.

    Usage:
        speech = SpeechOutput()
        speech.say("Hello, I am MARCUS", baby="MARCUS")
        speech.save("This is a test", "output.wav")
    """

    def __init__(self, output_dir: str = "/tmp/scorpion_speech"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.speech_count = 0
        self.muted = False

    def say(self, text: str, baby: str = "HERMES") -> SpeechResult:
        """Speak text using a baby's voice."""
        if self.muted:
            return SpeechResult(
                text=text,
                audio_path=None,
                duration=0,
                voice_profile=baby,
                played=False
            )

        self.speech_count += 1
        path = str(self.output_dir / f"speech_{self.speech_count}.wav")

        result = speak_text(text, baby, path, play_audio=True)

        return SpeechResult(
            text=text,
            audio_path=result.get("audio_path"),
            duration=result.get("estimated_duration", 0),
            voice_profile=baby,
            played=result.get("played", False)
        )

    def save(self, text: str, output_path: str, baby: str = "HERMES") -> str:
        """Save speech to file without playing."""
        result = speak_text(text, baby, output_path, play_audio=False)
        return result.get("audio_path", output_path)

    def mute(self):
        """Mute speech output."""
        self.muted = True

    def unmute(self):
        """Unmute speech output."""
        self.muted = False

    def get_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Get all available voice profiles."""
        return BABY_VOICE_PROFILES.copy()

    def announce(self, message: str, babies: List[str] = None) -> List[SpeechResult]:
        """Have multiple babies announce a message."""
        babies = babies or ["MARCUS", "HERMES"]
        results = []

        for baby in babies:
            intro = f"This is {baby}. "
            result = self.say(intro + message, baby)
            results.append(result)

        return results


if __name__ == "__main__":
    # Demo
    speech = SpeechOutput()

    print("=== Baby Voice Profiles ===")
    for name, profile in BABY_VOICE_PROFILES.items():
        print(f"{name}: pitch={profile.pitch}, speed={profile.speed}")
        print(f"  Personality: {profile.personality}")

    print("\n=== Speech Generation (simulated) ===")
    result = speak_text("Hello, I am learning to speak!", "PHOENIX", play_audio=False)
    print(f"Status: {result['status']}")
    print(f"Baby: {result['baby']}")
    print(f"Would say: {result.get('would_say', result.get('text'))}")

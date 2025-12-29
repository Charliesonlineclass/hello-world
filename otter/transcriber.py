"""
SCORPION-OTTER Transcriber
==========================

Audio transcription using OpenAI Whisper (local, no API needed).
Supports multiple audio formats and provides accurate transcription.

Requirements:
    pip install openai-whisper torch

For GPU acceleration (recommended):
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Union, Generator
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OTTER.transcriber")

# Supported audio formats
SUPPORTED_FORMATS = {
    '.mp3': 'MPEG Audio Layer 3',
    '.wav': 'Waveform Audio',
    '.m4a': 'MPEG-4 Audio',
    '.webm': 'WebM Audio',
    '.ogg': 'Ogg Vorbis',
    '.flac': 'Free Lossless Audio Codec',
    '.mp4': 'MPEG-4 (audio track)',
    '.mpeg': 'MPEG Audio',
    '.wma': 'Windows Media Audio'
}

# Model sizes and their characteristics
WHISPER_MODELS = {
    'tiny': {'size': '39M', 'vram': '~1GB', 'speed': 'fastest', 'accuracy': 'lowest'},
    'base': {'size': '74M', 'vram': '~1GB', 'speed': 'fast', 'accuracy': 'low'},
    'small': {'size': '244M', 'vram': '~2GB', 'speed': 'medium', 'accuracy': 'good'},
    'medium': {'size': '769M', 'vram': '~5GB', 'speed': 'slow', 'accuracy': 'high'},
    'large': {'size': '1550M', 'vram': '~10GB', 'speed': 'slowest', 'accuracy': 'highest'},
    'large-v2': {'size': '1550M', 'vram': '~10GB', 'speed': 'slowest', 'accuracy': 'best'},
    'large-v3': {'size': '1550M', 'vram': '~10GB', 'speed': 'slowest', 'accuracy': 'best'}
}

# Global whisper model cache
_whisper_model = None
_current_model_name = None


def supported_formats() -> Dict[str, str]:
    """Return dictionary of supported audio formats."""
    return SUPPORTED_FORMATS.copy()


def get_model_info(model_name: str = 'base') -> Dict[str, str]:
    """Get information about a Whisper model."""
    return WHISPER_MODELS.get(model_name, WHISPER_MODELS['base'])


def load_whisper_model(model_name: str = 'base', device: str = 'auto'):
    """
    Load Whisper model with caching.

    Args:
        model_name: Model size (tiny, base, small, medium, large, large-v2, large-v3)
        device: 'cuda', 'cpu', or 'auto' (auto-detect)

    Returns:
        Loaded Whisper model
    """
    global _whisper_model, _current_model_name

    try:
        import whisper
        import torch
    except ImportError:
        raise ImportError(
            "Whisper not installed. Run: pip install openai-whisper torch"
        )

    # Return cached model if same
    if _whisper_model is not None and _current_model_name == model_name:
        logger.info(f"Using cached Whisper model: {model_name}")
        return _whisper_model

    # Auto-detect device
    if device == 'auto':
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Auto-detected device: {device}")

    logger.info(f"Loading Whisper model '{model_name}' on {device}...")
    _whisper_model = whisper.load_model(model_name, device=device)
    _current_model_name = model_name

    return _whisper_model


def validate_audio_file(audio_path: Union[str, Path]) -> Path:
    """
    Validate that audio file exists and is supported format.

    Args:
        audio_path: Path to audio file

    Returns:
        Validated Path object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format not supported
    """
    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {path.suffix}. "
            f"Supported: {', '.join(SUPPORTED_FORMATS.keys())}"
        )

    return path


def transcribe_file(
    audio_path: Union[str, Path],
    model_name: str = 'base',
    language: Optional[str] = None,
    task: str = 'transcribe',
    verbose: bool = False
) -> Dict:
    """
    Transcribe an audio file to text.

    Args:
        audio_path: Path to audio file
        model_name: Whisper model size
        language: Language code (e.g., 'en', 'es') or None for auto-detect
        task: 'transcribe' or 'translate' (to English)
        verbose: Print progress during transcription

    Returns:
        Dictionary with:
            - text: Full transcription text
            - segments: List of timestamped segments
            - language: Detected/specified language
            - duration: Audio duration in seconds
            - model: Model used
    """
    path = validate_audio_file(audio_path)
    model = load_whisper_model(model_name)

    logger.info(f"Transcribing: {path.name}")
    start_time = datetime.now()

    # Transcribe with Whisper
    result = model.transcribe(
        str(path),
        language=language,
        task=task,
        verbose=verbose
    )

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Transcription completed in {elapsed:.1f}s")

    # Build response
    return {
        'text': result['text'].strip(),
        'segments': [
            {
                'id': seg['id'],
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip()
            }
            for seg in result['segments']
        ],
        'language': result['language'],
        'duration': result['segments'][-1]['end'] if result['segments'] else 0,
        'model': model_name,
        'file': str(path),
        'transcribed_at': datetime.now().isoformat()
    }


def transcribe_audio(
    audio_data: bytes,
    model_name: str = 'base',
    language: Optional[str] = None,
    format_hint: str = 'wav'
) -> Dict:
    """
    Transcribe audio from bytes (useful for streaming/API).

    Args:
        audio_data: Raw audio bytes
        model_name: Whisper model size
        language: Language code or None
        format_hint: Audio format hint for temp file

    Returns:
        Transcription result dictionary
    """
    import tempfile

    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix=f'.{format_hint}', delete=False) as f:
        f.write(audio_data)
        temp_path = f.name

    try:
        result = transcribe_file(temp_path, model_name, language)
        result['source'] = 'bytes'
        return result
    finally:
        os.unlink(temp_path)


def transcribe_with_timestamps(
    audio_path: Union[str, Path],
    model_name: str = 'base',
    language: Optional[str] = None
) -> List[Dict]:
    """
    Transcribe and return timestamped segments.

    Useful for subtitle generation or speaker diarization prep.

    Args:
        audio_path: Path to audio file
        model_name: Whisper model size
        language: Language code or None

    Returns:
        List of segment dictionaries with start, end, text
    """
    result = transcribe_file(audio_path, model_name, language)
    return result['segments']


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(segments: List[Dict]) -> str:
    """
    Generate SRT subtitle file content from segments.

    Args:
        segments: List of segment dictionaries

    Returns:
        SRT formatted string
    """
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg['start'])
        end = format_timestamp(seg['end'])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg['text'])
        lines.append("")
    return "\n".join(lines)


def save_transcript(
    result: Union[Dict, str],
    output_path: Optional[Union[str, Path]] = None,
    meeting_name: Optional[str] = None,
    format: str = 'txt'
) -> Path:
    """
    Save transcription to file.

    Args:
        result: Transcription result dict or plain text
        output_path: Explicit output path, or None to auto-generate
        meeting_name: Name for the meeting (used in auto-generated filename)
        format: Output format ('txt', 'json', 'srt', 'md')

    Returns:
        Path to saved file
    """
    # Handle plain text input
    if isinstance(result, str):
        result = {'text': result, 'segments': []}

    # Generate output path if not provided
    if output_path is None:
        transcripts_dir = Path("transcripts")
        transcripts_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = meeting_name or "meeting"
        name = name.replace(" ", "_").lower()
        output_path = transcripts_dir / f"{name}_{timestamp}.{format}"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save based on format
    if format == 'json':
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

    elif format == 'srt':
        srt_content = generate_srt(result.get('segments', []))
        with open(output_path, 'w') as f:
            f.write(srt_content)

    elif format == 'md':
        md_content = generate_markdown(result)
        with open(output_path, 'w') as f:
            f.write(md_content)

    else:  # txt
        with open(output_path, 'w') as f:
            f.write(result.get('text', str(result)))

    logger.info(f"Transcript saved: {output_path}")
    return output_path


def generate_markdown(result: Dict) -> str:
    """Generate markdown formatted transcript."""
    lines = [
        f"# Meeting Transcript",
        f"",
        f"**Date:** {result.get('transcribed_at', datetime.now().isoformat())}",
        f"**Duration:** {result.get('duration', 0):.1f} seconds",
        f"**Language:** {result.get('language', 'unknown')}",
        f"**Model:** {result.get('model', 'unknown')}",
        f"",
        f"---",
        f"",
        f"## Full Transcript",
        f"",
        result.get('text', ''),
        f"",
    ]

    if result.get('segments'):
        lines.extend([
            f"---",
            f"",
            f"## Timestamped Segments",
            f""
        ])
        for seg in result['segments']:
            timestamp = f"[{format_timestamp(seg['start'])} - {format_timestamp(seg['end'])}]"
            lines.append(f"**{timestamp}** {seg['text']}")
            lines.append("")

    return "\n".join(lines)


def get_audio_hash(audio_path: Union[str, Path]) -> str:
    """Generate hash of audio file for caching."""
    path = Path(audio_path)
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


class TranscriptionCache:
    """
    Cache for transcription results to avoid re-processing.
    """

    def __init__(self, cache_dir: Union[str, Path] = ".transcript_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, audio_path: Union[str, Path], model: str) -> Path:
        """Get cache file path for an audio file."""
        audio_hash = get_audio_hash(audio_path)
        return self.cache_dir / f"{audio_hash}_{model}.json"

    def get(self, audio_path: Union[str, Path], model: str) -> Optional[Dict]:
        """Retrieve cached transcription if available."""
        cache_path = self.get_cache_path(audio_path, model)
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                logger.info(f"Using cached transcription: {cache_path.name}")
                return json.load(f)
        return None

    def set(self, audio_path: Union[str, Path], model: str, result: Dict):
        """Cache transcription result."""
        cache_path = self.get_cache_path(audio_path, model)
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Cached transcription: {cache_path.name}")

    def transcribe_cached(
        self,
        audio_path: Union[str, Path],
        model_name: str = 'base',
        language: Optional[str] = None,
        force: bool = False
    ) -> Dict:
        """
        Transcribe with caching - returns cached result if available.

        Args:
            audio_path: Path to audio file
            model_name: Whisper model size
            language: Language code or None
            force: Force re-transcription even if cached

        Returns:
            Transcription result
        """
        if not force:
            cached = self.get(audio_path, model_name)
            if cached:
                return cached

        result = transcribe_file(audio_path, model_name, language)
        self.set(audio_path, model_name, result)
        return result


# Convenience function for cached transcription
_cache = None

def transcribe_cached(
    audio_path: Union[str, Path],
    model_name: str = 'base',
    language: Optional[str] = None
) -> Dict:
    """Transcribe with automatic caching."""
    global _cache
    if _cache is None:
        _cache = TranscriptionCache()
    return _cache.transcribe_cached(audio_path, model_name, language)


# Placeholder for real-time transcription (future implementation)
def transcribe_realtime(
    device_index: int = 0,
    model_name: str = 'tiny',
    callback: Optional[callable] = None
) -> Generator[str, None, None]:
    """
    Real-time transcription from microphone (placeholder).

    This is a placeholder for future implementation using pyaudio
    and streaming transcription.

    Args:
        device_index: Audio input device index
        model_name: Whisper model (recommend 'tiny' for speed)
        callback: Optional callback for each transcription chunk

    Yields:
        Transcribed text chunks
    """
    raise NotImplementedError(
        "Real-time transcription not yet implemented. "
        "For now, record audio and use transcribe_file()."
    )


if __name__ == "__main__":
    # CLI usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcriber.py <audio_file> [model] [output_format]")
        print(f"Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}")
        print(f"Models: {', '.join(WHISPER_MODELS.keys())}")
        sys.exit(1)

    audio_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else 'base'
    output_format = sys.argv[3] if len(sys.argv) > 3 else 'txt'

    result = transcribe_file(audio_file, model)
    output_path = save_transcript(result, format=output_format)

    print(f"\n{'='*60}")
    print("TRANSCRIPTION COMPLETE")
    print(f"{'='*60}")
    print(f"File: {audio_file}")
    print(f"Duration: {result['duration']:.1f}s")
    print(f"Language: {result['language']}")
    print(f"Saved to: {output_path}")
    print(f"{'='*60}\n")
    print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])

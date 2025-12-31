"""
SCORPION_BRAIN Senses Module
============================
Input/output interfaces for the AI babies.

Inputs:
- visual_input: OCR, screenshots, element detection
- audio_input: Transcription, microphone capture
- sensor_input: System metrics, file watch, network
- eyes: Image analysis, OCR, object detection
- ears: Audio transcription, speech detection

Outputs:
- speech_output: TTS with baby voice profiles
- action_output: Shell, file ops, API, docker
"""

from .visual_input import (
    VisualInput,
    capture_screenshot,
    ocr_image,
    detect_elements
)

from .audio_input import (
    AudioInput,
    transcribe_audio,
    record_audio
)

from .eyes import (
    Eyes,
    analyze_image,
    extract_text_ocr,
    detect_objects
)

from .ears import (
    Ears,
    transcribe_audio as ears_transcribe,
    detect_speech,
    audio_to_text_stream
)

from .speech_output import (
    SpeechOutput,
    speak_text,
    BABY_VOICE_PROFILES
)

from .sensor_input import (
    SensorInput,
    get_system_metrics,
    watch_file,
    check_network
)

from .action_output import (
    ActionOutput,
    run_shell,
    file_operation,
    docker_operation
)

__all__ = [
    # Visual
    'VisualInput',
    'capture_screenshot',
    'ocr_image',
    'detect_elements',
    # Audio
    'AudioInput',
    'transcribe_audio',
    'record_audio',
    # Eyes (enhanced visual)
    'Eyes',
    'analyze_image',
    'extract_text_ocr',
    'detect_objects',
    # Ears (enhanced audio)
    'Ears',
    'ears_transcribe',
    'detect_speech',
    'audio_to_text_stream',
    # Speech
    'SpeechOutput',
    'speak_text',
    'BABY_VOICE_PROFILES',
    # Sensor
    'SensorInput',
    'get_system_metrics',
    'watch_file',
    'check_network',
    # Action
    'ActionOutput',
    'run_shell',
    'file_operation',
    'docker_operation',
]

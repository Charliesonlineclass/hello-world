"""
SCORPION_BRAIN Eyes - Image Processing
======================================
Visual processing capabilities for SCORPION.

Features:
- Image analysis and description
- OCR text extraction
- Object detection
- Color analysis
- Face detection placeholder
"""

import subprocess
import base64
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ImageInfo:
    """Information about an image."""
    path: str
    width: int
    height: int
    format: str
    size_bytes: int
    color_depth: int
    has_alpha: bool


@dataclass
class DetectedObject:
    """A detected object in an image."""
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    center: Tuple[int, int]


@dataclass
class OCRResult:
    """Result from OCR text extraction."""
    text: str
    confidence: float
    blocks: List[Dict]
    word_count: int
    language: str


@dataclass
class AnalysisResult:
    """Complete image analysis result."""
    description: str
    objects: List[DetectedObject]
    text: Optional[str]
    colors: List[str]
    dimensions: Tuple[int, int]
    metadata: Dict


def analyze_image(path: str) -> Dict[str, Any]:
    """
    Analyze an image and return a description.

    Args:
        path: Path to image file

    Returns:
        Dict with image analysis results
    """
    result = {
        "path": path,
        "status": "pending",
        "timestamp": datetime.now().isoformat()
    }

    if not Path(path).exists():
        result["status"] = "error"
        result["error"] = "Image file not found"
        return result

    try:
        # Get image info
        info = _get_image_info(path)
        result["info"] = info

        # Detect objects (using simple methods or placeholders)
        objects = detect_objects(path)
        result["objects"] = objects.get("objects", [])

        # Extract text
        ocr_result = extract_text_ocr(path)
        if ocr_result.get("status") == "success":
            result["text"] = ocr_result.get("text", "")

        # Analyze colors
        colors = _analyze_colors(path)
        result["dominant_colors"] = colors

        # Generate description
        description = _generate_description(info, result.get("objects", []), result.get("text"))
        result["description"] = description

        result["status"] = "success"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def extract_text_ocr(path: str, language: str = "eng") -> Dict[str, Any]:
    """
    Extract text from image using OCR.

    Args:
        path: Path to image file
        language: OCR language code

    Returns:
        Dict with extracted text and metadata
    """
    result = {
        "path": path,
        "status": "pending",
        "language": language
    }

    if not Path(path).exists():
        result["status"] = "error"
        result["error"] = "Image file not found"
        return result

    try:
        # Try tesseract
        if _has_command("tesseract"):
            proc = subprocess.run(
                ["tesseract", path, "stdout", "-l", language, "--oem", "3", "--psm", "3"],
                capture_output=True,
                timeout=60
            )

            if proc.returncode == 0:
                text = proc.stdout.decode('utf-8', errors='ignore').strip()
                result["status"] = "success"
                result["text"] = text
                result["word_count"] = len(text.split())
                result["line_count"] = len(text.split('\n'))
                result["confidence"] = 0.85  # Tesseract confidence estimate

                # Extract blocks/paragraphs
                result["blocks"] = _parse_text_blocks(text)
                return result

        # Try pytesseract if available
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(path)
            text = pytesseract.image_to_string(img, lang=language)

            result["status"] = "success"
            result["text"] = text.strip()
            result["word_count"] = len(text.split())
            result["confidence"] = 0.85
            return result

        except ImportError:
            pass

        # Fallback
        result["status"] = "unavailable"
        result["text"] = ""
        result["message"] = "OCR not available - install tesseract"

    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "OCR timed out"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def detect_objects(path: str) -> Dict[str, Any]:
    """
    Detect objects in an image.

    Args:
        path: Path to image file

    Returns:
        Dict with detected objects
    """
    result = {
        "path": path,
        "status": "pending",
        "objects": []
    }

    if not Path(path).exists():
        result["status"] = "error"
        result["error"] = "Image file not found"
        return result

    try:
        # Try using opencv if available
        try:
            import cv2
            import numpy as np

            img = cv2.imread(path)
            if img is None:
                raise ValueError("Could not load image")

            height, width = img.shape[:2]
            objects = []

            # Face detection
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            for (x, y, w, h) in faces:
                objects.append({
                    "label": "face",
                    "confidence": 0.75,
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "center": [int(x + w/2), int(y + h/2)]
                })

            # Edge detection for shapes
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Detect rectangles (potential text blocks, UI elements)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Filter small contours
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect = w / h if h > 0 else 0

                    if 0.3 < aspect < 3:  # Reasonable aspect ratio
                        objects.append({
                            "label": "region",
                            "confidence": 0.6,
                            "bbox": [int(x), int(y), int(w), int(h)],
                            "center": [int(x + w/2), int(y + h/2)]
                        })

            result["status"] = "success"
            result["objects"] = objects[:20]  # Limit results
            result["dimensions"] = [width, height]
            return result

        except ImportError:
            pass

        # Fallback: basic image info without object detection
        info = _get_image_info(path)
        result["status"] = "partial"
        result["message"] = "Object detection not available - install opencv-python"
        result["dimensions"] = [info.get("width", 0), info.get("height", 0)]

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _get_image_info(path: str) -> Dict:
    """Get basic image information."""
    info = {
        "path": path,
        "exists": Path(path).exists()
    }

    if not info["exists"]:
        return info

    try:
        # Try PIL
        try:
            from PIL import Image
            with Image.open(path) as img:
                info["width"] = img.width
                info["height"] = img.height
                info["format"] = img.format
                info["mode"] = img.mode
                info["has_alpha"] = img.mode in ('RGBA', 'LA', 'PA')
            info["size_bytes"] = Path(path).stat().st_size
            return info
        except ImportError:
            pass

        # Try identify command
        if _has_command("identify"):
            proc = subprocess.run(
                ["identify", "-format", "%w %h %m", path],
                capture_output=True,
                timeout=10
            )
            if proc.returncode == 0:
                parts = proc.stdout.decode().strip().split()
                if len(parts) >= 3:
                    info["width"] = int(parts[0])
                    info["height"] = int(parts[1])
                    info["format"] = parts[2]

        info["size_bytes"] = Path(path).stat().st_size

    except Exception as e:
        info["error"] = str(e)

    return info


def _analyze_colors(path: str) -> List[str]:
    """Analyze dominant colors in image."""
    try:
        from PIL import Image
        from collections import Counter

        with Image.open(path) as img:
            # Resize for faster processing
            img = img.convert('RGB')
            img = img.resize((100, 100))

            # Get colors
            pixels = list(img.getdata())

            # Quantize to reduce colors
            quantized = []
            for r, g, b in pixels:
                qr = (r // 32) * 32
                qg = (g // 32) * 32
                qb = (b // 32) * 32
                quantized.append((qr, qg, qb))

            # Get most common
            counter = Counter(quantized)
            top_colors = counter.most_common(5)

            # Convert to hex
            return [f"#{r:02x}{g:02x}{b:02x}" for (r, g, b), _ in top_colors]

    except ImportError:
        return []
    except Exception as e:
        logger.debug(f"Color analysis failed: {e}")
        return []


def _parse_text_blocks(text: str) -> List[Dict]:
    """Parse text into blocks/paragraphs."""
    blocks = []
    paragraphs = text.split('\n\n')

    for i, para in enumerate(paragraphs):
        para = para.strip()
        if para:
            blocks.append({
                "index": i,
                "text": para[:500],
                "word_count": len(para.split()),
                "line_count": len(para.split('\n'))
            })

    return blocks


def _generate_description(info: Dict, objects: List, text: Optional[str]) -> str:
    """Generate a human-readable description of the image."""
    parts = []

    # Dimensions
    if "width" in info and "height" in info:
        parts.append(f"Image is {info['width']}x{info['height']} pixels")

    # Format
    if "format" in info:
        parts.append(f"in {info['format']} format")

    # Objects
    if objects:
        obj_counts = {}
        for obj in objects:
            label = obj.get("label", "object")
            obj_counts[label] = obj_counts.get(label, 0) + 1

        obj_desc = ", ".join(f"{count} {label}(s)" for label, count in obj_counts.items())
        parts.append(f"Contains: {obj_desc}")

    # Text
    if text:
        word_count = len(text.split())
        parts.append(f"Contains {word_count} words of text")

    return ". ".join(parts) if parts else "Image analysis complete"


def _has_command(cmd: str) -> bool:
    """Check if command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class Eyes:
    """
    High-level interface for image processing.

    Usage:
        eyes = Eyes()
        description = eyes.see("image.png")
        text = eyes.read_text("document.png")
        objects = eyes.find_objects("photo.jpg")
    """

    def __init__(self):
        self.cache: Dict[str, Dict] = {}

    def see(self, path: str, use_cache: bool = True) -> str:
        """Analyze image and return description."""
        if use_cache and path in self.cache:
            return self.cache[path].get("description", "")

        result = analyze_image(path)

        if use_cache:
            self.cache[path] = result

        return result.get("description", "Unable to analyze image")

    def read_text(self, path: str) -> str:
        """Extract text from image."""
        result = extract_text_ocr(path)
        return result.get("text", "")

    def find_objects(self, path: str) -> List[Dict]:
        """Find objects in image."""
        result = detect_objects(path)
        return result.get("objects", [])

    def get_info(self, path: str) -> Dict:
        """Get image information."""
        return _get_image_info(path)

    def get_colors(self, path: str) -> List[str]:
        """Get dominant colors."""
        return _analyze_colors(path)


if __name__ == "__main__":
    # Demo
    eyes = Eyes()

    print("=== Eyes Module Demo ===")
    print("This module provides image analysis capabilities.")
    print("\nMethods available:")
    print("  eyes.see(path) -> description")
    print("  eyes.read_text(path) -> extracted text")
    print("  eyes.find_objects(path) -> detected objects")
    print("  eyes.get_colors(path) -> dominant colors")

    # Test with a sample path
    test_path = "/tmp/test_image.png"
    print(f"\nTesting with: {test_path}")

    info = eyes.get_info(test_path)
    print(f"Image info: {info}")

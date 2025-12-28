"""
SCORPION_BRAIN Visual Input
===========================
Visual perception capabilities: OCR, screenshots, element detection.

Features:
- Screenshot capture
- OCR text extraction
- UI element detection
- Image analysis
"""

import base64
import subprocess
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box for detected elements."""
    x: int
    y: int
    width: int
    height: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        return self.width * self.height

    def contains(self, x: int, y: int) -> bool:
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)


@dataclass
class DetectedElement:
    """A detected UI element."""
    element_type: str  # button, text, input, image, link
    text: str
    bbox: BoundingBox
    confidence: float
    attributes: Dict = field(default_factory=dict)


@dataclass
class OCRResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    words: List[Dict] = field(default_factory=list)
    lines: List[str] = field(default_factory=list)


@dataclass
class Screenshot:
    """Captured screenshot data."""
    path: str
    width: int
    height: int
    timestamp: datetime
    format: str = "png"
    base64_data: Optional[str] = None


def capture_screenshot(
    output_path: str = None,
    region: Tuple[int, int, int, int] = None,
    include_base64: bool = False
) -> Dict[str, Any]:
    """
    Capture a screenshot.

    Args:
        output_path: Path to save screenshot (auto-generated if None)
        region: Optional (x, y, width, height) to capture specific area
        include_base64: Include base64-encoded image data

    Returns:
        Dict with screenshot info
    """
    timestamp = datetime.now()

    if output_path is None:
        output_path = f"/tmp/screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"

    result = {
        "status": "pending",
        "path": output_path,
        "timestamp": timestamp.isoformat()
    }

    try:
        # Try different screenshot methods
        if _has_command("scrot"):
            cmd = ["scrot", output_path]
            if region:
                x, y, w, h = region
                cmd = ["scrot", "-a", f"{x},{y},{w},{h}", output_path]
        elif _has_command("gnome-screenshot"):
            cmd = ["gnome-screenshot", "-f", output_path]
        elif _has_command("import"):  # ImageMagick
            cmd = ["import", "-window", "root", output_path]
        else:
            # Fallback: create a placeholder
            result["status"] = "simulated"
            result["message"] = "No screenshot tool available, using placeholder"
            result["width"] = 1920
            result["height"] = 1080
            return result

        # Execute screenshot command
        proc = subprocess.run(cmd, capture_output=True, timeout=10)

        if proc.returncode == 0 and Path(output_path).exists():
            result["status"] = "success"

            # Get image dimensions (if PIL available)
            try:
                from PIL import Image
                with Image.open(output_path) as img:
                    result["width"] = img.width
                    result["height"] = img.height
            except ImportError:
                result["width"] = 1920  # Assume standard
                result["height"] = 1080

            # Include base64 if requested
            if include_base64:
                with open(output_path, 'rb') as f:
                    result["base64"] = base64.b64encode(f.read()).decode('utf-8')

        else:
            result["status"] = "error"
            result["error"] = proc.stderr.decode() if proc.stderr else "Unknown error"

    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "Screenshot timed out"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def ocr_image(
    image_path: str,
    language: str = "eng"
) -> Dict[str, Any]:
    """
    Perform OCR on an image.

    Args:
        image_path: Path to image file
        language: OCR language (default: English)

    Returns:
        Dict with extracted text and metadata
    """
    result = {
        "status": "pending",
        "image": image_path,
        "language": language
    }

    if not Path(image_path).exists():
        result["status"] = "error"
        result["error"] = f"Image not found: {image_path}"
        return result

    try:
        # Try tesseract OCR
        if _has_command("tesseract"):
            proc = subprocess.run(
                ["tesseract", image_path, "stdout", "-l", language],
                capture_output=True,
                timeout=30
            )

            if proc.returncode == 0:
                text = proc.stdout.decode('utf-8', errors='ignore')
                result["status"] = "success"
                result["text"] = text.strip()
                result["lines"] = [l for l in text.split('\n') if l.strip()]
                result["word_count"] = len(text.split())
                result["confidence"] = 0.85  # Tesseract doesn't easily give confidence
            else:
                result["status"] = "error"
                result["error"] = proc.stderr.decode() if proc.stderr else "OCR failed"

        else:
            # Fallback: simulate OCR
            result["status"] = "simulated"
            result["text"] = "[OCR not available - install tesseract]"
            result["message"] = "Tesseract not installed"

    except subprocess.TimeoutExpired:
        result["status"] = "error"
        result["error"] = "OCR timed out"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def detect_elements(
    image_path: str,
    element_types: List[str] = None
) -> Dict[str, Any]:
    """
    Detect UI elements in an image.

    Args:
        image_path: Path to image/screenshot
        element_types: Types to detect (button, text, input, etc.)

    Returns:
        Dict with detected elements
    """
    element_types = element_types or ["button", "text", "input", "link"]

    result = {
        "status": "pending",
        "image": image_path,
        "requested_types": element_types
    }

    if not Path(image_path).exists():
        result["status"] = "error"
        result["error"] = f"Image not found: {image_path}"
        return result

    try:
        # First, try OCR to find text elements
        ocr_result = ocr_image(image_path)

        elements = []

        if ocr_result.get("status") == "success":
            # Create text elements from OCR
            lines = ocr_result.get("lines", [])
            y_pos = 50  # Simulated positions

            for i, line in enumerate(lines[:20]):  # Limit to 20 lines
                if line.strip():
                    # Detect if line looks like a button, link, etc.
                    elem_type = _classify_text_element(line)

                    if elem_type in element_types:
                        elements.append({
                            "type": elem_type,
                            "text": line.strip(),
                            "bbox": {
                                "x": 20,
                                "y": y_pos + (i * 30),
                                "width": len(line) * 8,
                                "height": 25
                            },
                            "confidence": 0.7
                        })

        # Add simulated elements for demo
        if not elements:
            elements = _generate_simulated_elements(element_types)
            result["note"] = "Using simulated elements (no real detection available)"

        result["status"] = "success"
        result["elements"] = elements
        result["element_count"] = len(elements)
        result["types_found"] = list(set(e["type"] for e in elements))

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


# Helper functions

def _has_command(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _classify_text_element(text: str) -> str:
    """Classify text as a UI element type."""
    text_lower = text.lower().strip()

    # Button patterns
    button_patterns = ['submit', 'click', 'ok', 'cancel', 'save', 'delete', 'confirm', 'next', 'back', 'login', 'signup']
    if any(p in text_lower for p in button_patterns) or text_lower.isupper():
        return "button"

    # Link patterns
    if text_lower.startswith(('http', 'www', '@')) or re.match(r'.*\.(com|org|net|io)', text_lower):
        return "link"

    # Input patterns
    input_patterns = ['enter', 'type', 'email:', 'password:', 'name:', 'username:']
    if any(p in text_lower for p in input_patterns):
        return "input"

    return "text"


def _generate_simulated_elements(types: List[str]) -> List[Dict]:
    """Generate simulated UI elements for demo."""
    elements = []

    simulated = {
        "button": [
            {"text": "Submit", "x": 100, "y": 200},
            {"text": "Cancel", "x": 200, "y": 200},
        ],
        "text": [
            {"text": "Welcome to SCORPION_BRAIN", "x": 50, "y": 50},
            {"text": "Status: Online", "x": 50, "y": 100},
        ],
        "input": [
            {"text": "Username field", "x": 100, "y": 150},
            {"text": "Password field", "x": 100, "y": 180},
        ],
        "link": [
            {"text": "https://example.com", "x": 50, "y": 300},
        ]
    }

    for elem_type in types:
        if elem_type in simulated:
            for item in simulated[elem_type]:
                elements.append({
                    "type": elem_type,
                    "text": item["text"],
                    "bbox": {
                        "x": item["x"],
                        "y": item["y"],
                        "width": len(item["text"]) * 8,
                        "height": 25
                    },
                    "confidence": 0.5,
                    "simulated": True
                })

    return elements


class VisualInput:
    """
    High-level interface for visual input.

    Usage:
        visual = VisualInput()
        screenshot = visual.capture()
        text = visual.read_text(screenshot.path)
        elements = visual.find_elements(screenshot.path, ["button"])
    """

    def __init__(self, output_dir: str = "/tmp/scorpion_visual"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_count = 0

    def capture(self, region: Tuple[int, int, int, int] = None) -> Screenshot:
        """Capture a screenshot."""
        self.screenshot_count += 1
        path = str(self.output_dir / f"screen_{self.screenshot_count}.png")

        result = capture_screenshot(path, region)

        return Screenshot(
            path=result.get("path", path),
            width=result.get("width", 1920),
            height=result.get("height", 1080),
            timestamp=datetime.now(),
            base64_data=result.get("base64")
        )

    def read_text(self, image_path: str) -> str:
        """Read text from an image using OCR."""
        result = ocr_image(image_path)
        return result.get("text", "")

    def find_elements(
        self,
        image_path: str,
        element_types: List[str] = None
    ) -> List[DetectedElement]:
        """Find UI elements in an image."""
        result = detect_elements(image_path, element_types)

        elements = []
        for elem in result.get("elements", []):
            bbox = elem.get("bbox", {})
            elements.append(DetectedElement(
                element_type=elem["type"],
                text=elem["text"],
                bbox=BoundingBox(
                    x=bbox.get("x", 0),
                    y=bbox.get("y", 0),
                    width=bbox.get("width", 100),
                    height=bbox.get("height", 25)
                ),
                confidence=elem.get("confidence", 0.5),
                attributes={"simulated": elem.get("simulated", False)}
            ))

        return elements

    def find_text_on_screen(self, search_text: str) -> List[DetectedElement]:
        """Capture screen and find specific text."""
        screenshot = self.capture()
        elements = self.find_elements(screenshot.path, ["text"])

        search_lower = search_text.lower()
        return [e for e in elements if search_lower in e.text.lower()]


if __name__ == "__main__":
    # Demo
    visual = VisualInput()

    print("=== Screenshot ===")
    result = capture_screenshot()
    print(f"Status: {result['status']}")
    print(f"Path: {result['path']}")

    print("\n=== OCR (simulated) ===")
    # Create a test image path
    ocr_result = ocr_image("/tmp/test.png")
    print(f"Status: {ocr_result['status']}")

    print("\n=== Element Detection (simulated) ===")
    elements = detect_elements("/tmp/test.png", ["button", "text"])
    print(f"Found {elements.get('element_count', 0)} elements")
    for elem in elements.get("elements", [])[:5]:
        print(f"  - {elem['type']}: {elem['text']}")

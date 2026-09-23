"""Image utilities for VisionVoice AI.

Handles image loading, format conversions (PIL <-> NumPy <-> QPixmap/QImage),
bounding box rendering, and thumbnail generation.
"""

import os
from typing import Any, List, Optional, Tuple, Union
import numpy as np
from PIL import Image, ImageDraw, ImageOps

from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtCore import Qt, QRectF


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def is_supported_image(filepath: str) -> bool:
    """Validates if file has a supported graphic extension."""
    if not filepath or not os.path.isfile(filepath):
        return False
    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


def load_image(source: Union[str, Image.Image, np.ndarray]) -> Image.Image:
    """Loads an image into PIL Image in RGB mode."""
    if isinstance(source, Image.Image):
        return source.convert("RGB")
    elif isinstance(source, np.ndarray):
        return Image.fromarray(source).convert("RGB")
    elif isinstance(source, str):
        if not os.path.exists(source):
            raise FileNotFoundError(f"Image not found at: {source}")
        img = Image.open(source)
        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")
    else:
        raise ValueError(f"Unsupported image source type: {type(source)}")


def pil_to_numpy(image: Image.Image) -> np.ndarray:
    """Converts PIL Image to RGB NumPy array."""
    return np.array(image.convert("RGB"))


def pil_to_qimage(image: Image.Image) -> QImage:
    """Converts PIL Image to PySide6 QImage without memory corruption."""
    rgb_image = image.convert("RGB")
    data = rgb_image.tobytes("raw", "RGB")
    qimg = QImage(
        data,
        rgb_image.width,
        rgb_image.height,
        rgb_image.width * 3,
        QImage.Format.Format_RGB888
    )
    return qimg.copy()


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    """Converts PIL Image directly to PySide6 QPixmap."""
    qimage = pil_to_qimage(image)
    return QPixmap.fromImage(qimage)


def qpixmap_to_pil(pixmap: QPixmap) -> Image.Image:
    """Converts QPixmap to PIL Image."""
    qimage = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
    width = qimage.width()
    height = qimage.height()
    ptr = qimage.constBits()
    arr = np.array(ptr).reshape((height, width, 3))
    return Image.fromarray(arr)


def draw_bounding_boxes_on_pixmap(
    pixmap: QPixmap,
    boxes: List[dict],
    color: QColor = QColor(0, 188, 212, 220),  # Cyan
    line_width: int = 2
) -> QPixmap:
    """Renders text detection bounding boxes onto a QPixmap copy."""
    result = QPixmap(pixmap)
    painter = QPainter(result)
    pen = QPen(color, line_width)
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    painter.setPen(pen)

    for box_info in boxes:
        box = box_info.get("box")
        if not box:
            continue

        # Handle 4-point polygon [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        if len(box) == 4 and isinstance(box[0], (list, tuple)):
            xs = [pt[0] for pt in box]
            ys = [pt[1] for pt in box]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            painter.drawRect(QRectF(x_min, y_min, x_max - x_min, y_max - y_min))
        # Handle [x_min, y_min, x_max, y_max]
        elif len(box) == 4 and isinstance(box[0], (int, float)):
            x_min, y_min, x_max, y_max = box
            painter.drawRect(QRectF(x_min, y_min, x_max - x_min, y_max - y_min))

    painter.end()
    return result

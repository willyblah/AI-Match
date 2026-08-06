"""Fills a PDF by adding text annotations defined in fields.json. See forms.md."""

import io
import json
import subprocess
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText


def transform_coordinates(bbox, image_width, image_height, pdf_width, pdf_height):
    """Transform bounding box from image coordinates to PDF coordinates"""
    # Image coordinates: origin at top-left, y increases downward
    # PDF coordinates: origin at bottom-left, y increases upward
    x_scale = pdf_width / image_width
    y_scale = pdf_height / image_height

    left = bbox[0] * x_scale
    right = bbox[2] * x_scale

    top = pdf_height - (bbox[1] * y_scale)
    bottom = pdf_height - (bbox[3] * y_scale)

    return left, bottom, right, top


import html as _html
import re as _re

_HTML_TAG_RE = _re.compile(r'<[^>]+>|<<<[^>]*>>>|<<[^>]*>>')


def strip_markup(text):
    """Remove HTML/markup tags, decode HTML entities, and collapse whitespace."""
    text = _HTML_TAG_RE.sub('', text)
    text = _html.unescape(text)       # &amp; → &, &nbsp; → space, etc.
    text = _re.sub(r'\s+', ' ', text) # collapse newlines/tabs/multiple spaces
    return text.strip()


def is_cjk_text(text):
    """Return True if text contains any CJK (Chinese/Japanese/Korean) characters."""
    for char in text:
        cp = ord(char)
        if (0x4E00 <= cp <= 0x9FFF or
                0x3400 <= cp <= 0x4DBF or
                0x20000 <= cp <= 0x2A6DF or
                0xF900 <= cp <= 0xFAFF or
                0x3000 <= cp <= 0x303F or
                0xFF00 <= cp <= 0xFFEF or
                0xAC00 <= cp <= 0xD7AF or
                0x3040 <= cp <= 0x309F or
                0x30A0 <= cp <= 0x30FF):
            return True
    return False


# Common CJK TTF/TTC font paths across operating systems.
_CJK_FONT_CANDIDATES = [
    # Ubuntu / Debian (fonts-wqy-zenhei, fonts-wqy-microhei)
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    # Ubuntu / Debian (fonts-noto-cjk)
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    # Windows
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/msyh.ttc",
]


def _find_cjk_font():
    """Return the path of the first available CJK font file, or None."""
    import os
    for path in _CJK_FONT_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


def _try_install_cjk_font():
    """Attempt to install a CJK font package on Linux via apt-get."""
    import platform
    if platform.system() != "Linux":
        return
    print("No CJK font found. Attempting to install fonts-wqy-zenhei via apt-get...")
    try:
        subprocess.check_call(
            ["apt-get", "install", "-y", "fonts-wqy-zenhei"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("fonts-wqy-zenhei installed.")
    except Exception:
        try:
            subprocess.check_call(
                ["sudo", "apt-get", "install", "-y", "fonts-wqy-zenhei"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("fonts-wqy-zenhei installed.")
        except Exception as e:
            print(f"Could not install CJK font automatically: {e}", file=sys.stderr)


def _ensure_reportlab():
    """Install reportlab if not already available."""
    try:
        import reportlab  # noqa: F401
    except ImportError:
        print("Installing reportlab...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "reportlab"],
            stdout=subprocess.DEVNULL,
        )
        print("reportlab installed.")


def _fill_with_reportlab_overlay(writer, fields_by_page, pdf_dimensions):
    """Render CJK-safe text using reportlab with an embedded TTF font."""
    _ensure_reportlab()

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas as rl_canvas

    font_path = _find_cjk_font()
    if font_path is None:
        _try_install_cjk_font()
        font_path = _find_cjk_font()

    if font_path is None:
        raise RuntimeError(
            "No CJK font file found on this system. "
            "Please install one, e.g.:\n"
            "  Ubuntu/Debian: sudo apt-get install fonts-wqy-zenhei\n"
            "  macOS: fonts are bundled with the OS\n"
            "  Windows: SimHei or SimSun should be pre-installed"
        )

    pdfmetrics.registerFont(TTFont("CJKFont", font_path, subfontIndex=0))
    print(f"Using CJK font: {font_path}")

    annotations_added = 0
    for page_num, fields in fields_by_page.items():
        pdf_width, pdf_height = pdf_dimensions[page_num]
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=(pdf_width, pdf_height))

        for field in fields:
            text = field["entry_text"]["text"]
            left, bottom, right, top = field["_transformed_bbox"]
            font_size = field["entry_text"].get("font_size", 14)
            font_color_hex = field["entry_text"].get("font_color", "000000")

            r = int(font_color_hex[0:2], 16) / 255
            g = int(font_color_hex[2:4], 16) / 255
            b = int(font_color_hex[4:6], 16) / 255

            c.setFont("CJKFont", font_size)
            c.setFillColorRGB(r, g, b)
            c.drawString(left, bottom, text)
            annotations_added += 1

        c.save()
        packet.seek(0)
        overlay_page = PdfReader(packet).pages[0]
        writer.pages[page_num - 1].merge_page(overlay_page)

    return annotations_added


def fill_pdf_form(input_pdf_path, fields_json_path, output_pdf_path):
    """Fill the PDF form with data from fields.json"""

    with open(fields_json_path, "r") as f:
        fields_data = json.load(f)

    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    pdf_dimensions = {}
    for i, page in enumerate(reader.pages):
        mediabox = page.mediabox
        pdf_dimensions[i + 1] = [float(mediabox.width), float(mediabox.height)]

    # Pre-process: compute transformed coords, group by page, detect CJK
    fields_by_page = {}
    has_cjk = False
    for field in fields_data["form_fields"]:
        page_num = field["page_number"]

        if "entry_text" not in field or "text" not in field["entry_text"]:
            continue
        text = strip_markup(field["entry_text"]["text"])
        field["entry_text"]["text"] = text  # write back cleaned text
        if not text:
            continue

        if is_cjk_text(text):
            has_cjk = True

        page_info = next(p for p in fields_data["pages"] if p["page_number"] == page_num)
        pdf_width, pdf_height = pdf_dimensions[page_num]

        transformed_bbox = transform_coordinates(
            field["entry_bounding_box"],
            page_info["image_width"],
            page_info["image_height"],
            pdf_width,
            pdf_height,
        )

        field_copy = dict(field)
        field_copy["_transformed_bbox"] = transformed_bbox
        fields_by_page.setdefault(page_num, []).append(field_copy)

    if has_cjk:
        # Embed a real CJK TTF font subset so text displays correctly in any viewer.
        # FreeText annotations only reference a font by name and cannot embed CJK glyphs.
        annotations_added = _fill_with_reportlab_overlay(writer, fields_by_page, pdf_dimensions)
    else:
        annotations_added = 0
        for page_num, fields in fields_by_page.items():
            for field in fields:
                text = field["entry_text"]["text"]
                font_name = field["entry_text"].get("font", "Arial")
                font_size = str(field["entry_text"].get("font_size", 14)) + "pt"
                font_color = field["entry_text"].get("font_color", "000000")

                # Font size/color seems to not work reliably across viewers:
                # https://github.com/py-pdf/pypdf/issues/2084
                annotation = FreeText(
                    text=text,
                    rect=field["_transformed_bbox"],
                    font=font_name,
                    font_size=font_size,
                    font_color=font_color,
                    border_color=None,
                    background_color=None,
                )
                writer.add_annotation(page_number=page_num - 1, annotation=annotation)
                annotations_added += 1

    with open(output_pdf_path, "wb") as output:
        writer.write(output)

    print(f"Successfully filled PDF form and saved to {output_pdf_path}")
    print(f"Added {annotations_added} text annotations")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: fill_pdf_form_with_annotations.py [input pdf] [fields.json] [output pdf]")
        sys.exit(1)
    input_pdf = sys.argv[1]
    fields_json = sys.argv[2]
    output_pdf = sys.argv[3]

    fill_pdf_form(input_pdf, fields_json, output_pdf)

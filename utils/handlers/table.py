import io
import logging
import re
import textwrap
from typing import Any, List, Tuple, Optional
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

# On essaie d'importer la config, sinon on fallback sur un logger par défaut
try:
    from core.config import cfg
    LOGGER_NAME = "EvilGPT"
except ImportError:
    LOGGER_NAME = __name__

logger = logging.getLogger(LOGGER_NAME)

URL_REGEX = r'\[([^\]]+)\]\((https?://[^\s\)]+)\)|(https?://[^\s\)]+)'
TABLE_IMAGE_PLACEHOLDER = "__TABLE_IMG"
EMOJI_BUFFER = 12
COLUMN_MAX_WIDTH = 1200

def _extract_links_and_sanitize(text: str, current_links: List[str]) -> Tuple[str, List[str]]:
    def replacer(match):
        label, url_md, url_plain = match.groups()
        url = url_md or url_plain
        if url in current_links:
            idx = current_links.index(url) + 1
        else:
            current_links.append(url)
            idx = len(current_links)
        
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return f"[{idx}] ({domain})"
    
    sanitized_text = re.sub(URL_REGEX, replacer, text)
    return sanitized_text, current_links

def _get_font(size: int, bold: bool = False, italic: bool = False):
    try:
        if bold and italic:
            path = "assets/fonts/NotoSans-BoldItalic.ttf"
        elif bold:
            path = "assets/fonts/NotoSans-Bold.ttf"
        elif italic:
            path = "assets/fonts/NotoSans-Italic.ttf"
        else:
            path = "assets/fonts/NotoSans-Regular.ttf"
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def _calc_col_widths(headers: List[str], rows: List[List[str]], font: ImageFont.FreeTypeFont, padding: int) -> List[int]:
    img = Image.new("RGB", (1, 1))
    widths = []
    with Pilmoji(img) as pilmoji:
        for i, header in enumerate(headers):
            max_w = pilmoji.draw.textlength(str(header), font=font) + padding * 2
            for row in rows:
                if i < len(row):
                    cell_text = str(row[i])
                    for line in cell_text.split("\n"):
                        raw_w = pilmoji.draw.textlength(line, font=font)
                        if any(ord(c) > 0xFFFF for c in line):
                            raw_w += EMOJI_BUFFER
                        max_w = max(max_w, raw_w + padding * 2)
            widths.append(int(min(max_w, COLUMN_MAX_WIDTH)))
    return widths

def _wrap_text(text: str, max_width: int, font: ImageFont.FreeTypeFont) -> List[str]:
    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        w = draw.textlength(test_line, font=font)
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def _render_table_image(headers: List[str], rows: List[List[str]], alignments: List[str]) -> Tuple[io.BytesIO, List[str]]:
    all_links = []
    sanitized_headers = []
    for h in headers:
        text, all_links = _extract_links_and_sanitize(h, all_links)
        sanitized_headers.append(text)
    
    sanitized_rows = []
    for row in rows:
        san_row = []
        for cell in row:
            text, all_links = _extract_links_and_sanitize(str(cell), all_links)
            san_row.append(text)
        sanitized_rows.append(san_row)

    font_size = 32
    fonts = {
        "reg": _get_font(font_size),
        "bold": _get_font(font_size, bold=True),
        "header": _get_font(font_size + 4, bold=True),
        "line_height": font_size + 10,
    }
    colors = {
        "bg": (7, 7, 9), "header_bg": (28, 28, 32), "row_bg": (7, 7, 9),
        "row_bg_alt": (28, 28, 32), "border": (60, 60, 65), "text": (255, 255, 255),
    }

    padding, header_height, min_row_h = 24, 80, 60
    col_widths = _calc_col_widths(sanitized_headers, sanitized_rows, fonts["reg"], padding)
    
    processed_rows = []
    for row in sanitized_rows:
        row_content = []
        max_h = min_row_h
        for i, cell in enumerate(row):
            wrapped = _wrap_text(cell, col_widths[i] - padding*2, fonts["reg"])
            row_content.append(wrapped)
            max_h = max(max_h, len(wrapped) * fonts["line_height"] + padding)
        processed_rows.append((row_content, max_h))

    total_w = sum(col_widths) + len(col_widths) + 1
    total_h = header_height + sum(h for _, h in processed_rows) + len(processed_rows) + 1
    
    img = Image.new("RGB", (total_w, total_h), colors["bg"])
    draw = ImageDraw.Draw(img)
    with Pilmoji(img) as pilmoji:
        x = 0
        for h_text, w, al in zip(sanitized_headers, col_widths, alignments):
            draw.rectangle([x, 0, x+w, header_height], fill=colors["header_bg"], outline=colors["border"])
            pilmoji.text((x + padding, (header_height - fonts["line_height"]) // 2), h_text, fill=colors["text"], font=fonts["header"])
            x += w + 1
        
        y = header_height + 1
        for idx, (content, h_row) in enumerate(processed_rows):
            x = 0
            bg = colors["row_bg_alt"] if idx % 2 else colors["row_bg"]
            for cell_lines, w, al in zip(content, col_widths, alignments):
                draw.rectangle([x, y, x+w, y+h_row], fill=bg, outline=colors["border"])
                for line_idx, line in enumerate(cell_lines):
                    pilmoji.text((x + padding, y + padding//2 + line_idx * fonts["line_height"]), line, fill=colors["text"], font=fonts["reg"])
                x += w + 1
            y += h_row + 1

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf, all_links

def detect_and_convert_tables(text: str) -> Tuple[str, List[io.BytesIO], List[dict]]:
    table_images = []
    table_data_list = []
    
    code_block_pattern = re.compile(r"```(?:markdown|md)?\n((?:\|.*\|(?:\n|$))+)```", re.MULTILINE)
    
    def replace_table(match):
        lines = [l for l in match.group(1).strip().split("\n") if l.strip()]
        if len(lines) < 2: return match.group(0)
        
        headers = [p.strip() for p in lines[0].strip()[1:-1].split("|")]
        aligns = []
        start_row = 1
        if len(lines) > 1 and re.match(r"^\|[\s\-\:\|]*\|$", lines[1].strip()):
            for p in lines[1].strip()[1:-1].split("|"):
                p = p.strip()
                if p.startswith(":") and p.endswith(":"): aligns.append("center")
                elif p.endswith(":"): aligns.append("right")
                else: aligns.append("left")
            start_row = 2
        
        rows = []
        for i in range(start_row, len(lines)):
            row_raw = lines[i].strip()
            if row_raw.startswith("|"): row_raw = row_raw[1:]
            if row_raw.endswith("|"): row_raw = row_raw[:-1]
            cells = [c.strip() for c in row_raw.split("|")]
            rows.append(cells[:len(headers)] + [""] * (len(headers) - len(cells)))
        
        try:
            buf, links = _render_table_image(headers, rows, aligns or ["left"]*len(headers))
            table_images.append(buf)
            idx = len(table_images) - 1
            table_data_list.append({"id": idx, "headers": headers, "rows": rows, "links": links})
            return f"__TABLE_IMG_{idx}__"
        except Exception as e:
            logger.error(f"Table render error: {e}")
            return match.group(0)

    new_text = code_block_pattern.sub(replace_table, text)
    return new_text, table_images, table_data_list

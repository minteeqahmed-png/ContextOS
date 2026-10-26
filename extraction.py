"""Offline evidence extraction. Coordinates are normalized to the saved frame."""
import base64
import io
import threading
import subprocess
import sys
import os
import json
from pathlib import Path
from PIL import Image, ImageOps

_engine = None
_lock = threading.Lock()


def image_bytes(data):
    raw = base64.b64decode(data.split(',', 1)[1], validate=True)
    with Image.open(io.BytesIO(raw)) as image:
        if image.width * image.height > 24_000_000:
            raise ValueError('Image exceeds 24 megapixels')
        image.verify()
    return raw


def extract_image(data):
    # Kill a stalled native OCR engine rather than leave a thread holding its lock.
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('ocr_worker.py'))],
                            input=data, text=True, capture_output=True,
                            timeout=float(os.environ.get('CONTEXTOS_OCR_TIMEOUT_SECONDS','90')),
                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0), check=True)
    return json.loads(result.stdout)


def extract_image_in_process(data):
    global _engine
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes(data)))).convert('RGB')
    with _lock:
        if _engine is None:
            _engine = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)
        results, _ = _engine(np.asarray(image))
    regions = []
    for box, text, confidence in results or []:
        xs, ys = zip(*box)
        regions.append({'id': str(len(regions)), 'text': text, 'confidence':float(confidence), 'box': [max(0, min(xs)/image.width), max(0, min(ys)/image.height), min(1, max(xs)/image.width), min(1, max(ys)/image.height)], 'method': 'local-ocr'})
    return regions


def render_pdf(raw, number):
    import fitz
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if doc.needs_pass:
            raise ValueError('Password-protected PDFs are not supported')
        if not 1 <= number <= len(doc):
            raise ValueError(f'Choose a page from 1 to {len(doc)}')
        page = doc[number - 1]
        if max(page.rect.width, page.rect.height) > 14400:
            raise ValueError('PDF page is too large')
        scale = min(2, 2000 / max(page.rect.width, page.rect.height))
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        rows = []
        for word in page.get_text('words', sort=True):
            rect = fitz.Rect(word[:4]) * page.rotation_matrix
            row = next((r for r in rows if abs(r['y'] - rect.y0) < 4), None)
            if row is None:
                row = {'y': rect.y0, 'words': []}
                rows.append(row)
            row['words'].append((rect, word[4]))
        regions = []
        for row in sorted(rows, key=lambda r: r['y']):
            words = sorted(row['words'], key=lambda w: w[0].x0)
            x0 = min(w[0].x0 for w in words) / page.rect.width
            y0 = min(w[0].y0 for w in words) / page.rect.height
            x1 = max(w[0].x1 for w in words) / page.rect.width
            y1 = max(w[0].y1 for w in words) / page.rect.height
            regions.append({'id': str(len(regions)), 'text': ' '.join(w[1] for w in words), 'box': [max(0,x0),max(0,y0),min(1,x1),min(1,y1)], 'method': 'pdf-text'})
        return 'data:image/png;base64,' + base64.b64encode(pix.tobytes('png')).decode(), regions, len(doc)

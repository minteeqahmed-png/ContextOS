"""Explicit live smoke test: sends only a generated, non-sensitive chart to Google."""
import base64
import io
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / '.runtime')]
from local_config import load_local_env
load_local_env()
os.environ.update({
    'CONTEXTOS_MODE': 'HYBRID_SANITIZED',
    'CONTEXTOS_REVIEW_POLICY': 'interactive',
    'CONTEXTOS_VISION_PROVIDER': 'openai_compatible',
    'CONTEXTOS_VISION_BASE_URL': 'https://generativelanguage.googleapis.com/v1beta/openai',
    'CONTEXTOS_VISION_MODEL': 'gemini-3.5-flash-lite',
})
from PIL import Image, ImageDraw
import httpx
import vision_privacy as vp


def main():
    out = ROOT / 'evaluation' / 'output' / 'gemini-live'
    out.mkdir(parents=True, exist_ok=True)
    im = Image.new('RGB', (800, 500), 'white')
    d = ImageDraw.Draw(im)
    d.line([(70, 50), (70, 430), (740, 430)], fill='black', width=3)
    d.line([(90, 180), (210, 190), (330, 330), (420, 360), (540, 190), (660, 70), (720, 90)], fill='#008830', width=8)
    d.ellipse((650, 320, 700, 370), fill='#dc2020')
    im.save(out / 'synthetic-chart.png')
    buf = io.BytesIO(); im.save(buf, format='PNG')
    image = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
    sanitized, _, _ = vp.redact(image, [], [])
    c = vp.config()
    report = {'model': c['model'], 'fixture': 'synthetic-chart.png', 'personal_captures_sent': False, 'results': {}}
    for name, prompt, schema in [
        ('descriptor', vp.DESCRIBE, vp.Descriptor),
        ('grounding', vp.GROUND + 'Where is the red circular indicator relative to the high point of the green line? Cite both regions.', vp.Grounding),
    ]:
        start = time.perf_counter()
        try:
            raw = vp.infer(vp.payload(sanitized, prompt, c), vp.target(c))
            (out / (name + '-raw.json')).write_text(json.dumps(raw, indent=2), encoding='utf-8')
            result = schema.model_validate(raw)
            report['results'][name] = {'schema_valid': True, 'elapsed_ms': round((time.perf_counter()-start)*1000), 'output': result.model_dump()}
        except httpx.HTTPStatusError as exc:
            # Never print request headers, key, or unfiltered provider error bodies.
            error = {'http_status': exc.response.status_code}
            try:
                detail = exc.response.json().get('error', {})
                error['provider_status'] = detail.get('status')
                msg = detail.get('message', '')
                key = os.environ.get('CONTEXTOS_VISION_API_KEY', '')
                error['message'] = msg.replace(key, '[REDACTED]')[:1500] if key else msg[:1500]
            except Exception:
                pass
            report['results'][name] = error
            break
        except Exception as exc:
            report['results'][name] = {'error_type': type(exc).__name__}
            break
    (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

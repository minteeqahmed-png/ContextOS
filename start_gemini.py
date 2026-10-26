"""Run the opt-in Gemini demo with a separate local library and interactive review."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def configure():
    from local_config import load_local_env
    load_local_env()
    if not os.environ.get('CONTEXTOS_VISION_API_KEY', '').strip():
        raise SystemExit('Set CONTEXTOS_VISION_API_KEY in .env to your Google AI Studio key.')
    os.environ.update({
        'CONTEXTOS_MODE': 'HYBRID_SANITIZED',
        'CONTEXTOS_REVIEW_POLICY': 'interactive',
        'CONTEXTOS_VISION_PROVIDER': 'openai_compatible',
        'CONTEXTOS_VISION_BASE_URL': 'https://generativelanguage.googleapis.com/v1beta/openai',
        'CONTEXTOS_VISION_MODEL': 'gemini-3.5-flash-lite',
        'CONTEXTOS_OPENROUTER_PROVIDER': '',
        'CONTEXTOS_DB': str(ROOT / 'data' / 'gemini-demo.sqlite3'),
    })


def main():
    configure()
    sys.path.insert(0, str(ROOT / '.runtime'))
    import backend
    import uvicorn
    print('ContextOS Gemini demo: http://127.0.0.1:8003')
    print('Local library; Gemini receives only explicitly approved sanitized frames and queries.')
    print('Model: gemini-3.5-flash-lite. Provider quotas and terms apply.')
    uvicorn.run(backend.app, host='127.0.0.1', port=8003, access_log=False)


if __name__ == '__main__':
    main()

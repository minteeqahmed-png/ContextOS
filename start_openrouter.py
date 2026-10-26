"""Interactive, credential-safe launcher for the isolated OpenRouter test library."""
import getpass
import os
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent


def main():
    from local_config import load_local_env
    load_local_env()
    port = 8002
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1', port)) == 0:
            raise SystemExit('Port 8002 is already in use. Stop that test server before starting another.')
    key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not key:
        key = getpass.getpass('Paste your OpenRouter API key (hidden; never saved to a file): ').strip()
    if not key:
        raise SystemExit('No key entered. Nothing started or sent.')
    os.environ.update({
        'OPENROUTER_API_KEY': key,
        'CONTEXTOS_MODE': 'HYBRID_SANITIZED',
        'CONTEXTOS_REVIEW_POLICY': 'interactive',
        'CONTEXTOS_VISION_PROVIDER': 'openrouter',
        'CONTEXTOS_VISION_BASE_URL': 'https://openrouter.ai/api/v1',
        'CONTEXTOS_VISION_MODEL': 'meta-llama/llama-4-maverick',
        'CONTEXTOS_OPENROUTER_PROVIDER': 'digitalocean',
        'CONTEXTOS_DB': str(ROOT/'evaluation'/'output'/'openrouter-test.sqlite3'),
    })
    sys.path.insert(0, str(ROOT))
    import backend
    import uvicorn
    print('\nContextOS live test: http://127.0.0.1:8002/')
    print('Separate test library; your main library on port 8000 is unchanged.')
    print('Model: Meta Llama 4 Maverick via OpenRouter / DigitalOcean.')
    print('Upload a non-sensitive fixture, review its image/payload, then Approve & Enrich.')
    print('Approved requests may incur provider charges. No request is made just by starting.')
    print('Keep this terminal open. Press Ctrl+C to stop.\n')
    try:
        uvicorn.run(backend.app, host='127.0.0.1', port=port, access_log=False)
    finally:
        os.environ.pop('OPENROUTER_API_KEY', None)


if __name__ == '__main__':
    main()

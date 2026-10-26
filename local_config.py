"""Load literal local .env settings without executing or expanding their contents."""
import os
import re
from pathlib import Path


def load_local_env(path=None):
    path = Path(path) if path else Path(__file__).parent / '.env'
    if not path.is_file():
        return
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, separator, value = line.partition('=')
        name, value = name.strip(), value.strip()
        if not separator or not re.fullmatch(r'[A-Z][A-Z0-9_]*', name):
            raise ValueError('Invalid local .env setting; expected NAME=value')
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        os.environ.setdefault(name, value)

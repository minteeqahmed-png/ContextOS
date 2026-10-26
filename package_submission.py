"""Create a source-only archive from an explicit allowlist; never bundle local data."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'submission'
OUT.mkdir(exist_ok=True)
files = [p for p in ROOT.iterdir() if p.is_file() and p.suffix in {'.py','.js','.css','.html','.md'}]
files += [ROOT / n for n in ('requirements.txt','package.json','.env.example','.gitignore','seeds.json')]
for directory in ('tests', 'evaluation/sources', 'evaluation/captures'):
    files += [p for p in (ROOT / directory).rglob('*') if p.is_file() and p.suffix in {'.py','.png','.html','.pdf'}]
files += [p for p in (ROOT/'evaluation').iterdir() if p.is_file() and p.suffix in {'.py','.md','.json'}]
files = sorted(set(files))
secrets = []
env = ROOT / '.env'
if env.exists():
    for line in env.read_text(encoding='utf-8-sig').splitlines():
        name, _, value = line.partition('=')
        if 'KEY' in name and len(value.strip()) > 12:
            secrets.append(value.strip().strip('"').strip("'"))
for p in files:
    blob = p.read_bytes()
    if any(secret.encode() in blob for secret in secrets):
        raise SystemExit('Packaging stopped: a credential appeared in an allowlisted file.')
archive = OUT / 'ContextOS-source.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in files: z.write(p, 'ContextOS/' + p.relative_to(ROOT).as_posix())
manifest = {'archive': archive.name, 'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(), 'files':[p.relative_to(ROOT).as_posix() for p in files], 'excluded':'All .env secrets, data/, .runtime/, evaluation/output/, databases and caches'}
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Packaged',len(files),'files:',archive)

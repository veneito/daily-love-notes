"""Check the distributable tree for accidental credential/runtime artifacts."""
from pathlib import Path
import json,re,subprocess,sys
root=Path(__file__).resolve().parent
patterns=[
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'),
    re.compile(r'github_pat_[A-Za-z0-9_]{30,}'),
    re.compile(r'AKIA[A-Z0-9]{16}'),
    re.compile(r'#setup=[A-Za-z0-9_-]{20,}'),
    re.compile(r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'),
]
try:files=[root/p for p in subprocess.check_output(['git','ls-files'],cwd=root,text=True,stderr=subprocess.DEVNULL).splitlines()]
except subprocess.CalledProcessError:files=[]
if not files:files=[p for p in root.rglob('*') if p.is_file() and not any(part in ('.git','__pycache__','.gradle','build') for part in p.relative_to(root).parts)]
errors=[]
for path in files:
    relative=path.relative_to(root)
    if path.suffix.lower() in ('.sqlite','.db','.pem','.key','.jks','.keystore','.apk','.aab','.log') or path.name.startswith('.env') and path.name!='.env.example' or any(part in ('.openai','data','room-version-backup') for part in relative.parts):errors.append(str(relative)+': private/runtime artifact')
    if path.suffix.lower()=='.png':continue
    try:text=path.read_text(encoding='utf-8')
    except (UnicodeError,OSError):errors.append(str(relative)+': unexpected binary');continue
    if any(p.search(text) for p in patterns):errors.append(str(relative)+': possible credential (value omitted)')
seed=(root/'dist/notes.js').read_text(encoding='utf-8');notes=json.loads(seed[seed.index('=')+1:].strip().rstrip(';'))
if len(notes)!=365 or len(set(notes))!=365 or not all(n.startswith('Example note ') for n in notes):errors.append('Seed must contain 365 unique placeholder notes.')
if errors:
    print('\n'.join(errors));sys.exit(1)
print(f'Checked {len(files)} files: no detected credentials or private runtime artifacts; all 365 notes are placeholders.')

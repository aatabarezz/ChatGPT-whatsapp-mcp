#!/usr/bin/env python3
"""Connect a user-owned OpenAI tunnel without exposing its runtime key."""
import argparse
import getpass
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tunnel-id', required=True, help='Your own tunnel ID from OpenAI Platform')
    args = parser.parse_args()
    if not re.fullmatch(r'tunnel_[A-Za-z0-9]+', args.tunnel_id):
        parser.error('Expected a tunnel_... identifier, not a URL or API key.')
    root = Path(__file__).resolve().parents[1]
    bundled = root / 'bin/tunnel-runtime/tunnel-client'
    client = str(bundled) if bundled.is_file() else shutil.which('tunnel-client')
    python = root / 'whatsapp-mcp-server/.venv/bin/python'
    if not client or not python.is_file():
        sys.exit('Install the official tunnel-client and run uv sync in whatsapp-mcp-server first. See docs/CODEX_SETUP.md.')
    key = getpass.getpass('Paste the dedicated OpenAI runtime API key (hidden): ').strip()
    if not key.startswith('sk-') or key.count('sk-') != 1 or any(c.isspace() for c in key) or '*' in key:
        sys.exit('Invalid or duplicated key. Nothing saved. Paste the complete key exactly once.')
    os.umask(0o077)
    secret_dir = Path.home() / '.config/tunnel-client/whatsapp-secrets'
    secret_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    secret_dir.chmod(0o700)
    keyfile = secret_dir / 'runtime-key'
    fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        os.fchmod(f.fileno(), 0o600)
        f.write(key)
    del key
    command = shlex.join([str(python), '-B', str(root / 'whatsapp-mcp-server/main.py')])
    subprocess.run([client, 'runtimes', 'connect', '--alias', 'whatsapp', '--profile', 'whatsapp',
                    '--tunnel-id', args.tunnel_id, '--mcp-command', command,
                    '--runtime-api-key', f'file:{keyfile}'], check=True)
    status = subprocess.run([client, 'runtimes', 'status', 'whatsapp', '--json'], check=True, capture_output=True, text=True)
    data = json.loads(status.stdout)
    fields = ('process_running', 'healthy', 'ready')
    print(json.dumps({field: data.get(field) for field in fields}, indent=2))
    if data.get('remote_error') or not all(data.get(field) for field in fields):
        sys.exit('Tunnel is not fully verified. Run tunnel-client runtimes status whatsapp locally; check authentication and permissions. Do not share raw logs or keys.')
    print('Tunnel ready. Add it in ChatGPT Plugins using Connection: Tunnel. Keep this Mac awake.')


if __name__ == '__main__':
    main()

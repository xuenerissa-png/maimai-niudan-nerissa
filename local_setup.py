"""Local launcher with a guided first-run connection flow."""
import os
from pathlib import Path
import subprocess
import sys
from skill.setup import configure


def main():
    root = Path(__file__).resolve().parent
    secret = root / '.private' / 'token'
    args = sys.argv[1:]
    gui = '--gui' in args
    requested = '--configure' in args
    args = [arg for arg in args if arg not in {'--configure', '--gui'}]
    if requested or not secret.exists() or not secret.read_text().strip():
        if not configure(root, gui=gui):
            return 1
        if not args:
            return 0
    env = os.environ.copy()
    env['MCD_MCP_TOKEN'] = secret.read_text().strip()
    return subprocess.call([sys.executable, '-m', 'skill.cli', *(args or ['test'])], cwd=root, env=env)


if __name__ == '__main__':
    raise SystemExit(main())

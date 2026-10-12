import getpass
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
secret = root / '.private' / 'token'
if '--configure' in sys.argv or not secret.exists():
    print('请从 https://open.mcd.cn/mcp 获取个人 Token。')
    token = getpass.getpass('粘贴 Token 后按回车（输入不显示）：').strip()
    if not token:
        raise SystemExit('未输入 Token，未保存配置。')
    secret.parent.mkdir(mode=0o700, exist_ok=True)
    secret.parent.chmod(0o700)
    fd = os.open(secret, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(token)
    print('已保存到本机私有配置，开始测试连接。')
env = os.environ.copy()
env['MCD_MCP_TOKEN'] = secret.read_text().strip()
args = [a for a in sys.argv[1:] if a != '--configure'] or ['test']
raise SystemExit(subprocess.call([sys.executable, '-m', 'skill.cli', *args], cwd=root, env=env))

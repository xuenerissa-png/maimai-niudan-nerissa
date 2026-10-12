"""Local first-run guide. Tokens are never printed or passed as process arguments."""
import getpass
import os
from pathlib import Path
import subprocess
import sys
import webbrowser
from .mcp_client import McDonaldMCP, MCPError

CONSOLE_URL = 'https://open.mcd.cn/mcp'
FIRST_MEAL = '摇个麦门：广州柯木塱附近自取，1人，预算30元，500千卡以内。'


def connection_hint(error):
    text = str(error)
    if '401' in text:
        return '这枚 Token 没有通过验证。请回官方控制台重新复制有效 Token，再运行配置入口。'
    if '429' in text:
        return '官方服务暂时限流，请稍后重新打开配置入口。'
    if '无法连接' in text:
        return '暂时连不上官方服务。请检查网络后再试；不一定是 Token 有问题，不必急着更换。'
    return '这次未能完成连接验证，请稍后重试。已有配置会保留。'


def verify_token(token, client_factory=McDonaldMCP):
    client = client_factory(token=token)
    client.initialize()
    return client.list_tools()


def save_token(root, token):
    private = Path(root) / '.private'
    private.mkdir(mode=0o700, exist_ok=True)
    private.chmod(0o700)
    # Replace only after successful verification; temporary secret is private too.
    temporary = private / 'token.new'
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            if hasattr(os, 'fchmod'):
                os.fchmod(stream.fileno(), 0o600)
            stream.write(token)
        os.replace(temporary, private / 'token')
    finally:
        if temporary.exists():
            temporary.unlink()


def mac_dialog(script):
    completed = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if completed.returncode:
        raise KeyboardInterrupt
    return completed.stdout.strip()


def read_token(gui=False):
    if gui and sys.platform == 'darwin':
        choice = mac_dialog('''button returned of (display dialog "欢迎使用麦麦扭蛋！\\n\\n① 打开麦当劳官方控制台，登录后进入「控制台」。\\n② 首次使用按页面提示激活 MCP，复制个人 Token。\\n③ 回到这里，点击「我已复制」。\\n\\nToken 只在本机填写，不要发到聊天里。" with title "连接麦当劳 · 第1步" buttons {"取消", "打开控制台", "我已复制"} default button "打开控制台" cancel button "取消")''')
        if choice == '打开控制台':
            webbrowser.open(CONSOLE_URL)
            mac_dialog('''display dialog "请在浏览器完成登录、激活并复制 Token。\\n\\n复制好了，再点「继续填写」。" with title "连接麦当劳 · 第2步" buttons {"取消", "继续填写"} default button "继续填写" cancel button "取消"''')
        return mac_dialog('''text returned of (display dialog "在下面粘贴刚复制的个人 Token。\\n输入以圆点隐藏，仅保存在本机；验证成功后才保存。" with title "连接麦当劳 · 第3步" default answer "" with hidden answer buttons {"取消", "验证连接"} default button "验证连接" cancel button "取消")''')
    print('第1步：打开麦当劳官方控制台：' + CONSOLE_URL)
    print('第2步：登录 → 控制台 → 按提示激活 MCP → 复制个人 Token。')
    print('第3步：回到本窗口粘贴。Mac 按 ⌘V，Windows/Linux 按终端的粘贴快捷键。')
    print('输入时不会显示文字或星号，这是正常的；粘贴后按回车。不要把 Token 发到聊天里。')
    if not sys.stdin.isatty():
        raise MCPError('请在你自己的终端运行配置入口，不能从聊天或管道输入 Token。')
    return getpass.getpass('在这里粘贴 Token：')


def configure(root, *, gui=False, token_reader=None, client_factory=McDonaldMCP, output=print):
    output('欢迎使用麦麦扭蛋！只需连接一次麦当劳，之后就能摇餐。')
    try:
        token = (token_reader or (lambda: read_token(gui)))().strip()
        if not token:
            output('没有填写 Token，配置未更改。想继续时重新打开配置入口即可。')
            return False
        if any(char.isspace() for char in token):
            output('复制内容中有空格或换行，请只复制 Token 本身。配置未更改。')
            return False
        output('正在验证官方连接…')
        tools = verify_token(token, client_factory)
        if not tools:
            raise MCPError('官方未返回工具')
        save_token(root, token)
    except (KeyboardInterrupt, EOFError):
        output('已取消，配置未更改。想继续时重新打开配置入口即可。')
        return False
    except MCPError as error:
        output(connection_hint(error))
        output('本次未保存新 Token；已有配置未更改。')
        return False
    except OSError:
        output('无法读取输入或保存配置，请在可写的本机目录运行，并检查终端是否可用。')
        return False
    output('连接成功！Token 已保存在本机，下次不需要重复填写。')
    output('下一步：在已安装本 Skill 的 AI 助手中说「' + FIRST_MEAL + '」')
    output('助手会先查询真实菜单，再核验价格和热量；下单前会确认。')
    if gui and sys.platform == 'darwin':
        try:
            mac_dialog('''display dialog "连接成功！\\n\\n回到已安装麦麦扭蛋 Skill 的 AI 助手，试着说：\\n「摇个麦门，1人，预算30元，500千卡以内。」\\n\\n再告诉助手城市和附近地标，就能查询真实菜单。\\nToken 已保存在本机，下次无需重复填写。" with title "麦麦扭蛋 · 已连接" buttons {"开始摇餐"} default button "开始摇餐"''')
        except (KeyboardInterrupt, OSError):
            pass
    return True

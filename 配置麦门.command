#!/bin/zsh
cd -- "${0:A:h}"
if ! command -v python3 >/dev/null 2>&1; then
  printf '还没有找到 Python。请先从 https://www.python.org/downloads/ 安装 Python 3.10 或更新版本，再重新打开此文件。\n'
else
  python3 local_setup.py --configure --gui
fi
printf '\n操作已结束，按回车关闭窗口…'
read -r

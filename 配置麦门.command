#!/bin/zsh
cd -- "${0:A:h}"
python3 local_setup.py --configure
printf '\n按回车关闭窗口…'
read -r

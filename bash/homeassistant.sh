#!/bin/bash

PYTHON=$1
# Upgrade home assistant  to the latest version
${PYTHON} -m pip install homeassistant -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade
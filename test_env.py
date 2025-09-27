#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Python环境测试脚本
"""

import sys
import os

print("=== Python环境测试 ===")
print(f"Python版本: {sys.version}")
print(f"Python可执行文件: {sys.executable}")
print(f"当前工作目录: {os.getcwd()}")
print(f"系统: {sys.platform}")
print("测试成功!")
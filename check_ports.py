# -*- coding: utf-8 -*-
"""
检查可用串口脚本
用于列出当前系统中所有可用的串口
"""

import serial.tools.list_ports

print("===== 可用串口列表 =====")
ports = serial.tools.list_ports.comports()
if not ports:
    print("未找到可用的串口")
else:
    for i, port in enumerate(ports):
        print(f"[{i+1}] 设备: {port.device}")
        print(f"    描述: {port.description}")
        print(f"    硬件ID: {port.hwid}")
        print()
print("===== 检查完成 =====")
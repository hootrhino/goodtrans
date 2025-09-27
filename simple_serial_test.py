#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的串口连接测试脚本
"""

import sys
import time
from serial_manager import SerialManager

print("=== 简单串口连接测试 ===")
print(f"Python版本: {sys.version}")

# 测试COM16串口连接
try:
    print("\n尝试连接COM16...")
    manager = SerialManager(address=1001, verify_code="1234")
    success = manager.connect("COM16")
    
    if success:
        print("✓ COM16连接成功!")
        
        # 获取可用串口列表
        ports = manager.get_available_ports()
        print(f"\n可用串口列表: {ports}")
        
        # 等待一会儿
        time.sleep(1)
        
        # 断开连接
        manager.disconnect()
        print("已断开COM16连接")
    else:
        print("✗ COM16连接失败!")

except Exception as e:
    print(f"连接COM16时发生错误: {e}")
    import traceback
    traceback.print_exc()

# 测试COM17串口连接
try:
    print("\n尝试连接COM17...")
    manager = SerialManager(address=1002, verify_code="1234")
    success = manager.connect("COM17")
    
    if success:
        print("✓ COM17连接成功!")
        
        # 等待一会儿
        time.sleep(1)
        
        # 断开连接
        manager.disconnect()
        print("已断开COM17连接")
    else:
        print("✗ COM17连接失败!")

except Exception as e:
    print(f"连接COM17时发生错误: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")
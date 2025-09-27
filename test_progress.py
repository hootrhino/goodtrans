#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度条测试脚本
专门用于测试发送方的进度条更新功能
"""

import os
import time
from serial_manager import SerialManager

# 全局变量
manager1 = None  # 发送方管理器
manager2 = None  # 接收方管理器

# 生成一个较小的测试文件（约100KB）以便快速测试
TEST_FILE_NAME = "progress_test_file.txt"
TEST_FILE_CONTENT = "这是测试进度条的文件内容。\n" * 10000


def create_test_file():
    """创建测试文件"""
    with open(TEST_FILE_NAME, "w", encoding="utf-8") as f:
        f.write(TEST_FILE_CONTENT)
    print(f"已创建测试文件: {TEST_FILE_NAME}")


def on_file_progress(address, received_size, total_size):
    """文件传输进度回调函数"""
    if total_size > 0:
        progress = (received_size / total_size) * 100
        # 明确区分发送方和接收方的进度
        if address == 1001:  # 发送方进度
            print(f"发送进度: {progress:.1f}% ({received_size}/{total_size} 字节)")
        else:  # 接收方进度
            print(f"接收进度: {progress:.1f}% ({received_size}/{total_size} 字节)")


def on_file_received(address, file_path, file_name):
    """文件接收回调函数"""
    print(f"\n✓ 文件接收成功!\n接收自: 节点 {address}\n保存路径: {file_path}\n文件名: {file_name}")


def main():
    """主函数"""
    global manager1, manager2
    
    try:
        print("===== 进度条测试 =====")
        
        # 创建测试文件
        create_test_file()
        
        # 初始化管理器
        print("\n初始化串口管理器...")
        manager1 = SerialManager(address=1001, verify_code="1234")
        manager1.on_file_progress = on_file_progress
        
        manager2 = SerialManager(address=1002, verify_code="1234")
        manager2.on_file_progress = on_file_progress
        manager2.on_file_received = on_file_received
        
        # 连接串口
        print("正在连接串口COM18...")
        if not manager1.connect("COM18"):
            print("COM18连接失败!")
            return
        print("COM18连接成功!")
        
        print("正在连接串口COM19...")
        if not manager2.connect("COM19"):
            print("COM19连接失败!")
            return
        print("COM19连接成功!")
        
        # 设置配对密码并配对
        print("\n设置配对密码并配对...")
        manager1.pairing_passwords[1002] = "test123"
        manager2.pairing_passwords[1001] = "test123"
        
        # 发现节点
        print("\n执行节点发现...")
        for _ in range(3):
            manager1.broadcast_discover()
            manager2.broadcast_discover()
            time.sleep(0.5)
        
        time.sleep(1)
        
        # 请求配对
        print("\n请求配对...")
        success = manager1.request_pair(1002, "test123")
        if success:
            print("配对请求发送成功")
        else:
            print("配对请求发送失败")
        
        # 等待配对完成
        time.sleep(2)
        
        # 检查配对状态
        is_paired = manager1.is_node_paired(1002) and manager2.is_node_paired(1001)
        print(f"配对状态: {is_paired}")
        
        if not is_paired:
            print("配对失败，测试终止")
            return
        
        # 执行文件传输
        print("\n开始文件传输...")
        success = manager1.send_file(1002, TEST_FILE_NAME)
        
        if success:
            print("文件发送命令已发出")
            # 等待文件传输完成
            time.sleep(5)
        else:
            print("文件发送命令失败")
        
        print("\n===== 测试完成 =====")
        
    finally:
        # 清理资源
        print("\n清理资源...")
        if manager1:
            manager1.disconnect()
        if manager2:
            manager2.disconnect()
        
        if os.path.exists(TEST_FILE_NAME):
            try:
                os.remove(TEST_FILE_NAME)
                print(f"已删除测试文件: {TEST_FILE_NAME}")
            except:
                pass


if __name__ == "__main__":
    main()
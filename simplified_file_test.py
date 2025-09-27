#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版串口文件传输测试脚本
"""

import os
import time
import sys
from serial_manager import SerialManager
from protocol import MessageType

# 创建一个小的测试文件
TEST_FILE_NAME = "small_test_file.txt"
TEST_FILE_CONTENT = "这是一个用于测试的小文件。"

# 全局变量
file_received_flag = False
received_content = ""


def create_test_file():
    """创建测试文件"""
    with open(TEST_FILE_NAME, 'w', encoding='utf-8') as f:
        f.write(TEST_FILE_CONTENT)
    print(f"已创建测试文件: {TEST_FILE_NAME}")


def on_file_received(address, file_path, file_name):
    """文件接收回调函数"""
    global file_received_flag, received_content
    file_received_flag = True
    
    print(f"\n✓ 文件接收成功!")
    print(f"接收自: 节点 {address}")
    print(f"保存路径: {file_path}")
    print(f"文件名: {file_name}")
    
    # 读取接收到的文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        received_content = f.read()


def main():
    """主函数"""
    print("=== 简化版文件传输测试 ===")
    print(f"Python版本: {sys.version}")
    
    try:
        # 创建测试文件
        create_test_file()
        
        # 初始化接收端（COM17）
        print("\n初始化接收端（COM17）...")
        receiver = SerialManager(address=1002, verify_code="1234")
        receiver.on_file_received = on_file_received
        
        if not receiver.connect("COM17"):
            print("✗ 无法连接到COM17，测试终止。")
            return
        print("✓ COM17连接成功")
        
        # 初始化发送端（COM16）
        print("\n初始化发送端（COM16）...")
        sender = SerialManager(address=1001, verify_code="1234")
        
        if not sender.connect("COM16"):
            print("✗ 无法连接到COM16，测试终止。")
            receiver.disconnect()
            return
        print("✓ COM16连接成功")
        
        # 等待一会儿
        time.sleep(1)
        
        # 模拟配对（直接添加到已配对节点）
        print("\n模拟节点配对...")
        sender.paired_nodes.add(1002)  # 假设已配对
        receiver.paired_nodes.add(1001)  # 假设已配对
        print("✓ 节点配对完成")
        
        # 发送文件
        print(f"\n发送文件: {TEST_FILE_NAME}")
        success = sender.send_file(1002, TEST_FILE_NAME)
        
        if success:
            print("✓ 文件发送命令已发出")
            
            # 等待文件接收完成，最多等待5秒
            start_time = time.time()
            while not file_received_flag and time.time() - start_time < 5:
                print("等待文件接收...")
                time.sleep(0.5)
            
            if file_received_flag:
                # 验证文件内容
                if received_content == TEST_FILE_CONTENT:
                    print("✓ 文件内容验证成功!")
                    print("🎉 文件传输测试成功!")
                else:
                    print("✗ 文件内容验证失败!")
                    print(f"期望: {TEST_FILE_CONTENT}")
                    print(f"实际: {received_content}")
            else:
                print("✗ 文件传输超时!")
        else:
            print("✗ 文件发送命令失败!")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        try:
            if 'sender' in locals():
                sender.disconnect()
            if 'receiver' in locals():
                receiver.disconnect()
            
            # 删除测试文件
            if os.path.exists(TEST_FILE_NAME):
                os.remove(TEST_FILE_NAME)
                print(f"已删除测试文件: {TEST_FILE_NAME}")
            
            # 删除接收到的文件
            for f in os.listdir('.'):
                if f.startswith('received_'):
                    os.remove(f)
                    print(f"已删除接收到的文件: {f}")
        except Exception as e:
            print(f"清理资源时发生错误: {e}")
        
        print("\n=== 测试完成 ===")


if __name__ == "__main__":
    main()
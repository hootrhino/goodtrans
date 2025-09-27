#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口文件传输测试脚本
用于测试COM16和COM17之间的文件传输功能
"""

import os
import time
import sys
from serial_manager import SerialManager
from protocol import MessageType

# 创建一个测试文件
TEST_FILE_NAME = "test_transfer_file.txt"
# 生成大约1MB的测试内容
TEST_FILE_CONTENT = "这是一个测试文件内容，用于验证串口大文件传输功能。\n" * 50000

# 全局变量
manager1 = None  # 连接到COM16的管理器
manager2 = None  # 连接到COM17的管理器
is_manager1_connected = False
is_manager2_connected = False
manager1_nodes = []
manager2_nodes = []
file_received_flag = False


def create_test_file():
    """创建测试文件"""
    with open(TEST_FILE_NAME, "w", encoding="utf-8") as f:
        f.write(TEST_FILE_CONTENT)
    print(f"已创建测试文件: {TEST_FILE_NAME}")


def on_file_received(address, file_path, file_name):
    """文件接收回调函数"""
    global file_received_flag
    file_received_flag = True
    print(
        f"\n✓ 文件接收成功!\n接收自: 节点 {address}\n保存路径: {file_path}\n文件名: {file_name}"
    )

    # 验证文件内容
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if content == TEST_FILE_CONTENT:
        print("✓ 文件内容验证成功!")
    else:
        print("✗ 文件内容验证失败!")


def on_file_progress(address, received_size, total_size):
    """文件传输进度回调函数"""
    if total_size > 0:
        progress = (received_size / total_size) * 100
        # 区分发送方和接收方的进度更新
        if address == 1001 and received_size < total_size:  # 发送方的进度更新
            print(
                f"\r发送进度: {progress:.1f}% ({received_size}/{total_size} 字节)              ")
        else:  # 接收方的进度更新
            print(
                f"\r接收进度: {progress:.1f}% ({received_size}/{total_size} 字节)              ")


def on_node_discovered(address):
    """节点发现回调函数"""
    print(f"发现节点: {address}")


def init_managers():
    """初始化两个SerialManager实例"""
    global manager1, manager2, is_manager1_connected, is_manager2_connected

    # 初始化第一个管理器（COM16）
    manager1 = SerialManager(address=1001, verify_code="1234")
    manager1.on_file_received = on_file_received
    manager1.on_file_progress = on_file_progress
    manager1.on_node_discovered = on_node_discovered

    # 初始化第二个管理器（COM17）
    manager2 = SerialManager(address=1002, verify_code="1234")
    manager2.on_file_received = on_file_received
    manager2.on_file_progress = on_file_progress
    manager2.on_node_discovered = on_node_discovered

    # 连接串口
    print("正在连接串口COM18...")
    is_manager1_connected = manager1.connect("COM18")
    if is_manager1_connected:
        print("COM18连接成功!")
    else:
        print("COM18连接失败!")

    print("正在连接串口COM19...")
    is_manager2_connected = manager2.connect("COM19")
    if is_manager2_connected:
        print("COM19连接成功!")
    else:
        print("COM19连接失败!")


def discover_nodes():
    """执行节点发现"""
    global manager1_nodes, manager2_nodes

    print("\n开始节点发现...")

    # 两边都广播发现消息
    for _ in range(3):  # 尝试3次
        manager1.broadcast_discover()
        manager2.broadcast_discover()
        time.sleep(1)  # 等待响应

    # 获取发现的节点
    time.sleep(1)  # 再等待一会确保所有响应都被处理
    manager1_nodes = manager1.get_discovered_nodes()
    manager2_nodes = manager2.get_discovered_nodes()

    print(f"COM18发现的节点: {manager1_nodes}")
    print(f"COM19发现的节点: {manager2_nodes}")

    return len(manager1_nodes) > 0 and len(manager2_nodes) > 0


def pair_nodes():
    """进行节点配对"""
    print("\n开始节点配对...")

    # 设置配对密码
    manager1.pairing_passwords[1002] = "test123"
    manager2.pairing_passwords[1001] = "test123"

    # manager1 向 manager2 发送配对请求
    if 1002 in manager1_nodes:
        success = manager1.request_pair(1002, "test123")  # 使用正确的方法和密码
        if success:
            print("COM18已发送配对请求到COM19")
        else:
            print("COM18发送配对请求失败")

    # 等待配对完成
    time.sleep(3)  # 增加等待时间确保配对流程完成

    # 检查配对状态
    is_paired1 = manager1.is_node_paired(1002)
    is_paired2 = manager2.is_node_paired(1001)

    print(f"COM18与COM19配对状态: {is_paired1}")
    print(f"COM19与COM18配对状态: {is_paired2}")

    return is_paired1 and is_paired2


def test_file_transfer():
    """测试文件传输"""
    global file_received_flag

    print("\n开始文件传输测试...")
    print(f"发送文件: {TEST_FILE_NAME}")

    # 从COM16发送文件到COM17
    success = manager1.send_file(1002, TEST_FILE_NAME)

    if success:
        print("文件发送命令已发出")

        # 等待文件接收完成，延长超时时间到180秒（3分钟）以适应大文件传输
        start_time = time.time()
        while not file_received_flag and time.time() - start_time < 180:
            time.sleep(0.5)

        if not file_received_flag:
            print("✗ 文件传输超时!")
    else:
        print("✗ 文件发送命令失败!")


def cleanup():
    """清理资源"""
    global manager1, manager2

    # 断开连接
    if manager1:
        manager1.disconnect()
    if manager2:
        manager2.disconnect()

    # 删除测试文件
    if os.path.exists(TEST_FILE_NAME):
        try:
            os.remove(TEST_FILE_NAME)
            print(f"已删除测试文件: {TEST_FILE_NAME}")
        except:
            pass


def main():
    """主函数"""
    print("脚本已启动...")
    try:
        print("===== 串口文件传输测试 =====")
        print(f"Python版本: {sys.version}")
        print(f"当前工作目录: {os.getcwd()}")

        # 创建测试文件
        print("\n1. 创建测试文件...")
        create_test_file()

        # 初始化管理器
        print("\n2. 初始化串口管理器...")
        init_managers()

        if not (is_manager1_connected and is_manager2_connected):
            print("无法连接到串口，测试终止。")
            return

        # 节点发现
        print("\n3. 执行节点发现...")
        if not discover_nodes():
            print("节点发现失败，测试终止。")
            return

        # 节点配对
        print("\n4. 进行节点配对...")
        if not pair_nodes():
            print("节点配对失败，测试终止。")
            return

        # 测试文件传输
        print("\n5. 开始文件传输测试...")
        test_file_transfer()

        print("\n===== 测试完成 =====")

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\n清理资源...")
        cleanup()
        print("脚本已结束")


if __name__ == "__main__":
    main()

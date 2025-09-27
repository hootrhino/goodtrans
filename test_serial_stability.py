import serial
import time
import sys
from serial_manager import SerialManager

# 测试脚本：验证Write timeout错误修复效果

def main():
    print("===== 串口通信稳定性测试 ======")
    
    try:
        # 获取可用串口
        manager = SerialManager()
        ports = manager.get_available_ports()
        
        if not ports:
            print("未找到可用串口")
            sys.exit(1)
            
        print("可用串口列表:")
        for i, port in enumerate(ports):
            print(f"{i+1}. {port['device']} - {port['description']}")
            
        # 选择串口
        choice = input("请选择要测试的串口序号: ")
        try:
            port_index = int(choice) - 1
            if port_index < 0 or port_index >= len(ports):
                print("无效的选择")
                sys.exit(1)
            selected_port = ports[port_index]['device']
        except ValueError:
            print("请输入有效的数字")
            sys.exit(1)
            
        # 设置地址和验证码
        address = int(input("请输入本机地址 (默认: 1000): ") or "1000")
        verify_code = input("请输入验证码 (默认: 1234): ") or "1234"
        
        # 连接串口
        print(f"\n连接到串口: {selected_port}")
        manager = SerialManager(selected_port, address, verify_code)
        
        if not manager.is_connected:
            print("连接失败，请检查串口是否被占用")
            sys.exit(1)
        
        print("串口连接成功！开始测试各种操作的稳定性...")
        
        # 测试节点发现
        print("\n=== 测试节点发现广播 ===")
        for i in range(5):
            print(f"广播发现请求 {i+1}/5...")
            manager.broadcast_discover()
            time.sleep(1)
        
        # 测试文本发送（假设目标节点地址为1001）
        target_address = int(input("\n请输入测试文本消息的目标节点地址 (默认: 1001): ") or "1001")
        print("\n=== 测试文本消息发送 ===")
        for i in range(5):
            message = f"测试消息 {i+1} - {time.strftime('%H:%M:%S')}"
            print(f"发送文本消息 {i+1}/5: {message}")
            result = manager.send_text(target_address, message)
            print(f"发送结果: {'成功' if result else '失败'}")
            time.sleep(1)
        
        # 测试配对请求
        should_test_pair = input("\n是否测试配对请求? (y/n, 默认: n): ") or "n"
        if should_test_pair.lower() == 'y':
            pair_address = int(input("请输入要配对的节点地址: "))
            pair_password = input("请输入配对密码: ")
            print(f"\n=== 测试配对请求 ===")
            result = manager.request_pair(pair_address, pair_password)
            print(f"配对请求结果: {'成功' if result else '失败'}")
        
        print("\n===== 测试完成 ======")
        print("请检查是否有Write timeout错误发生。")
        print("如果测试过程中没有出现Write timeout错误，说明修复有效。")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
if __name__ == "__main__":
    main()
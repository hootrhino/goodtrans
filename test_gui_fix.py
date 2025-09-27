import serial
import time
import os
import sys
from serial_manager import SerialManager

# 简单的GUI文件传输测试脚本

def main():
    print("===== GUI文件传输问题测试 ======")
    
    try:
        # 创建测试文件
        test_file_path = "test_gui_transfer.txt"
        file_size_mb = 2  # 创建一个2MB的测试文件
        print(f"创建{file_size_mb}MB的测试文件...")
        
        with open(test_file_path, 'wb') as f:
            # 写入指定大小的随机数据
            for i in range(file_size_mb * 1024):
                f.write(os.urandom(1024))
                if i % 100 == 0:
                    print(f"生成中: {i/10.24:.1f}%")
        
        print(f"测试文件创建完成: {test_file_path}")
        print(f"文件大小: {os.path.getsize(test_file_path)/1024/1024:.2f}MB")
        
        print("\n请确保您已打开GUI应用程序并连接了串口")
        print("请在GUI中选择目标节点并尝试发送这个测试文件")
        print("观察是否还有Write timeout错误")
        print("\n按Enter键退出...")
        
        # 等待用户输入
        input()
        
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"测试文件已删除: {test_file_path}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        sys.exit(1)
    
    print("\n===== 测试完成 ======")
    
if __name__ == "__main__":
    main()
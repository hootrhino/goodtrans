"""
串口通讯协议定义
Protocol Format:
[HEADER][TYPE][LENGTH][ADDRESS][VERIFY_CODE][PAYLOAD][CRC]
- HEADER: 2 bytes, 0xAA55
- TYPE: 1 byte, 消息类型
- LENGTH: 2 bytes, 总消息长度
- ADDRESS: 4 bytes, 发送方地址
- VERIFY_CODE: 4 bytes, 验证码
- PAYLOAD: 变长, 实际数据
- CRC: 2 bytes, 校验和
"""

import struct
import hashlib
import json

class MessageType:
    DISCOVER = 0x01      # 节点发现
    DISCOVER_ACK = 0x02  # 发现响应
    TEXT = 0x03          # 文本消息
    FILE_START = 0x04    # 文件传输开始
    FILE_DATA = 0x05     # 文件数据块
    FILE_END = 0x06      # 文件传输结束
    PAIR_REQUEST = 0x07  # 配对请求
    PAIR_RESPONSE = 0x08 # 配对响应
    PAIR_CONFIRM = 0x09  # 配对确认
    AUTH_REQUEST = 0x07  # 认证请求
    AUTH_RESPONSE = 0x08 # 认证响应

class SerialProtocol:
    HEADER = b'\x55\xAA'
    HEADER_BYTES = 2
    TYPE_BYTES = 1
    LENGTH_BYTES = 2
    ADDRESS_BYTES = 4
    VERIFY_CODE_BYTES = 4
    CRC_BYTES = 2
    
    MIN_PACKET_SIZE = HEADER_BYTES + TYPE_BYTES + LENGTH_BYTES + ADDRESS_BYTES + VERIFY_CODE_BYTES + CRC_BYTES
    
    def __init__(self, verify_code="1234"):
        verify_code_str = str(verify_code)
        self.verify_code = verify_code_str.encode('utf-8')[:4]
        if len(self.verify_code) < 4:
            self.verify_code = self.verify_code.ljust(4, b'0')
    
    def calculate_crc(self, data):
        """计算CRC16校验"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    def create_packet(self, msg_type, address, payload=b''):
        """创建数据包"""
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        elif isinstance(payload, dict):
            payload = json.dumps(payload).encode('utf-8')
        
        length = self.MIN_PACKET_SIZE + len(payload)
        
        # 构建包头
        packet = self.HEADER
        packet += struct.pack('B', msg_type)
        packet += struct.pack('<H', length)
        packet += struct.pack('<I', address)
        packet += self.verify_code
        packet += payload
        
        # 计算CRC
        crc = self.calculate_crc(packet)
        packet += struct.pack('<H', crc)
        
        return packet
    
    def parse_packet(self, data):
        """解析数据包"""
        if len(data) < self.MIN_PACKET_SIZE:
            return None
        
        # 检查包头
        if data[:2] != self.HEADER:
            return None
        
        # 解析长度
        length = struct.unpack('<H', data[3:5])[0]
        
        if len(data) < length:
            return None
        
        # 检查CRC
        received_crc = struct.unpack('<H', data[-2:])[0]
        calculated_crc = self.calculate_crc(data[:-2])
        
        if received_crc != calculated_crc:
            return None
        
        # 解析消息
        msg_type = struct.unpack('B', data[2:3])[0]
        address = struct.unpack('<I', data[5:9])[0]
        verify_code = data[9:13]
        payload = data[13:-2]
        
        return {
            'type': msg_type,
            'address': address,
            'verify_code': verify_code,
            'payload': payload,
            'raw': data
        }
    
    def verify_auth(self, received_code):
        """验证验证码"""
        return received_code == self.verify_code
"""
串口管理器
处理串口通信、节点发现、文件传输等功能
"""

import serial
import serial.tools.list_ports
import threading
import time
import os
import struct
import json
from protocol import SerialProtocol, MessageType

class SerialManager:
    def __init__(self, port_name=None, address=1000, verify_code="1234", baudrate=115200):
        self.address = address
        self.verify_code = verify_code
        self.protocol = SerialProtocol(verify_code)
        self.baudrate = baudrate
        
        self.serial_port = None
        self.is_connected = False
        self.is_running = False
        self.receive_thread = None
        
        # 回调函数
        self.on_text_received = None
        self.on_file_received = None
        self.on_node_discovered = None
        self.on_file_progress = None
        
        # 节点列表
        self.discovered_nodes = {}
        
        # 配对管理
        self.paired_nodes = set()  # 已配对的节点
        self.pairing_passwords = {}  # 节点配对密码
        self.pending_pairs = {}  # 待处理的配对请求
        
        # 文件传输相关
        self.file_receive_buffer = {}
        self.file_send_buffer = {}
        
        # 如果提供了端口名称，自动连接
        if port_name:
            self.connect(port_name, baudrate)
        
    def get_available_ports(self):
        """获取可用串口列表"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports
    
    def connect(self, port_name, baudrate=115200):
        """连接串口"""
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                timeout=1,
                bytesize=8,
                parity='N',
                stopbits=1
            )
            self.is_connected = True
            self.start_receive_thread()
            return True
        except Exception as e:
            print(f"连接串口失败: {e}")
            return False
    
    def disconnect(self):
        """断开串口连接"""
        self.is_connected = False
        self.is_running = False
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1)
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
    
    def start_receive_thread(self):
        """启动接收线程"""
        self.is_running = True
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
    
    def _receive_loop(self):
        """接收循环"""
        buffer = b''
        while self.is_running and self.is_connected:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    buffer += data
                    
                    # 处理完整的数据包
                    while True:
                        packet = self._extract_packet(buffer)
                        if packet:
                            buffer = buffer[len(packet['raw']):]
                            self._handle_packet(packet)
                        else:
                            break
                            
                time.sleep(0.01)
            except Exception as e:
                print(f"接收数据错误: {e}")
                break
    
    def _extract_packet(self, buffer):
        """从缓冲区提取完整的数据包"""
        if len(buffer) < self.protocol.MIN_PACKET_SIZE:
            return None
        
        # 查找包头
        header_pos = buffer.find(self.protocol.HEADER)
        if header_pos == -1:
            return None
        
        buffer = buffer[header_pos:]
        
        if len(buffer) < 5:  # 至少需要包头+类型+长度
            return None
        
        # 获取消息长度
        length = struct.unpack('<H', buffer[3:5])[0]
        
        if len(buffer) < length:
            return None
        
        # 解析数据包
        packet = self.protocol.parse_packet(buffer[:length])
        return packet
    
    def _handle_packet(self, packet):
        """处理接收到的数据包"""
        # 验证验证码 - 确保验证码是字符串格式
        verify_code_str = str(self.verify_code)
        if packet['verify_code'] != verify_code_str.encode('utf-8')[:4]:
            print("验证码验证失败")
            return
        
        msg_type = packet['type']
        
        if msg_type == MessageType.DISCOVER:
            # 节点发现
            self._handle_discover(packet)
        elif msg_type == MessageType.DISCOVER_ACK:
            # 发现响应
            self._handle_discover_ack(packet)
        elif msg_type == MessageType.PAIR_REQUEST:
            # 配对请求
            self._handle_pair_request(packet)
        elif msg_type == MessageType.PAIR_RESPONSE:
            # 配对响应
            self._handle_pair_response(packet)
        elif msg_type == MessageType.PAIR_CONFIRM:
            # 配对确认
            self._handle_pair_confirm(packet)
        elif msg_type == MessageType.TEXT:
            # 文本消息
            self._handle_text(packet)
        elif msg_type == MessageType.FILE_START:
            # 文件传输开始
            self._handle_file_start(packet)
        elif msg_type == MessageType.FILE_DATA:
            # 文件数据
            self._handle_file_data(packet)
        elif msg_type == MessageType.FILE_END:
            # 文件传输结束
            self._handle_file_end(packet)
    
    def broadcast_discover(self):
        """广播节点发现"""
        if not self.is_connected:
            return
        
        packet = self.protocol.create_packet(
            MessageType.DISCOVER,
            self.address,
            {'address': self.address, 'verify_code': str(self.verify_code)}
        )
        
        try:
            self.serial_port.write(packet)
        except Exception as e:
            print(f"广播发现失败: {e}")
    
    def _handle_discover(self, packet):
        """处理节点发现"""
        try:
            data = json.loads(packet['payload'].decode('utf-8'))
            node_address = data['address']
            
            # 发送响应
            response = self.protocol.create_packet(
                MessageType.DISCOVER_ACK,
                self.address,
                {'address': self.address, 'verify_code': str(self.verify_code)}
            )
            
            self.serial_port.write(response)
            
        except Exception as e:
            print(f"处理发现消息错误: {e}")
    
    def _handle_discover_ack(self, packet):
        """处理发现响应"""
        try:
            data = json.loads(packet['payload'].decode('utf-8'))
            node_address = data['address']
            
            self.discovered_nodes[node_address] = {
                'address': node_address,
                'last_seen': time.time()
            }
            
            if self.on_node_discovered:
                self.on_node_discovered(node_address)
                
        except Exception as e:
            print(f"处理发现响应错误: {e}")
    
    def _handle_text(self, packet):
        """处理文本消息"""
        try:
            # 检查发送方是否已配对
            if not self.is_node_paired(packet['address']):
                print(f"收到来自未配对节点 {packet['address']} 的消息，已忽略")
                return
                
            text = packet['payload'].decode('utf-8')
            if self.on_text_received:
                self.on_text_received(packet['address'], text)
        except Exception as e:
            print(f"处理文本消息错误: {e}")
    
    def request_pair(self, target_address, password):
        """请求与目标节点配对"""
        if not self.is_connected:
            return False
        
        try:
            # 存储待处理的配对请求
            self.pending_pairs[target_address] = {
                'password': password,
                'timestamp': time.time()
            }
            
            # 发送配对请求
            pair_data = {
                'requester_address': self.address,
                'password': password
            }
            
            packet = self.protocol.create_packet(
                MessageType.PAIR_REQUEST,
                self.address,
                pair_data
            )
            
            self.serial_port.write(packet)
            return True
            
        except Exception as e:
            print(f"发送配对请求失败: {e}")
            return False
    
    def _handle_pair_request(self, packet):
        """处理配对请求，添加确认对话框"""
        try:
            data = json.loads(packet['payload'].decode('utf-8'))
            requester_address = data['requester_address']
            received_password = data['password']
            
            # 使用GUI线程安全地显示确认对话框
            if hasattr(self, 'on_pair_request'):
                self.on_pair_request(requester_address, received_password)
            else:
                # 如果没有GUI回调，使用默认的自动处理
                self._auto_handle_pair_request(requester_address, received_password)
                
        except Exception as e:
            print(f"处理配对请求错误: {e}")

    def _auto_handle_pair_request(self, requester_address, received_password):
        """自动处理配对请求（向后兼容）"""
        try:
            # 检查本地是否存储了该节点的配对密码
            expected_password = self.pairing_passwords.get(requester_address)
            
            # 发送配对响应
            response_data = {
                'responder_address': self.address,
                'requester_address': requester_address,
                'result': received_password == expected_password,
                'password': expected_password or ''
            }
            
            response = self.protocol.create_packet(
                MessageType.PAIR_RESPONSE,
                self.address,
                response_data
            )
            
            self.serial_port.write(response)
            
            # 如果密码匹配，自动建立配对关系
            if received_password == expected_password:
                self.paired_nodes.add(requester_address)
                
        except Exception as e:
            print(f"自动处理配对请求错误: {e}")

    def handle_pair_request_with_confirmation(self, requester_address, received_password, accept=True):
        """根据用户确认处理配对请求"""
        try:
            # 检查本地是否存储了该节点的配对密码
            expected_password = self.pairing_passwords.get(requester_address)
            
            # 如果用户接受了请求但密码不匹配，询问用户是否设置新密码
            if accept and received_password != expected_password:
                # 用户接受了使用新密码
                self.pairing_passwords[requester_address] = received_password
                expected_password = received_password
            
            # 发送配对响应
            response_data = {
                'responder_address': self.address,
                'requester_address': requester_address,
                'result': accept and (received_password == expected_password),
                'password': expected_password or ''
            }
            
            response = self.protocol.create_packet(
                MessageType.PAIR_RESPONSE,
                self.address,
                response_data
            )
            
            self.serial_port.write(response)
            
            # 如果接受配对，建立配对关系
            if accept and received_password == expected_password:
                self.paired_nodes.add(requester_address)
                print(f"已接受节点 {requester_address} 的配对请求")
            elif not accept:
                print(f"已拒绝节点 {requester_address} 的配对请求")
                
        except Exception as e:
            print(f"处理配对确认错误: {e}")
    
    def _handle_pair_response(self, packet):
        """处理配对响应"""
        try:
            data = json.loads(packet['payload'].decode('utf-8'))
            responder_address = data['responder_address']
            result = data['result']
            received_password = data['password']
            
            # 检查是否是我们发出的请求
            pending = self.pending_pairs.get(responder_address)
            if not pending:
                return
            
            # 发送配对确认
            confirm_data = {
                'requester_address': self.address,
                'responder_address': responder_address,
                'result': result
            }
            
            confirm = self.protocol.create_packet(
                MessageType.PAIR_CONFIRM,
                self.address,
                confirm_data
            )
            
            self.serial_port.write(confirm)
            
            # 如果配对成功，建立配对关系
            if result:
                self.paired_nodes.add(responder_address)
                self.pairing_passwords[responder_address] = pending['password']
            
            # 清理待处理请求
            del self.pending_pairs[responder_address]
            
        except Exception as e:
            print(f"处理配对响应错误: {e}")
    
    def _handle_pair_confirm(self, packet):
        """处理配对确认"""
        try:
            data = json.loads(packet['payload'].decode('utf-8'))
            requester_address = data['requester_address']
            result = data['result']
            
            # 如果确认成功，建立配对关系
            if result:
                self.paired_nodes.add(requester_address)
                
        except Exception as e:
            print(f"处理配对确认错误: {e}")
    
    def set_node_password(self, node_address, password):
        """设置节点的配对密码"""
        self.pairing_passwords[node_address] = password
    
    def is_node_paired(self, node_address):
        """检查节点是否已配对"""
        return node_address in self.paired_nodes
    
    def get_paired_nodes(self):
        """获取已配对的节点列表"""
        return list(self.paired_nodes)
    
    def unpair_node(self, node_address):
        """取消与节点的配对"""
        if node_address in self.paired_nodes:
            self.paired_nodes.remove(node_address)
        if node_address in self.pairing_passwords:
            del self.pairing_passwords[node_address]
    
    def send_text(self, target_address, text):
        """发送文本消息（检查配对状态）"""
        if not self.is_connected:
            return False
        
        if not self.is_node_paired(target_address):
            print(f"节点 {target_address} 未配对，无法发送消息")
            return False
        
        try:
            packet = self.protocol.create_packet(
                MessageType.TEXT,
                self.address,
                text
            )
            
            self.serial_port.write(packet)
            return True
        except Exception as e:
            print(f"发送文本失败: {e}")
            return False
    
    def send_file(self, target_address, file_path):
        """发送文件（检查配对状态）"""
        if not self.is_connected or not os.path.exists(file_path):
            return False
        
        if not self.is_node_paired(target_address):
            print(f"节点 {target_address} 未配对，无法发送文件")
            return False
        
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # 发送文件开始消息
            start_data = {
                'file_name': file_name,
                'file_size': file_size
            }
            
            packet = self.protocol.create_packet(
                MessageType.FILE_START,
                self.address,
                start_data
            )
            
            self.serial_port.write(packet)
            
            # 发送文件数据
            chunk_size = 1024
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    packet = self.protocol.create_packet(
                        MessageType.FILE_DATA,
                        self.address,
                        chunk
                    )
                    
                    self.serial_port.write(packet)
                    time.sleep(0.01)
            
            # 发送文件结束消息
            packet = self.protocol.create_packet(
                MessageType.FILE_END,
                self.address,
                {'file_name': file_name}
            )
            
            self.serial_port.write(packet)
            return True
            
        except Exception as e:
            print(f"发送文件失败: {e}")
            return False
    
    def _handle_file_start(self, packet):
        """处理文件传输开始"""
        try:
            # 检查发送方是否已配对
            if not self.is_node_paired(packet['address']):
                print(f"收到来自未配对节点 {packet['address']} 的文件传输请求，已忽略")
                return
                
            data = json.loads(packet['payload'].decode('utf-8'))
            file_name = data['file_name']
            file_size = data['file_size']
            
            self.file_receive_buffer[packet['address']] = {
                'file_name': file_name,
                'file_size': file_size,
                'data': b'',
                'received_size': 0
            }
            
            if self.on_file_progress:
                self.on_file_progress(packet['address'], 0, file_size)
            
        except Exception as e:
            print(f"处理文件开始错误: {e}")
    
    def _handle_file_data(self, packet):
        """处理文件数据"""
        if packet['address'] not in self.file_receive_buffer:
            return
        
        file_info = self.file_receive_buffer[packet['address']]
        file_info['data'] += packet['payload']
        file_info['received_size'] += len(packet['payload'])
        
        if self.on_file_progress:
            progress = (file_info['received_size'] / file_info['file_size']) * 100
            self.on_file_progress(
                packet['address'], 
                file_info['received_size'], 
                file_info['file_size']
            )
    
    def _handle_file_end(self, packet):
        """处理文件传输结束"""
        if packet['address'] not in self.file_receive_buffer:
            return
        
        try:
            file_info = self.file_receive_buffer[packet['address']]
            
            # 保存文件
            save_path = f"received_{file_info['file_name']}"
            with open(save_path, 'wb') as f:
                f.write(file_info['data'])
            
            if self.on_file_received:
                self.on_file_received(
                    packet['address'],
                    save_path,
                    file_info['file_name']
                )
            
            if self.on_file_progress:
                self.on_file_progress(packet['address'], file_info['file_size'], file_info['file_size'])
            
            # 清理缓冲区
            del self.file_receive_buffer[packet['address']]
            
        except Exception as e:
            print(f"处理文件结束错误: {e}")
    
    def get_discovered_nodes(self):
        """获取发现的节点列表"""
        # 清理过期的节点（30秒无响应）
        current_time = time.time()
        expired_nodes = []
        
        for addr, node in self.discovered_nodes.items():
            if current_time - node['last_seen'] > 30:
                expired_nodes.append(addr)
        
        for addr in expired_nodes:
            del self.discovered_nodes[addr]
        
        return list(self.discovered_nodes.keys())
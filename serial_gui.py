"""
串口通讯工具GUI界面
使用Tkinter实现
"""

import tkinter as tk
from tkinter import (
    ttk,
    filedialog,
    messagebox,
    scrolledtext,
    simpledialog,
    scrolledtext,
    simpledialog,
)
import threading
import time
import os
from serial_manager import SerialManager


class SerialCommGUI:
    def __init__(self, root):
        """初始化GUI"""
        self.root = root
        self.root.title("串口通信工具")
        self.root.geometry("500x800")
        self.root.minsize(500, 800)

        # 初始化变量
        self.serial_manager = None
        self.current_selected_node = None  # 当前选中的节点

        self.setup_styles()
        self.create_widgets()
        self.periodic_refresh()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use("clam")

        # 配置颜色
        self.root.configure(bg="#f0f0f0")

    def create_widgets(self):
        """创建界面组件"""
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # 配置面板
        self.create_config_panel(main_frame)

        # 节点列表面板
        node_frame = ttk.LabelFrame(main_frame, text="节点列表", padding=8)
        node_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=3)

        # 当前通信节点显示
        self.current_node_label = ttk.Label(
            node_frame, text="当前通信节点: 未选择", font=("Arial", 9, "bold")
        )
        self.current_node_label.pack(fill=tk.X, pady=(0, 3))

        # 节点列表框
        self.node_listbox = tk.Listbox(node_frame, height=5)
        self.node_listbox.pack(fill=tk.BOTH, expand=True, pady=3)
        self.node_listbox.bind("<<ListboxSelect>>", self.on_node_selected)

        # 节点操作按钮
        node_btn_frame = ttk.Frame(node_frame)
        node_btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(
            node_btn_frame, text="🔍 发现节点", command=self.discover_nodes
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(node_btn_frame, text="🔄 刷新节点", command=self.refresh_nodes).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(node_btn_frame, text="🔗 配对节点", command=self.pair_node).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(node_btn_frame, text="❌ 取消配对", command=self.unpair_node).pack(
            side=tk.LEFT, padx=2
        )

        # 配对状态显示
        self.pair_status_label = ttk.Label(node_frame, text="配对状态: 未配对")
        self.pair_status_label.pack(fill=tk.X, pady=2)

        # 消息传输面板
        message_frame = ttk.LabelFrame(main_frame, text="消息传输", padding=8)
        message_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=3)

        # 消息显示区域
        self.message_text = scrolledtext.ScrolledText(message_frame, height=6, width=50)
        self.message_text.pack(fill=tk.BOTH, expand=True, pady=3)

        # 消息输入区域
        msg_input_frame = ttk.Frame(message_frame)
        msg_input_frame.pack(fill=tk.X, pady=2)

        ttk.Label(msg_input_frame, text="消息:").pack(side=tk.LEFT)
        self.message_entry = ttk.Entry(msg_input_frame, width=35)
        self.message_entry.pack(side=tk.LEFT, padx=3)

        # 创建发送消息按钮
        send_btn = ttk.Button(
            msg_input_frame, text="📤 发送", command=self.send_message
        )
        send_btn.pack(side=tk.LEFT, padx=3)

        # 文件传输面板
        file_frame = ttk.LabelFrame(main_frame, text="文件传输", padding=8)
        file_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=3)

        # 文件选择和发送
        file_input_frame = ttk.Frame(file_frame)
        file_input_frame.pack(fill=tk.X, pady=2)

        self.file_path_entry = ttk.Entry(file_input_frame, width=35)
        self.file_path_entry.pack(side=tk.LEFT, padx=3)
        ttk.Button(file_input_frame, text="浏览", command=self.browse_file).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(file_input_frame, text="发送文件", command=self.send_file).pack(
            side=tk.LEFT, padx=2
        )

        # 进度条
        self.file_progress = ttk.Progressbar(file_frame, mode="determinate")
        self.file_progress.pack(fill=tk.X, pady=5)
        self.file_progress_label = ttk.Label(file_frame, text="准备就绪")
        self.file_progress_label.pack()

        # 状态栏
        self.status_label = ttk.Label(main_frame, text="就绪")
        self.status_label.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)

        # 设置权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self.show_about)

    def create_config_panel(self, parent):
        """创建配置面板"""
        config_frame = ttk.LabelFrame(parent, text="串口配置", padding=10)
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 地址配置
        ttk.Label(config_frame, text="节点地址:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        self.address_entry = ttk.Entry(config_frame, width=10)
        self.address_entry.grid(row=0, column=1, padx=5)
        self.address_entry.insert(0, "1")

        # 验证码配置
        ttk.Label(config_frame, text="节点验证码:").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        self.verify_entry = ttk.Entry(config_frame, width=10)
        self.verify_entry.grid(row=0, column=3, padx=5)
        self.verify_entry.insert(0, "1234")

        # 串口选择
        ttk.Label(config_frame, text="串口:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.port_combo = ttk.Combobox(config_frame, width=15, state="readonly")
        self.port_combo.grid(row=1, column=1, padx=5)

        # 刷新串口按钮
        ttk.Button(config_frame, text="刷新", command=self.refresh_ports).grid(
            row=1, column=2, padx=5
        )

        # 连接按钮
        self.connect_btn = ttk.Button(
            config_frame, text="连接", command=self.toggle_connection
        )
        self.connect_btn.grid(row=1, column=3, padx=5)

        # 初始化串口管理器
        self.refresh_ports()

    def refresh_ports(self):
        """刷新可用串口列表"""
        try:
            import serial.tools.list_ports

            ports = serial.tools.list_ports.comports()
            self.port_combo["values"] = [port.device for port in ports]
            if ports:
                self.port_combo.current(0)
        except Exception as e:
            messagebox.showerror("错误", f"获取串口列表失败: {e}")

    def toggle_connection(self):
        """切换串口连接状态"""
        if self.serial_manager and self.serial_manager.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """连接串口"""
        port = self.port_combo.get()
        if not port:
            messagebox.showwarning("警告", "请选择串口")
            return

        try:
            address = int(self.address_entry.get())
            verify_code = str(self.verify_entry.get())  # 保持为字符串

            # 创建串口管理器
            self.serial_manager = SerialManager(port, address, verify_code)

            # 重新绑定回调
            self.serial_manager.on_text_received = self.on_text_received
            self.serial_manager.on_file_received = self.on_file_received
            self.serial_manager.on_node_discovered = self.on_node_discovered
            self.serial_manager.on_pair_request = self.on_pair_request
            self.serial_manager.on_file_progress = self.on_file_progress

            self.connect_btn.config(text="断开")
            self.status_label.config(text="已连接")
            self.refresh_nodes()
            self.start_discovery_timer()  # 启动节点自动发现

        except Exception as e:
            print(e)
            messagebox.showerror("错误", f"连接失败: {e}")

    def disconnect(self):
        """断开串口"""
        if hasattr(self, "_discovery_timer"):
            self.root.after_cancel(self._discovery_timer)

        if self.serial_manager:
            self.serial_manager.disconnect()
            self.serial_manager = None

        self.connect_btn.config(text="连接")
        self.status_label.config(text="已断开")
        self.node_listbox.delete(0, tk.END)

    def start_discovery_timer(self):
        """启动节点发现定时器"""
        if hasattr(self, "_discovery_timer"):
            self.root.after_cancel(self._discovery_timer)

        def discover_nodes():
            if self.serial_manager and self.serial_manager.is_connected:
                self.serial_manager.broadcast_discover()
                self._discovery_timer = self.root.after(
                    2000, discover_nodes
                )  # 每2秒发现一次

        discover_nodes()

    def refresh_nodes(self):
        """刷新节点列表"""
        if not self.serial_manager:
            return

        # 保存当前选中的节点
        selected_node = self.current_selected_node

        self.node_listbox.delete(0, tk.END)
        nodes = self.serial_manager.get_discovered_nodes()

        # 重新填充节点列表
        selected_index = -1
        for index, node in enumerate(nodes):
            if self.serial_manager.is_node_paired(node):
                display_text = f"{node} (已配对)"
            else:
                display_text = str(node)

            self.node_listbox.insert(tk.END, display_text)

            # 如果这是之前选中的节点，记录索引
            if selected_node == node:
                selected_index = index

        # 恢复选中状态
        if selected_index >= 0 and selected_index < self.node_listbox.size():
            self.node_listbox.selection_set(selected_index)
            self.node_listbox.see(selected_index)
            # 确保current_selected_node保持不变
            self.current_selected_node = selected_node
        elif selected_node is not None:
            # 如果之前选中的节点不存在了，清除当前选择
            self.current_selected_node = None
            self.current_node_label.config(text="当前通信节点: 未选择")

        self.update_pair_status()

    def pair_node(self):
        """配对节点"""
        if not self.serial_manager:
            messagebox.showwarning("警告", "请先连接串口")
            return

        selection = self.node_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个节点")
            return

        node_str = self.node_listbox.get(selection[0])
        node_address = int(node_str.split()[0])

        if self.serial_manager.is_node_paired(node_address):
            messagebox.showinfo("信息", "该节点已配对")
            return

        # 弹出密码输入对话框
        password = simpledialog.askstring(
            "配对", f"请输入与节点 {node_address} 的配对密码:"
        )
        if password:
            self.serial_manager.set_node_password(node_address, password)
            if self.serial_manager.request_pair(node_address, password):
                messagebox.showinfo("配对", f"已向节点 {node_address} 发送配对请求")
            else:
                messagebox.showerror("错误", "发送配对请求失败")

    def unpair_node(self):
        """取消配对"""
        if not self.serial_manager:
            messagebox.showwarning("警告", "请先连接串口")
            return

        selection = self.node_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个节点")
            return

        node_str = self.node_listbox.get(selection[0])
        node_address = int(node_str.split()[0])

        if not self.serial_manager.is_node_paired(node_address):
            messagebox.showinfo("信息", "该节点未配对")
            return

        self.serial_manager.unpair_node(node_address)
        messagebox.showinfo("取消配对", f"已取消与节点 {node_address} 的配对")
        self.refresh_nodes()

    def update_pair_status(self):
        """更新配对状态显示"""
        if not self.serial_manager:
            return

        paired_nodes = self.serial_manager.get_paired_nodes()
        if paired_nodes:
            self.pair_status_label.config(
                text=f"配对状态: 已配对 {len(paired_nodes)} 个节点"
            )
        else:
            self.pair_status_label.config(text="配对状态: 未配对")

    def discover_nodes(self):
        """手动发现节点"""
        if not self.serial_manager:
            messagebox.showwarning("警告", "请先连接串口")
            return

        self.serial_manager.broadcast_discover()
        messagebox.showinfo("发现节点", "正在发现网络中的节点...")

    def on_node_selected(self, event):
        """节点选择事件处理"""
        selection = self.node_listbox.curselection()
        if selection:
            node_str = self.node_listbox.get(selection[0])
            node_address = int(node_str.split()[0])
            self.current_selected_node = node_address
            self.current_node_label.config(text=f"当前通信节点: {node_address}")
        else:
            self.current_selected_node = None
            self.current_node_label.config(text="当前通信节点: 未选择")

    def on_node_discovered(self, node_address):
        """节点发现回调"""
        self.root.after(0, self.refresh_nodes)

    def on_pair_request(self, requester_address, received_password):
        """收到配对请求时的回调"""

        def show_confirmation_dialog():
            # 检查是否已有该节点的密码
            existing_password = self.serial_manager.pairing_passwords.get(
                requester_address
            )

            if existing_password:
                # 已有密码，检查是否匹配
                if received_password == existing_password:
                    message = (
                        f"节点 {requester_address} 请求配对\n\n密码匹配，是否接受配对？"
                    )
                else:
                    message = f"节点 {requester_address} 请求配对\n\n密码不匹配：\n收到密码: {received_password}\n期望密码: {existing_password}\n\n是否接受并使用新密码？"
            else:
                # 没有密码，询问是否接受
                message = f"节点 {requester_address} 请求配对\n\n收到密码: {received_password}\n\n是否接受配对？"

            result = messagebox.askyesno("配对请求", message)

            if self.serial_manager:
                self.serial_manager.handle_pair_request_with_confirmation(
                    requester_address, received_password, accept=result
                )

                if result:
                    self.root.after(1000, self.refresh_nodes)  # 延迟刷新节点列表

        # 使用after确保在GUI线程中执行
        self.root.after(0, show_confirmation_dialog)

        def show_confirmation_dialog():
            # 检查是否已有该节点的密码
            existing_password = self.serial_manager.pairing_passwords.get(
                requester_address
            )

            if existing_password:
                # 已有密码，检查是否匹配
                if received_password == existing_password:
                    message = (
                        f"节点 {requester_address} 请求配对\n\n密码匹配，是否接受配对？"
                    )
                else:
                    message = f"节点 {requester_address} 请求配对\n\n密码不匹配：\n收到密码: {received_password}\n期望密码: {existing_password}\n\n是否接受并使用新密码？"
            else:
                # 没有密码，询问是否接受
                message = f"节点 {requester_address} 请求配对\n\n收到密码: {received_password}\n\n是否接受配对？"

            result = messagebox.askyesno("配对请求", message)

            if self.serial_manager:
                self.serial_manager.handle_pair_request_with_confirmation(
                    requester_address, received_password, accept=result
                )

                if result:
                    self.root.after(1000, self.refresh_nodes)  # 延迟刷新节点列表

        # 使用after确保在GUI线程中执行
        self.root.after(0, show_confirmation_dialog)

    def send_message(self):
        """发送消息"""
        if not self.serial_manager:
            messagebox.showwarning("警告", "请先连接串口")
            return

        if self.current_selected_node is None:
            messagebox.showwarning("警告", "请先选择一个节点")
            return

        node_address = self.current_selected_node
        message = self.message_entry.get().strip()
        if not message:
            messagebox.showwarning("警告", "请输入消息内容")
            return

        if self.serial_manager.send_text(node_address, message):
            self.message_text.insert(tk.END, f"我 -> {node_address}: {message}\n")
            self.message_text.see(tk.END)
            self.message_entry.delete(0, tk.END)
        else:
            messagebox.showerror("错误", "发送失败")

    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename()
        if filename:
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, filename)

    def send_file(self):
        """发送文件"""
        if not self.serial_manager:
            messagebox.showwarning("警告", "请先连接串口")
            return

        if self.current_selected_node is None:
            messagebox.showwarning("警告", "请先选择一个节点")
            return

        node_address = self.current_selected_node
        file_path = self.file_path_entry.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("警告", "请选择有效的文件")
            return

        if self.serial_manager.send_file(node_address, file_path):
            filename = os.path.basename(file_path)
            self.message_text.insert(
                tk.END, f"我 -> {node_address}: 发送文件 {filename}\n"
            )
            self.message_text.see(tk.END)
        else:
            messagebox.showerror("错误", "发送文件失败")

    def on_text_received(self, from_address, text):
        """接收到文本消息回调"""
        self.root.after(
            0,
            lambda: self.message_text.insert(tk.END, f"{from_address} -> 我: {text}\n"),
        )
        self.root.after(0, lambda: self.message_text.see(tk.END))

    def on_file_received(self, from_address, file_path, file_name):
        """接收到文件回调"""
        self.root.after(
            0,
            lambda: self.message_text.insert(
                tk.END, f"{from_address} -> 我: 收到文件 {file_name}\n"
            ),
        )
        self.root.after(0, lambda: self.message_text.see(tk.END))
        # 不再显示弹窗，只在消息框记录日志
        self.root.after(
            0,
            lambda: self.message_text.insert(
                tk.END, f"系统: 文件 {file_name} 已保存到 {file_path}\n"
            ),
        )
        self.root.after(0, lambda: self.message_text.see(tk.END))

    def on_file_progress(self, from_address, received_size, total_size):
        """文件传输进度回调"""

        def update_progress():
            if total_size > 0:
                progress = (received_size / total_size) * 100
                self.file_progress["value"] = progress

                if received_size >= total_size:
                    self.file_progress_label.config(text="传输完成")
                    # 2秒后重置进度条
                    self.root.after(
                        2000,
                        lambda: [
                            self.file_progress.config(value=0),
                            self.file_progress_label.config(text="准备就绪"),
                        ],
                    )
                else:
                    self.file_progress_label.config(
                        text=f"接收中: {received_size}/{total_size} 字节 ({progress:.1f}%)"
                    )
            else:
                self.file_progress_label.config(text="准备就绪")

        self.root.after(0, update_progress)

    def show_about(self):
        """显示关于对话框"""
        about_text = """
串口通信工具 v1.0.0

一个基于Python Tkinter的串口通讯工具，
支持节点发现、文本消息和文件传输功能。

作者: wwhai

功能特性:
- 🔌 串口连接
- 🔍 节点发现  
- 💬 文本通讯
- 📁 文件传输
- 🔐 安全验证
- 🎨 图形界面

© 2024 wwhai 版权所有
"""
        messagebox.showinfo("关于", about_text.strip())

    def periodic_refresh(self):
        """定期刷新"""
        if self.serial_manager:
            self.refresh_nodes()
        self.root.after(5000, self.periodic_refresh)


def main():
    """主函数"""
    root = tk.Tk()
    app = SerialCommGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

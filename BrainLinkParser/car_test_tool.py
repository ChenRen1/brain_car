#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小车命令测试工具
允许用户直接通过命令行向小车发送命令进行测试
"""

import os
import sys
import time

# 添加项目根目录到Python路径，确保可以导入config和其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 然后再导入需要的模块
import serial.tools.list_ports
from connector import CarConnector
from command_map import COMMAND_MAP, get_speed_command

class CarTestTool:
    """小车命令测试工具类"""
    
    def __init__(self):
        """初始化测试工具"""
        self.connector = CarConnector()
        self.commands_history = []
        self.current_port = None
    
    def list_available_ports(self):
        """列出所有可用的串口"""
        print("\n可用的串口列表:")
        ports = list(serial.tools.list_ports.comports())
        
        if not ports:
            print("  没有找到可用的串口")
            return []
        
        for i, port in enumerate(ports):
            print(f"  {i+1}. {port.device} - {port.description}")
        
        return [port.device for port in ports]
    
    def connect_to_port(self):
        """连接到指定的串口"""
        ports = self.list_available_ports()
        
        if not ports:
            return False
        
        while True:
            try:
                choice = input("\n请输入要连接的串口序号或直接输入串口名（例如 COM10）: ")
                
                # 尝试将输入解析为序号
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(ports):
                        port = ports[idx]
                    else:
                        print("无效的序号，请重新输入")
                        continue
                except ValueError:
                    # 如果不是序号，就当作串口名直接使用
                    port = choice
                
                print(f"正在连接到 {port}...")
                if self.connector.connect(port):
                    print(f"成功连接到 {port}")
                    self.current_port = port
                    return True
                else:
                    retry = input("连接失败，是否重试？(y/n): ")
                    if retry.lower() != 'y':
                        return False
            except KeyboardInterrupt:
                print("\n操作取消")
                return False
    
    def show_help(self):
        """显示帮助信息"""
        print("\n=== 小车命令测试工具 ===")
        print("可用命令:")
        print("  forward    - 前进")
        print("  backward   - 后退")
        print("  left       - 左转")
        print("  right      - 右转")
        print("  speed_up   - 加速")
        print("  speed_down - 减速")
        print("  speed [值] - 设置速度（范围500-1000），例如: speed 700")
        print("  stop       - 停止所有动作")
        print("  stop_forward  - 停止前进")
        print("  stop_backward - 停止后退")
        print("  stop_left     - 停止左转")
        print("  stop_right    - 停止右转")
        print("  raw [命令]    - 发送原始命令，例如: raw <SPD-600>")
        print("  history   - 显示命令历史")
        print("  reconnect - 重新连接串口")
        print("  help      - 显示此帮助信息")
        print("  exit      - 退出程序")
    
    def execute_command(self, cmd_input):
        """执行用户输入的命令"""
        parts = cmd_input.strip().split()
        if not parts:
            return True
        
        cmd = parts[0].lower()
        
        # 特殊命令处理
        if cmd == 'exit' or cmd == 'quit':
            return False
        
        elif cmd == 'help':
            self.show_help()
            return True
        
        elif cmd == 'history':
            self.show_history()
            return True
        
        elif cmd == 'reconnect':
            self.connector.disconnect()
            self.connect_to_port()
            return True
        
        # 检查连接状态
        if not self.connector.is_connected():
            print("错误: 未连接到小车，请先连接")
            if self.connect_to_port():
                self.execute_command(cmd_input)  # 重新执行命令
            return True
        
        # 发送原始命令
        if cmd == 'raw' and len(parts) > 1:
            raw_cmd = ' '.join(parts[1:])
            self.send_command(raw_cmd)
            self.commands_history.append(f"raw: {raw_cmd}")
            return True
        
        # 速度设置命令
        elif cmd == 'speed' and len(parts) > 1:
            try:
                speed_value = int(parts[1])
                if 500 <= speed_value <= 1000:
                    speed_cmd = get_speed_command(speed_value)
                    if speed_cmd:
                        self.send_command(speed_cmd)
                        self.commands_history.append(f"speed: {speed_value}")
                    else:
                        print(f"错误: 无法生成速度命令，速度值 {speed_value} 可能无效")
                else:
                    print(f"错误: 速度值必须在 500-1000 范围内，当前值: {speed_value}")
            except ValueError:
                print(f"错误: 无效的速度值: {parts[1]}")
            return True
        
        # 标准命令映射
        elif cmd in COMMAND_MAP:
            self.send_command(COMMAND_MAP[cmd])
            self.commands_history.append(cmd)
            return True
        
        # 别名映射
        elif cmd == 'stop':
            self.send_command(COMMAND_MAP.get('stop_all', 'BSTD'))
            self.commands_history.append('stop')
            return True
        
        else:
            print(f"未知命令: {cmd}")
            self.show_help()
            return True
    
    def send_command(self, command):
        """发送命令并显示结果"""
        print(f"发送命令: {command}")
        if self.connector.send_command(command):
            print("命令发送成功")
        else:
            print("命令发送失败")
    
    def show_history(self):
        """显示命令历史"""
        print("\n命令历史:")
        if not self.commands_history:
            print("  暂无历史命令")
        else:
            for i, cmd in enumerate(self.commands_history[-10:], 1):  # 显示最近10条
                print(f"  {i}. {cmd}")
    
    def run(self):
        """运行测试工具"""
        try:
            print("小车命令测试工具")
            print("按 Ctrl+C 随时退出")
            
            # 自动尝试连接
            self.connect_to_port()
            
            # 显示帮助信息
            self.show_help()
            
            # 主循环
            while True:
                try:
                    cmd_input = input("\n请输入命令 (help 获取帮助): ")
                    if not self.execute_command(cmd_input):
                        break
                except KeyboardInterrupt:
                    print("\n操作取消")
        finally:
            # 确保断开连接
            if self.connector.is_connected():
                print("\n正在断开连接...")
                self.connector.disconnect()
                print("已断开连接")
            print("测试工具已退出")

if __name__ == "__main__":
    tool = CarTestTool()
    tool.run()
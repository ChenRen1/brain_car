#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
脑机控制小车主程序
整合脑机数据采集、转换和小车控制命令发送的完整流程
"""

import os
import sys
import time
import logging
import signal
import traceback
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log/brainlink_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MainProgram')

# 导入配置
from config.port import port_config
from config.car_control_config import LOOP_INTERVAL_MS

# 添加全局停止标志
should_stop = False

# 导入核心模块
from controler import Controler
from connector import CarConnector
from converter import BrainDataConverter
from generator import CommandGenerator


def setup_signal_handler(cleanup_func):
    """
    设置信号处理器，用于优雅退出
    """
    def signal_handler(sig, frame):
        global should_stop
        logger.info(f"收到信号 {sig}，开始清理资源...")
        # 设置停止标志，通知所有线程退出
        should_stop = True
        cleanup_func()
        logger.info("程序已退出")
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号


def process_one_pair(brainlink_port, car_port):
    """
    处理一对脑机和小车设备
    
    Args:
        brainlink_port: 脑机设备端口
        car_port: 小车设备端口
        
    Returns:
        tuple: (controler, connector) - 成功连接的控制器和连接器实例
    """
    logger.info(f"开始初始化设备对: 脑机[{brainlink_port}] <-> 小车[{car_port}]")
    
    # 创建控制器并连接脑机
    controler = Controler()
    if not controler.connect(brainlink_port):
        logger.error(f"无法连接脑机设备端口: {brainlink_port}")
        return None, None
    
    # 创建连接器并连接小车
    connector = CarConnector()
    if not connector.connect(car_port):
        logger.error(f"无法连接小车设备端口: {car_port}")
        controler.disconnect()
        return None, None

    logger.info(f"设备对初始化成功: 脑机[{brainlink_port}] <-> 小车[{car_port}]")
    return controler, connector


def run_control_loop(controler, connector, converter, generator, brainlink_port, car_port):
    """
    运行控制循环
    
    Args:
        controler: 脑机控制器实例
        connector: 小车连接器实例
        converter: 数据转换器实例
        generator: 命令生成器实例
        brainlink_port: 脑机端口
        car_port: 小车端口
    """
    global should_stop
    logger.info(f"开始设备对 [{brainlink_port}] <-> [{car_port}] 的控制循环，执行间隔: {LOOP_INTERVAL_MS}ms")
    
    try:
        while not should_stop:
            # 从脑机获取核心数据
            essential_data = controler.get_essential_data()
            
            # 打印essential_data（使用回车符实现原地刷新）
            if essential_data and all(key in essential_data for key in ['attention', 'meditation', 'gyro']):
                try:
                    # 转换数据为小车控制信号
                    control_signal = converter.convert_essential_data(essential_data)
                    
                    # 生成控制命令
                    commands = generator.generate_commands_from_car_control(control_signal)
                    
                    # 使用ANSI转义序列将光标移动到屏幕顶部
                    # 这在大多数终端中都能正常工作
                    print('\033[H\033[J', end='')
                    
                    # 打印三行数据，使用end=''防止自动换行
                    print(f'Essential Data: 注意力={essential_data.get("attention")}, 冥想={essential_data.get("meditation")}, 陀螺仪={essential_data.get("gyro")}', end='')
                    print('\033[K')  # 清除当前行剩余部分
                    print(f'控制信号: 速度={control_signal.get("speed")}, 方向={control_signal.get("direction")}, 前进={control_signal.get("is_forward")}', end='')
                    print('\033[K')  # 清除当前行剩余部分
                    print(f'命令: {commands}', end='')
                    print('\033[K')  # 清除当前行剩余部分
                    
                    # 发送命令到小车
                    for command in commands:
                        if command and not should_stop:  # 检查是否应该停止
                            connector.send_command(command)
                except Exception as e:
                    logger.error(f"数据处理错误: {str(e)}")
                    logger.debug(traceback.format_exc())
            else:
                logger.warning("未获取到有效的脑机数据")
            
            # 等待指定的间隔时间，使用可中断的睡眠
            for _ in range(int((LOOP_INTERVAL_MS / 1000.0) / 0.1)):  # 分成多次短暂睡眠，以便能够响应停止信号
                if should_stop:
                    break
                time.sleep(0.1)
    
    except KeyboardInterrupt:
        logger.info(f"设备对 [{brainlink_port}] <-> [{car_port}] 收到键盘中断信号")
    except Exception as e:
        logger.error(f"控制循环出错: {str(e)}")
        logger.debug(traceback.format_exc())
    finally:
        logger.info(f"设备对 [{brainlink_port}] <-> [{car_port}] 控制循环已退出")


def cleanup_resources(devices):
    """
    清理所有资源
    
    Args:
        devices: 设备列表，每个元素是(controler, connector)元组
    """
    logger.info("开始清理资源...")
    
    for controler, connector in devices:
        if controler:
            controler.disconnect()
        if connector:
            connector.disconnect()
    
    logger.info("资源清理完成")


def main():
    """
    主函数
    """
    global should_stop
    logger.info("==== 脑机控制小车系统启动 ====")
    
    # 获取所有端口配对
    port_pairs = port_config.get_all_pairs()
    
    if not port_pairs:
        logger.error("未配置任何设备端口对")
        return
    
    logger.info(f"检测到 {len(port_pairs)} 对设备配置")
    
    # 初始化设备列表和线程列表
    devices = []
    threads = []
    
    # 设置信号处理器
    setup_signal_handler(lambda: cleanup_resources(devices))
    
    try:
        # 为每对设备创建线程
        for i, pair in enumerate(port_pairs):
            brainlink_port = pair.get('brainlink')
            car_port = pair.get('car')
            
            if not brainlink_port or not car_port:
                logger.error(f"设备对 {i+1} 配置不完整")
                continue
            
            # 处理当前设备对
            controler, connector = process_one_pair(brainlink_port, car_port)
            
            if controler and connector:
                devices.append((controler, connector))
                
                # 创建数据转换器和命令生成器
                converter = BrainDataConverter()
                generator = CommandGenerator()
                
                # 创建并启动线程
                thread_name = f"DevicePair-{brainlink_port}-{car_port}"
                thread = threading.Thread(
                    target=run_control_loop,
                    args=(controler, connector, converter, generator, brainlink_port, car_port),
                    name=thread_name,
                    daemon=False  # 设置为非守护线程，确保能正确清理
                )
                threads.append(thread)
                thread.start()
                logger.info(f"启动线程: {thread_name}")
        
        # 主线程等待所有工作线程
        if threads:
            logger.info(f"所有 {len(threads)} 个设备对线程已启动，主线程等待...")
            # 主线程保持运行，直到收到终止信号
            while not should_stop:
                time.sleep(1)
            
            # 等待所有线程结束，给它们一个合理的时间来清理
            for thread in threads:
                if thread.is_alive():
                    thread.join(timeout=2.0)  # 最多等待2秒
    
    finally:
        # 确保所有资源都被清理
        cleanup_resources(devices)
    
    logger.info("==== 脑机控制小车系统关闭 ====")


if __name__ == "__main__":
    main()
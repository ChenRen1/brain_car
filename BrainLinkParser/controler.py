import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
import serial  # 添加serial模块导入
import traceback  # 添加traceback模块导入
from cushy_serial import CushySerial
from BrainLinkParser import BrainLinkParser
from config.csv_writer import csv_writer
import queue
import threading


# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Controler')

class Controler:
    def __init__(self):
        """
        初始化脑机控制器
        """
        self.serial = None  # 串口连接
        # 正确初始化解析器，使用双下划线方法作为回调
        self.parser = BrainLinkParser(self.__onEEG, self.__onExtendEEG, self.__onGyro, self.__onRR, self.__onRaw)
        self.is_connected = False  # 连接状态
        self.port = None  # 端口信息
        
        # 数据缓存，用于存储最新的数据
        self.last_eeg_data = None
        self.last_extend_eeg_data = None
        self.last_gyro_data = None
        self.last_rr_data = None
        self.last_raw_data = None
        
        # 运行控制
        self.running = False
        
    def connect(self, port):
        """
        连接到脑机设备
        
        Args:
            port: 串口端口名称
            
        Returns:
            bool: 是否连接成功
        """
        try:
            # 关闭已有的连接
            if self.is_connected:
                self.disconnect()
            
            # 保存端口信息
            self.port = port
            
            # 创建串口连接
            self.serial = CushySerial(port, 115200)
            
            # 注册消息处理回调
            @self.serial.on_message()
            def parse(data):
                if self.running:  # 只有在运行状态下才解析数据
                    self.parser.parse(data)
            
            # 设置连接状态
            self.is_connected = True
            self.running = True
            
            logger.info(f"成功连接到脑机设备，端口: {port}")
            return True
            
        except Exception as e:
            logger.error(f"连接脑机设备失败: {str(e)}")
            logger.debug(traceback.format_exc())
            self.disconnect()
            return False

    def disconnect(self):
        """
        断开与脑机设备的连接
        """
        # 停止运行标志
        self.running = False
        
        # 关闭串口
        if self.serial and self.is_connected:
            try:
                self.serial.close()
                logger.debug("串口已关闭")
            except Exception as e:
                logger.error(f"关闭串口时出错: {str(e)}")
        
        # 重置状态
        self.serial = None
        self.is_connected = False
        self.port = None
        
        logger.info("脑机设备连接已断开")

    def __onRaw(self, raw):
        """处理原始数据的私有回调函数"""
        # 缓存原始数据
        self.last_raw_data = raw
        logger.debug(f"接收到原始数据: {raw}")
        return

    def __onEEG(self, data):
        """处理EEG数据的私有回调函数"""
        # 缓存EEG数据
        self.last_eeg_data = data
        logger.debug(f"attention = {data.attention}, meditation = {data.meditation}, \\n                    delta = {data.delta}, theta = {data.theta}, lowAlpha = {data.lowAlpha}, \\n                    highAlpha = {data.highAlpha}, lowBeta = {data.lowBeta}, highBeta = {data.highBeta}, \\n                    lowGamma = {data.lowGamma}, highGamma = {data.highGamma}")
        return

    def __onExtendEEG(self, data):
        """处理扩展EEG数据的私有回调函数"""
        # 缓存扩展EEG数据
        self.last_extend_eeg_data = data
        logger.debug(f"ap = {data.ap}, battery = {data.battery}, version = {data.version}, \\n                    gnaw = {data.gnaw}, temperature = {data.temperature}, heart = {data.heart}")
        return

    def __onGyro(self, x, y, z):
        """处理陀螺仪数据的私有回调函数"""
        # 缓存陀螺仪数据为字典格式
        self.last_gyro_data = {'x': x, 'y': y, 'z': z}
        logger.debug(f"x = {x}, y = {y}, z = {z}")
        return

    def __onRR(self, rr1, rr2, rr3):
        """处理RR数据的私有回调函数"""
        # 缓存RR数据为字典格式
        self.last_rr_data = {'rr1': rr1, 'rr2': rr2, 'rr3': rr3}
        logger.debug(f"rr1 = {rr1}, rr2 = {rr2}, rr3 = {rr3}")
        return

    def get_eeg_data(self):
        """
        获取最新的EEG数据
        :return: EEG数据对象，包含attention, meditation, delta等字段
        """
        return self.last_eeg_data
     
    def get_gyro_data(self):
        """
        获取最新的陀螺仪数据
        :return: 包含x, y, z三个轴数据的字典
        """
        return self.last_gyro_data
            
    def get_essential_data(self):
        """
        获取核心数据：注意力、冥想值和陀螺仪数据
        同时将所有脑机数据写入对应的CSV文件
        :return: 包含attention、meditation和gyro三个字段的字典
        """
        essential_data = {
            'attention': None,
            'meditation': None,
            'gyro': None
        }
        
        # 从EEG数据中获取注意力和冥想值
        if self.last_eeg_data:
            essential_data['attention'] = getattr(self.last_eeg_data, 'attention', None)
            essential_data['meditation'] = getattr(self.last_eeg_data, 'meditation', None)
            # 将EEG数据写入CSV
            csv_writer.write_eeg_data(self.last_eeg_data)
        
        # 将扩展EEG数据写入CSV
        if self.last_extend_eeg_data:
            csv_writer.write_extend_eeg_data(self.last_extend_eeg_data)
        
        # 获取陀螺仪数据
        essential_data['gyro'] = self.last_gyro_data
        # 将陀螺仪数据写入CSV
        if self.last_gyro_data:
            csv_writer.write_gyro_data(
                self.last_gyro_data.get('x'), 
                self.last_gyro_data.get('y'), 
                self.last_gyro_data.get('z')
            )
        
        # 将RR数据写入CSV
        if self.last_rr_data:
            csv_writer.write_rr_data(
                self.last_rr_data.get('rr1'), 
                self.last_rr_data.get('rr2'), 
                self.last_rr_data.get('rr3')
            )
        
        # 将原始数据写入CSV
        if self.last_raw_data:
            csv_writer.write_raw_data(self.last_raw_data)
        
        logger.debug(f"返回核心数据: {essential_data}")
        return essential_data
    
    def __del__(self):
        """析构函数，确保断开连接"""
        self.disconnect()


# 只有在直接运行此文件时才执行以下代码
if __name__ == "__main__":
    controler = Controler()
    if controler.connect('COM7'):
        # 添加等待时间，给设备一些时间发送数据
        print("等待接收数据...")
        time.sleep(2)  # 等待2秒
        # 多次获取数据，增加获取到有效数据的机会
        for i in range(3):
            print(f"\n第{i+1}次尝试获取数据:")
            data = controler.get_essential_data()
            print(f"essential_data: {data}")
            # 如果获取到了有效数据，停止尝试
            if any(value is not None for value in data.values()):
                print("已获取到有效数据!")
                break
            time.sleep(1)
        controler.disconnect()
    else:
        print("无法连接到脑机设备")

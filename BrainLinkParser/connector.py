import logging
import traceback  # 添加traceback模块导入
from cushy_serial import CushySerial
from generator import CommandGenerator

# 配置日志记录器
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CarConnector')

class CarConnector:
    """
    简化的小车连接器类
    使用CushySerial模块实现基本的连接、断开和命令发送功能
    """
    def __init__(self):
        """
        初始化小车连接器
        """
        self.serial = None
        self.port = None
        self.baud_rate = 9600
        self.running = False  # 添加运行标志
    
    def connect(self, port):
        """
        连接到小车设备
        
        参数:
            port: 小车设备的串口，如 COM10
            
        返回:
            bool: 连接成功返回 True，失败返回 False
        """
        try:
            # 断开已存在的连接
            if self.serial:
                self.disconnect()
            
            # 使用CushySerial创建连接
            self.serial = CushySerial(port, self.baud_rate)
            self.port = port
            self.running = True  # 设置运行标志
            
            # 初始化小车为停止状态，初始速度为500
            try:
                logger.debug(f"初始化小车为停止状态，初始速度500...")
                generator = CommandGenerator()
                stop_command = generator.generate_stop_command()
                
                if stop_command:
                    # 与disconnect方法保持一致的命令发送格式
                    full_command = stop_command + "\r\n"
                    self.serial.write(full_command.encode('utf-8'))
                    logger.debug(f"已发送停止命令: {stop_command}")
                else:
                    logger.warning("生成的停止命令为空")
            except Exception as init_e:
                logger.error(f"小车初始化失败: {str(init_e)}")
                logger.debug(traceback.format_exc())
            
            logger.debug(f"成功连接到小车，端口: {port}")
            
            return True
        except Exception as e:
            logger.error(f"连接小车失败: {str(e)}")
            logger.debug(traceback.format_exc())  # 添加详细错误跟踪
            self.serial = None
            self.port = None
            self.running = False
            return False
    
    def disconnect(self):
        """
        断开与小车设备的连接
        """
        try:
            if self.serial and self.running:
                # 在断开连接前发送停止命令
                try:
                    logger.info(f"准备发送停止命令给小车...")  # 提高日志级别
                    generator = CommandGenerator()
                    stop_command = generator.generate_stop_command()
                    
                    # 验证停止命令
                    if not stop_command:
                        logger.error("停止命令为空，无法发送")
                    else:
                        # 直接使用serial.write而不是send_command，确保停止命令能发送
                        full_command = stop_command + "\r\n"
                        logger.info(f"发送停止命令: {stop_command}")  # 提高日志级别，让用户能看到
                        self.serial.write(full_command.encode('utf-8'))
                        # 增加延迟时间，确保命令被处理
                        import time
                        time.sleep(0.3)  # 增加延迟从0.1秒到0.3秒
                        logger.info("停止命令已发送并等待处理")
                except Exception as e:
                    logger.error(f"发送停止命令失败: {str(e)}")
                    logger.debug(traceback.format_exc())
                
                # 关闭串口连接
                self.serial.close()
                logger.info(f"已断开小车连接，端口: {self.port}")  # 提高日志级别
        except Exception as e:
            logger.error(f"断开小车连接时出错: {str(e)}")
            logger.debug(traceback.format_exc())
        finally:
            # 在finally块中设置运行标志为False，确保无论如何都会更新状态
            self.running = False
            self.serial = None
            self.port = None
    
    def send_command(self, command):
        """
        发送命令到小车
        
        参数:
            command: 要发送的命令字符串
            
        返回:
            bool: 发送成功返回 True，失败返回 False
        """
        # 检查是否应该运行
        if not self.running:
            logger.warning("连接器未在运行状态，跳过命令发送")
            return False
        
        if not command:
            logger.warning("没有提供要发送的命令")
            return False
        
        if not self.serial:
            logger.warning("未连接到小车，无法发送命令")
            return False
        
        try:
            # 添加回车换行符确保命令被正确接收
            full_command = command + "\r\n"
            # 将字符串编码为字节再发送
            self.serial.write(full_command.encode('utf-8'))
            logger.debug(f"成功发送命令到小车: {command}")  # 修改为debug级别，避免日志过多
            return True
        except Exception as e:
            logger.error(f"发送命令失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return False
    
    def is_connected(self):
        """
        检查连接状态
        
        返回:
            bool: 已连接返回 True，未连接返回 False
        """
        return self.serial is not None and self.running


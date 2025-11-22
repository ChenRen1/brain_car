import csv
import os
import time
import logging

# 为CSVWriter创建独立的logger配置，确保日志只输出到文件
logger = logging.getLogger('CSVWriter')
logger.setLevel(logging.INFO)

# 创建文件处理器
file_handler = logging.FileHandler('log/csv_writer.log')
file_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 移除所有现有的处理器，然后只添加文件处理器
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
logger.addHandler(file_handler)

# 确保logger不传播到父级logger，这样就不会被根logger的处理器（如控制台）捕获
logger.propagate = False


class CSVWriter:
    """
    CSV文件写入器类
    用于将各种数据写入到CSV文件中，每次运行生成新文件（包含时间戳）
    """
    
    def __init__(self, base_dir='data', init_files=False):
        """
        初始化CSV写入器
        
        Args:
            base_dir: CSV文件保存的基础目录
            init_files: 是否在初始化时就创建CSV文件，默认为False
        """
        self.base_dir = base_dir
        # 确保数据目录存在
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            logger.info(f"创建数据目录: {self.base_dir}")
        
        # 生成时间戳用于文件名
        self.timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
        
        # 文件路径映射，包含时间戳
        self.file_paths = {
            'eeg': os.path.join(self.base_dir, f'brainlink_eeg_{self.timestamp}.csv'),
            'extend_eeg': os.path.join(self.base_dir, f'brainlink_extend_eeg_{self.timestamp}.csv'),
            'gyro': os.path.join(self.base_dir, f'brainlink_gyro_{self.timestamp}.csv'),
            'rr': os.path.join(self.base_dir, f'brainlink_rr_{self.timestamp}.csv'),
            'raw': os.path.join(self.base_dir, f'brainlink_raw_{self.timestamp}.csv')
        }
        
        # 根据标志决定是否初始化CSV文件
        if init_files:
            self._init_csv_files()
    
    def _init_csv_files(self):
        """
        初始化所有CSV文件，创建表头
        """
        # EEG数据CSV
        self.write_eeg_header()
        
        # 扩展EEG数据CSV
        self.write_extend_eeg_header()
        
        # 陀螺仪数据CSV
        self.write_gyro_header()
        
        # RR数据CSV
        self.write_rr_header()
        
        # 原始数据CSV
        self.write_raw_header()
    
    def write_eeg_header(self):
        """
        写入EEG数据CSV文件的表头
        """
        headers = ['timestamp', 'attention', 'meditation', 'delta', 'theta', 
                  'lowAlpha', 'highAlpha', 'lowBeta', 'highBeta', 'lowGamma', 'highGamma']
        try:
            with open(self.file_paths['eeg'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"初始化EEG数据CSV文件: {self.file_paths['eeg']}")
        except Exception as e:
            logger.error(f"初始化EEG数据CSV文件失败: {str(e)}")
    
    def write_extend_eeg_header(self):
        """
        写入扩展EEG数据CSV文件的表头
        """
        headers = ['timestamp', 'ap', 'battery', 'version', 'gnaw', 'temperature', 'heart']
        try:
            with open(self.file_paths['extend_eeg'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"初始化扩展EEG数据CSV文件: {self.file_paths['extend_eeg']}")
        except Exception as e:
            logger.error(f"初始化扩展EEG数据CSV文件失败: {str(e)}")
    
    def write_gyro_header(self):
        """
        写入陀螺仪数据CSV文件的表头
        """
        headers = ['timestamp', 'x', 'y', 'z']
        try:
            with open(self.file_paths['gyro'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"初始化陀螺仪数据CSV文件: {self.file_paths['gyro']}")
        except Exception as e:
            logger.error(f"初始化陀螺仪数据CSV文件失败: {str(e)}")
    
    def write_rr_header(self):
        """
        写入RR数据CSV文件的表头
        """
        headers = ['timestamp', 'rr1', 'rr2', 'rr3']
        try:
            with open(self.file_paths['rr'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"初始化RR数据CSV文件: {self.file_paths['rr']}")
        except Exception as e:
            logger.error(f"初始化RR数据CSV文件失败: {str(e)}")
    
    def write_raw_header(self):
        """
        写入原始数据CSV文件的表头
        """
        headers = ['timestamp', 'raw_data']
        try:
            with open(self.file_paths['raw'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"初始化原始数据CSV文件: {self.file_paths['raw']}")
        except Exception as e:
            logger.error(f"初始化原始数据CSV文件失败: {str(e)}")
    
    def write_eeg_data(self, data):
        """
        写入EEG数据到CSV文件
        
        Args:
            data: EEG数据对象，包含attention, meditation等属性
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        row = [
            timestamp,
            data.attention,
            data.meditation,
            data.delta,
            data.theta,
            data.lowAlpha,
            data.highAlpha,
            data.lowBeta,
            data.highBeta,
            data.lowGamma,
            data.highGamma
        ]
        try:
            with open(self.file_paths['eeg'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"写入EEG数据失败: {str(e)}")
    
    def write_extend_eeg_data(self, data):
        """
        写入扩展EEG数据到CSV文件
        
        Args:
            data: 扩展EEG数据对象，包含ap, battery等属性
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        row = [
            timestamp,
            data.ap,
            data.battery,
            data.version,
            data.gnaw,
            data.temperature,
            data.heart
        ]
        try:
            with open(self.file_paths['extend_eeg'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"写入扩展EEG数据失败: {str(e)}")
    
    def write_gyro_data(self, x, y, z):
        """
        写入陀螺仪数据到CSV文件
        
        Args:
            x, y, z: 陀螺仪的三个轴的数据
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        row = [timestamp, x, y, z]
        try:
            with open(self.file_paths['gyro'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"写入陀螺仪数据失败: {str(e)}")
    
    def write_rr_data(self, rr1, rr2, rr3):
        """
        写入RR数据到CSV文件
        
        Args:
            rr1, rr2, rr3: RR数据的三个值
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        row = [timestamp, rr1, rr2, rr3]
        try:
            with open(self.file_paths['rr'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"写入RR数据失败: {str(e)}")
    
    def write_raw_data(self, raw):
        """
        写入原始数据到CSV文件
        
        Args:
            raw: 原始数据
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        row = [timestamp, str(raw)]
        try:
            with open(self.file_paths['raw'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            logger.error(f"写入原始数据失败: {str(e)}")
    
    def reset_all_files(self):
        """
        重置所有CSV文件（清空并重新创建表头）
        """
        logger.info("重置所有CSV文件")
        self._init_csv_files()


# 创建默认实例，方便直接导入使用
# 不自动初始化文件，等待显式调用reset_all_files
csv_writer = CSVWriter(init_files=False)
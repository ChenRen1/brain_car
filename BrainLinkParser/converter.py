"""
脑机数据转换器模块
简化版：专注于核心转换功能
"""

import os
import sys
import logging

# 配置日志记录器
logger = logging.getLogger('BrainDataConverter')

# 添加项目根目录到Python路径，以便导入config模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 从config模块导入配置常量
from config.car_control_config import (
    BASE_SPEED,
    MAX_SPEED,
    MEDITATION_THRESHOLD,
    MIN_DIRECTION,
    MAX_DIRECTION,
    CENTER_DIRECTION,
    MAX_ATTENTION_VALUE,
    MAX_MEDITATION_VALUE,
    MAX_GYRO_ANGLE,
    DIRECTION_RANGE_PER_SIDE,
    CENTER_GYRO_ANGLE,
    STEERING_GAIN
)


class BrainDataConverter:
    """
    脑机数据转换器类
    简洁的功能类，输入注意力、冥想值和陀螺仪数据，输出速度和方向控制信号
    """
    
    def __init__(self):
        """
        初始化脑机数据转换器
        """
        # 初始化前一个方向值，用于平滑处理
        self._previous_direction = CENTER_DIRECTION
        # 初始化旧的gyro_y值为None，用于检测前后方向变化
        self._previous_gyro_y = None
        # 初始化最后确定的方向状态为向前
        self._last_direction_state = True
        # 小车状态信息
        self.car_status = {
            'direction': CENTER_DIRECTION,
            'speed': BASE_SPEED,
            'is_forward': True
        }
    
    def calculate_speed(self, attention: float, meditation: float) -> int:
        """
        根据注意力和冥想值计算小车速度
        
        规则：
        - 如果冥想值大于冥想度阈值，则速度为基础速度
        - 否则，注意力值线性映射到速度值
        
        Args:
            attention (float): 注意力值
            meditation (float): 冥想度值
            
        Returns:
            int: 计算后的速度值
        """
        # 确保输入值在有效范围内
        attention = max(0, min(attention, MAX_ATTENTION_VALUE))
        meditation = max(0, min(meditation, MAX_MEDITATION_VALUE))
        
        # 如果冥想值大于阈值，则使用基础速度
        if meditation > MEDITATION_THRESHOLD:
            speed = BASE_SPEED
        else:
            # 否则，根据注意力线性映射速度
            speed_range = MAX_SPEED - BASE_SPEED
            mapped_speed = BASE_SPEED + (attention / MAX_ATTENTION_VALUE) * speed_range
            speed = max(BASE_SPEED, min(int(mapped_speed), MAX_SPEED))
        
        # 更新小车状态中的速度信息
        self.car_status['speed'] = speed
        logger.debug(f"小车速度状态更新: {self.car_status['speed']}")
        
        # 确保速度在有效范围内
        return speed
    
    def calculate_forward_direction(self, gyro_y: float) -> bool:
        """
        根据陀螺仪y值判断前后方向
        
        规则：
        - y值大于0代表向后
        - y值小于0代表向前
        
        Args:
            gyro_y (float): 陀螺仪y轴值
            
        Returns:
            bool: True表示向前，False表示向后
        """
        # 如果gyro_y为None，返回默认向后方向
        if gyro_y is None:
            return False
        
        # 计算当前方向：y小于0表示向前，y大于0表示向后
        current_direction = gyro_y < 10
        
        # 更新小车状态中的方向信息
        self.car_status['is_forward'] = current_direction
        
        return current_direction
    
    def calculate_direction(self, gyro_z: float) -> int:
        """
        根据陀螺仪z值计算小车转向
        
        规则：
        - z值为正代表向左歪头，z值越大，向左倾斜角度越大
        - z值为负代表向右歪头，z值越大（绝对值越小），向右倾斜角度越大
        - 特别处理：当z值从0跳变到-75时，视为向右歪头的起始动作
        - z值接近0代表头部正位
        - 增加平滑逻辑：如果方向变化小于总变化幅度的1%，则保持前值
        
        Args:
            gyro_z (float): 陀螺仪z轴值
            
        Returns:
            int: 计算后的转向值
        """
        # 确保gyro_z在有效范围内
        gyro_z = max(-90, min(gyro_z, 90))
        
        if gyro_z > 0:  # 向左歪头
            # 正值映射：z值越大，转向值越小（越左）
            # 从0到90映射到CENTER_DIRECTION到MIN_DIRECTION
            # 使用STEERING_GAIN放大转向映射
            left_ratio = (gyro_z / 90) * STEERING_GAIN
            direction = CENTER_DIRECTION - (left_ratio * DIRECTION_RANGE_PER_SIDE)
        elif gyro_z < 0:  # 向右歪头
            # 负值映射：特别处理从0跳变到-75的情况
            # 重新映射：将z值范围从-90到0调整为-75到0作为主要区间
            # 当z值为-75时，视为向右歪头的起始动作，对应较小的转向角度
            # 当z值接近0时，视为较大的向右歪头角度
            # 使用STEERING_GAIN放大转向映射
            # 首先将z值从-75到0的范围映射到0到1的比例
            if gyro_z < -75:
                # 对于小于-75的值，限制在-75
                normalized_z = -75
            else:
                normalized_z = gyro_z
            
            # 重新映射：-75→0，0→1
            right_ratio = ((normalized_z + 75) / 75) * STEERING_GAIN
            direction = CENTER_DIRECTION + (right_ratio * DIRECTION_RANGE_PER_SIDE)
        else:  # z = 0，正位
            direction = CENTER_DIRECTION
        
        # 确保转向值在有效范围内
        direction = max(MIN_DIRECTION, min(int(direction), MAX_DIRECTION))
        
        # 计算总变化幅度
        total_range = MAX_DIRECTION - MIN_DIRECTION
        # 计算变化阈值（总变化幅度的1%）
        change_threshold = total_range * 0.01
        
        # 如果当前方向与前一个方向的差异小于阈值，返回0且不更新前值
        if abs(direction - self._previous_direction) < change_threshold:
            return self._previous_direction  # 返回前一个方向值而不是0
        
        # 只有当方向变化足够大时，才更新前一个方向值
        self._previous_direction = direction
        # 更新小车状态中的方向信息
        self.car_status['direction'] = direction
        
        return direction
    
    def convert_essential_data(self, essential_data: dict) -> dict:
        """
        将脑机数据转换为小车控制信号
        
        Args:
            essential_data (dict): 包含attention、meditation和gyro的字典
            
        Returns:
            dict: 包含speed、direction和is_forward的控制信号字典
            None: 如果essential_data不完整或数据格式错误
        """
        try:
            # 检查essential_data是否包含必要的字段
            if not essential_data or 'attention' not in essential_data or 'meditation' not in essential_data or 'gyro' not in essential_data:
                logger.error("essential_data缺少必要字段")
                return None
            
            # 提取数据
            attention = essential_data.get('attention')
            meditation = essential_data.get('meditation')
            gyro = essential_data.get('gyro')
            
            # 检查数据是否有效
            if attention is None or meditation is None or gyro is None:
                logger.warning("essential_data中包含无效数据")
                return None
            
            # 提取陀螺仪的y和z轴数据
            gyro_y = gyro.get('y', 0) if isinstance(gyro, dict) else 0
            gyro_z = gyro.get('z', 0) if isinstance(gyro, dict) else 0
            
            # 计算速度（状态在calculate_speed中更新）
            speed = self.calculate_speed(attention, meditation)
            # 计算方向（状态在calculate_direction中更新）
            direction = self.calculate_direction(gyro_z)
            # 计算前后方向（状态在calculate_forward_direction中更新）
            is_forward = self.calculate_forward_direction(gyro_y)
            
            # 记录完整的状态信息日志
            logger.debug(f"小车完整状态更新: 方向={self.car_status['direction']}, 速度={self.car_status['speed']}, 前进方向={'向前' if self.car_status['is_forward'] else '向后'}")
            
            result = {
                'speed': speed,
                'direction': direction,
                'is_forward': is_forward
            }
            
                
            return result
        except Exception as e:
            logger.error(f"转换数据时出错: {str(e)}")
            # 为保持兼容性，添加返回None
            return None
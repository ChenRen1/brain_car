"""
命令生成器模块
负责将速度与角度值转化为具体的控制命令
"""

import math
import logging
from typing import Dict, List
import command_map

from config.car_control_config import (
    BASE_SPEED
)
# 使用全局日志配置
logger = logging.getLogger(__name__)


class CommandGenerator:
    """
    命令生成器类
    负责将速度和角度值转换为具体的控制命令
    """
    
    def __init__(self):
        """
        初始化命令生成器
        """
        try:
            # 将当前速度初始化为BASE_SPEED，与小车连接时的初始速度保持一致
            self._current_speed = BASE_SPEED
            # 初始化is_forward历史值为None
            self._last_is_forward = None
            # 初始化前一个角度值为None
            self._previous_angle = None
            # 初始化成功时不打印日志，只在失败时打印
        except Exception as e:
            logger.error(f"CommandGenerator初始化失败: {str(e)}")
    
    def generate_speed_commands(self, target_speed: int) -> List[str]:
        """
        根据目标速度和当前速度（私有变量）生成速度控制命令
        使用新的速度控制命令格式<SPD-{speed}>
        
        Args:
            target_speed: 目标速度
            
        Returns:
            List[str]: 生成的速度命令列表
        """
        speed_commands = []
        
        if target_speed == 0:
            # 停止命令
            stop_command = command_map.get_stop_all_command()
            logger.debug(f"生成停止命令: {stop_command}")
            if stop_command:
                speed_commands.append(stop_command)
        else:
            # 确保速度值在有效范围内
            if 500 <= target_speed <= 1000:
                # 只有当目标速度与当前速度不同时才生成命令
                if target_speed != self._current_speed:
                    # 生成新的速度控制命令
                    speed_command = command_map.get_speed_command(target_speed)
                    logger.debug(f"生成速度控制命令: {speed_command}")
                    if speed_command:
                        speed_commands.append(speed_command)
            else:
                logger.warning(f"目标速度 {target_speed} 超出有效范围 [500, 1000]")
        
        # 只在生成了速度命令后才更新当前速度私有变量
        if speed_commands:
            self._current_speed = target_speed
            # 在返回结果前打印所有命令
            print(f"即将发送的速度命令: {speed_commands}")
        
        return speed_commands
    
    def generate_movement_command(self, is_forward: bool) -> str:
        """
        生成前进或后退命令
        
        Args:
            is_forward: True表示生成前进命令，False表示生成后退命令
            
        Returns:
            str: 前进或后退命令，如果无法生成则返回空字符串
        """
        direction = 'forward' if is_forward else 'backward'
        movement_command = self._get_direction_command(direction)
        
        if movement_command:
            logger.debug(f"生成{'前进' if is_forward else '后退'}命令: {movement_command}")
            # 更新last_is_forward历史值
            self._last_is_forward = is_forward
        else:
            logger.warning(f"无法生成{'前进' if is_forward else '后退'}命令")
            movement_command = ""
        
        return movement_command
    
    def generate_direction_command(self, angle: int) -> str:
        """
        根据精确转向角度生成转向命令
        只生成转向命令，不包含前后方向逻辑
        
        Args:
            angle: 精确转向角度
            
        Returns:
            str: 转向命令，确保不会返回None
        """
        # 检查角度是否与前一个角度相同
        if self._previous_angle is not None and angle == self._previous_angle:
            # 如果角度相同，不生成新的转向命令
            logger.debug(f"角度值 {angle} 与前值相同，不生成转向命令")
            return ""
        
        # 生成转向命令
        direction_command = command_map.get_steering_command(angle)
        
        # 确保转向命令非None
        if direction_command is None:
            logger.warning(f"无法生成有效转向命令，角度: {angle}")
            direction_command = ""
        else:
            # 更新前一个角度值
            self._previous_angle = angle
            logger.debug(f"生成转向命令: {direction_command}, 角度: {angle}")
        
        return direction_command
    
    def generate_commands_from_car_control(self, car_control_data: Dict) -> List[str]:
        """
        接收小车控制数据并生成完整的命令列表
        直接处理car_control_data，验证数据格式并生成相应的控制命令
        
        Args:
            car_control_data: 包含speed、direction和is_forward字段的小车控制数据字典
                            
        Returns:
            List[str]: 生成的命令列表
        """
        try:
            # 验证输入数据格式
            required_fields = ['speed', 'direction', 'is_forward']
            for field in required_fields:
                if field not in car_control_data:
                    logger.error(f"缺少必要字段: {field}")
                    return []
            
            logger.debug(f"开始生成命令: {car_control_data}, 当前速度: {self._current_speed}")
            commands_sent = []
            
            # 获取目标速度、方向和前进/后退状态
            target_speed = car_control_data['speed']
            target_direction = car_control_data['direction']
            is_forward = car_control_data['is_forward']
            
            logger.debug(f"状态更新 - 目标速度: {target_speed}, 目标方向: {target_direction}, 前进方向: {is_forward}")
            
            # 生成速度命令
            speed_commands = self.generate_speed_commands(target_speed)
            commands_sent.extend(speed_commands)
            
            # 如果不是停止命令，生成转向命令
            if target_speed != 0:
                # 使用方向值作为角度
                angle = target_direction
                logger.debug(f"当前is_forward值: {is_forward}")
                
                # 检查方向变化，如果方向改变，先发送方向命令
                if self._last_is_forward is not None and self._last_is_forward != is_forward:
                    movement_command = self.generate_movement_command(is_forward)
                    if movement_command and movement_command.strip():
                        commands_sent.append(movement_command)
                # 如果是首次设置方向，发送方向命令
                elif self._last_is_forward is None:
                    movement_command = self.generate_movement_command(is_forward)
                    if movement_command and movement_command.strip():
                        commands_sent.append(movement_command)
                
                # 调用generate_direction_command获取转向命令
                steering_command = self.generate_direction_command(angle=angle)
                # 确保只添加非空且有效的转向命令
                if steering_command and steering_command.strip():
                    commands_sent.append(steering_command)
            
            logger.debug(f"命令生成完成，共生成 {len(commands_sent)} 条命令: {commands_sent}")
            return commands_sent
            
        except Exception as e:
            logger.error(f"从小车控制数据生成命令时出错: {str(e)}")
            return []
    
    def _get_direction_command(self, direction: str) -> str:
        """
        根据方向获取相应的命令
        
        Args:
            direction: 方向字符串 ('forward', 'backward', 'left', 'right')
            
        Returns:
            str: 方向命令
        """
        direction_command_map = {
            'forward': command_map.get_forward_command,
            'backward': command_map.get_backward_command,
            'left': command_map.get_left_command,
            'right': command_map.get_right_command
        }
        
        if direction in direction_command_map:
            return direction_command_map[direction]()
        
        logger.warning(f"未知方向: {direction}")
        return None
    
    def generate_stop_command(self) -> str:
        """
        生成停止命令
        
        Returns:
            str: 停止全部命令
        """
        stop_command = command_map.get_stop_all_command()
        logger.debug(f"生成停止全部命令: {stop_command}")
        # 更新当前速度为0
        self._current_speed = 0
        return stop_command
      



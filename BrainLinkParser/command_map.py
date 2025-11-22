"""
命令映射模块
提供简单的命令映射功能，方便其他模块调用
"""

# 命令映射字典，基于command_config.json的配置
COMMAND_MAP = {
    'forward': '<BUPD>',    # 前进命令
    'backward': '<BDND>',   # 后退命令
    'left': '<BLTD>',       # 左命令
    'right': '<BRTD>',      # 右命令
    'speed_up': 'BUAD',     # 加速命令（注意没有尖括号）
    'speed_down': 'BUMD',   # 减速命令（注意没有尖括号）
    'stop_forward': '<BUPU>',  # 停止前进命令
    'stop_backward': '<BDNU>', # 停止后退命令
    'stop_left': '<BLTU>',     # 停止左转命令
    'stop_right': '<BRTU>',    # 停止右转命令
    'stop_all': 'BSTD',        # 停止全部命令
    'speed': '<SPD-'           # 速度控制命令前缀（完整命令需要添加速度值和>）
}

# 命令描述映射，基于command_config.json的配置
COMMAND_DESCRIPTIONS = {
    'forward': '前进',
    'backward': '后退',
    'left': '左',
    'right': '右',
    'speed_up': '加速',
    'speed_down': '减速',
    'stop_forward': '停止前进',
    'stop_backward': '停止后退',
    'stop_left': '停止左转',
    'stop_right': '停止右转',
    'stop_all': '停止全部',
    'steering': '转向',
    'speed': '速度控制'
}

# 命令参数信息，基于command_config.json的配置
COMMAND_PARAMS = {
    'steering': {
        'has_parameter': True, 
        'min_value': 500, 
        'max_value': 2500, 
        'format': '<SUP-{angle}>',
        'parameter_name': 'angle'
    },
    'speed': {
        'has_parameter': True,
        'min_value': 500,
        'max_value': 1000,
        'format': '<SPD-{speed}>',
        'parameter_name': 'speed'
    }
}

# 便捷函数 - 获取指定命令
def get_command(command_name: str) -> str:
    """
    获取指定名称的命令格式
    
    Args:
        command_name: 命令名称
        
    Returns:
        str: 命令格式字符串，如果命令不存在返回None
    """
    return COMMAND_MAP.get(command_name)

# 便捷函数 - 获取前进命令
def get_forward_command() -> str:
    """
    获取前进命令
    
    Returns:
        str: 前进命令格式
    """
    return COMMAND_MAP.get('forward')

# 便捷函数 - 获取后退命令
def get_backward_command() -> str:
    """
    获取后退命令
    
    Returns:
        str: 后退命令格式
    """
    return COMMAND_MAP.get('backward')

# 便捷函数 - 获取左转命令
def get_left_command() -> str:
    """
    获取左转命令
    
    Returns:
        str: 左转命令格式
    """
    return COMMAND_MAP.get('left')

# 便捷函数 - 获取右转命令
def get_right_command() -> str:
    """
    获取右转命令
    
    Returns:
        str: 右转命令格式
    """
    return COMMAND_MAP.get('right')

# 便捷函数 - 获取加速命令
def get_speed_up_command() -> str:
    """
    获取加速命令
    
    Returns:
        str: 加速命令格式
    """
    return COMMAND_MAP.get('speed_up')

# 便捷函数 - 获取减速命令
def get_speed_down_command() -> str:
    """
    获取减速命令
    
    Returns:
        str: 减速命令格式
    """
    return COMMAND_MAP.get('speed_down')



# 便捷函数 - 获取停止前进命令
def get_stop_forward_command() -> str:
    """
    获取停止前进命令
    
    Returns:
        str: 停止前进命令格式
    """
    return COMMAND_MAP.get('stop_forward')

# 便捷函数 - 获取停止后退命令
def get_stop_backward_command() -> str:
    """
    获取停止后退命令
    
    Returns:
        str: 停止后退命令格式
    """
    return COMMAND_MAP.get('stop_backward')

# 便捷函数 - 获取停止左转命令
def get_stop_left_command() -> str:
    """
    获取停止左转命令
    
    Returns:
        str: 停止左转命令格式
    """
    return COMMAND_MAP.get('stop_left')

# 便捷函数 - 获取停止右转命令
def get_stop_right_command() -> str:
    """
    获取停止右转命令
    
    Returns:
        str: 停止右转命令格式
    """
    return COMMAND_MAP.get('stop_right')

# 便捷函数 - 获取停止全部命令
def get_stop_all_command() -> str:
    """
    获取停止全部命令
    
    Returns:
        str: 停止全部命令格式
    """
    return COMMAND_MAP.get('stop_all')

def get_speed_command(speed: int) -> str:
    """
    获取指定速度的速度控制命令
    
    Args:
        speed: 速度值，必须在500-1000之间
        
    Returns:
        str: 速度控制命令格式，如果速度值超出范围返回None
    """
    speed_info = COMMAND_PARAMS.get('speed')
    if speed_info and speed_info['has_parameter']:
        min_value = speed_info['min_value']
        max_value = speed_info['max_value']
        if min_value <= speed <= max_value:
            # 使用命令格式模板生成完整命令
            return f"<SPD-{speed}>"
    return None

# 便捷函数 - 获取转向命令
def get_steering_command(angle: int) -> str:
    """
    获取转向命令
    
    Args:
        angle: 转向角度 (500-2500)
        
    Returns:
        str: 转向命令格式
    """
    # 验证角度范围
    if angle < 500 or angle > 2500:
        print(f"警告: 转向角度 {angle} 超出有效范围 (500-2500)")
        angle = max(500, min(2500, angle))
    
    return f'<SUP-{angle:d}>'

# 获取所有命令名称
def get_all_commands() -> list:
    """
    获取所有可用命令名称
    
    Returns:
        list: 命令名称列表
    """
    return list(COMMAND_MAP.keys())

# 获取命令描述
def get_command_description(command_name: str) -> str:
    """
    获取命令描述
    
    Args:
        command_name: 命令名称
        
    Returns:
        str: 命令描述
    """
    return COMMAND_DESCRIPTIONS.get(command_name, '未知命令')

# 验证命令是否存在
def is_valid_command(command_name: str) -> bool:
    """
    验证命令是否有效
    
    Args:
        command_name: 命令名称
        
    Returns:
        bool: 命令是否有效
    """
    return command_name in COMMAND_MAP
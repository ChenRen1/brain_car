"""
小车控制配置文件
存储脑机数据转换为小车控制信号所需的常量配置
"""

# 速度配置常量
BASE_SPEED = 500  # 基础速度
MAX_SPEED = 800  # 最大速度
MEDITATION_THRESHOLD = 95  # 冥想度阈值（超过此值小车保持基础速度）

# 转向配置常量
MIN_DIRECTION = 500  # 最小转向值（最左）
MAX_DIRECTION = 2500  # 最大转向值（最右）
CENTER_DIRECTION = 1500  # 居中转向值

# 数据范围限制
MAX_ATTENTION_VALUE = 100  # 注意力最大值
MAX_MEDITATION_VALUE = 100  # 冥想度最大值
MAX_GYRO_ANGLE = 180  # 陀螺仪最大角度

# 转向计算常量
DIRECTION_RANGE_PER_SIDE = 400  # 从中心到最大转向的范围
CENTER_GYRO_ANGLE = 90  # 居中陀螺仪角度
STEERING_GAIN = 2.0  # 转向放大倍数，用于增强歪头动作到转向的映射灵敏度

# 执行间隔配置
LOOP_INTERVAL_MS = 100  # 主循环执行间隔（毫秒）
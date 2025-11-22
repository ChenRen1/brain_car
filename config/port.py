class PortConfig:
    """
    小车端口配置类
    用于管理小车连接的串口配置信息
    支持多对一端口配置，可在初始化时手动配置所有端口
    """
    def __init__(self):
        # 手动配置的端口配对列表，用户可以直接在这里修改
        # 格式: [{"brainlink": "脑机端口", "car": "小车端口"}, ...]
        self.port_pairs = [
            # 第一对设备
            {"brainlink": "COM7", "car": "COM8"},
            # 第二对设备（如果需要）
            # {"brainlink": "COM10", "car": "COM12"},
            # 第三对设备（如果需要）
            # {"brainlink": "COM13", "car": "COM8"},
        ]
    
    def get_port(self, type, index=0):
        """
        获取指定类型和索引的端口
        :param type: 端口类型，"car"或"brainlink"
        :param index: 配对索引，从0开始
        :return: 端口字符串
        :raises ValueError: 如果类型无效或索引超出范围
        """
        if type not in ["car", "brainlink"]:
            raise ValueError("Invalid port type. Use 'car' or 'brainlink'.")
        
        if index < 0 or index >= len(self.port_pairs):
            raise ValueError(f"Index {index} out of range for port pairs")
        
        if type in self.port_pairs[index]:
            return self.port_pairs[index][type]
        
        raise ValueError(f"Port type '{type}' not found in pair {index}")
    
    def get_all_pairs(self):
        """
        获取所有端口配对
        主程序可以通过这个方法读取所有配置的端口对
        :return: 端口配对列表的副本
        """
        return self.port_pairs.copy()
    
    def get_pair_count(self):
        """
        获取配置的端口对数量
        :return: 端口对数量
        """
        return len(self.port_pairs)
    


# 创建默认实例，方便直接导入使用
port_config = PortConfig()

import asyncio
import re
import winreg
import subprocess
import xml.etree.ElementTree as ET
from bleak import BleakScanner


def get_paired_bluetooth_devices_from_registry():
    """
    从Windows注册表获取已配对的蓝牙设备
    返回格式: {MAC地址: 设备名称}
    """
    paired_devices = {}
    
    try:
        # 打开蓝牙设备注册表项
        key_path = r'SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices'
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
        
        # 遍历所有已配对设备的MAC地址
        i = 0
        while True:
            try:
                # 获取MAC地址（注册表项名称）
                mac_address = winreg.EnumKey(key, i)
                i += 1
                
                # 格式化MAC地址为标准格式 (XX:XX:XX:XX:XX:XX)
                formatted_mac = ':'.join([mac_address[j:j+2] for j in range(0, 12, 2)]).upper()
                
                # 尝试获取设备名称
                device_key = winreg.OpenKey(key, mac_address, 0, winreg.KEY_READ)
                try:
                    # 尝试从不同的注册表值获取设备名称
                    name_values = ['Name', 'DeviceName', 'LocalName']
                    device_name = '未知'
                    
                    for name_val in name_values:
                        try:
                            device_name = winreg.QueryValueEx(device_key, name_val)[0]
                            break
                        except WindowsError:
                            continue
                    
                    paired_devices[formatted_mac] = device_name
                finally:
                    device_key.Close()
                    
            except WindowsError:
                break
        
        key.Close()
        
    except WindowsError as e:
        print(f"读取蓝牙注册表时出错: {e}")
    
    return paired_devices


def get_paired_bluetooth_devices_wmi():
    """
    使用WMI获取已配对的蓝牙设备
    返回格式: {MAC地址: 设备名称}
    """
    paired_devices = {}
    
    try:
        # 使用wmic命令获取蓝牙设备信息
        result = subprocess.check_output(
            ['wmic', 'path', 'Win32_PnPEntity', 'where', 'Service="BTHENUM"', 'get', 'Name', '/format:xml'],
            universal_newlines=True
        )
        
        # 解析XML输出
        root = ET.fromstring(result)
        for name_elem in root.findall('.//Name'):
            name = name_elem.text
            if name and '(' in name and ')' in name:
                # 尝试从名称中提取MAC地址
                # 格式通常为: "设备名称 (XX:XX:XX:XX:XX:XX)"
                try:
                    mac_match = re.search(r'\(([0-9A-Fa-f:]+)\)', name)
                    if mac_match:
                        mac_address = mac_match.group(1).upper()
                        # 提取设备名称（去除MAC地址部分）
                        device_name = name.split('(')[0].strip()
                        paired_devices[mac_address] = device_name
                except Exception:
                    pass
    
    except Exception as e:
        print(f"使用WMI获取蓝牙设备时出错: {e}")
    
    return paired_devices


def get_bluetooth_com_ports():
    """
    从Windows注册表中获取蓝牙设备关联的COM端口信息
    返回格式: {设备名称: COM端口号}
    """
    bluetooth_com_ports = {}
    
    # 尝试从多个可能的注册表位置获取蓝牙COM端口信息
    registry_paths = [
        r'HARDWARE\DEVICEMAP\SERIALCOMM',
        r'SYSTEM\CurrentControlSet\Enum\USB',
    ]
    
    for path in registry_paths:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_READ)
            
            # 处理不同路径的逻辑
            if 'SERIALCOMM' in path:
                # SERIALCOMM路径直接枚举值
                i = 0
                while True:
                    try:
                        value_name, port_name, _ = winreg.EnumValue(key, i)
                        i += 1
                        
                        # 检查是否是蓝牙设备的COM端口
                        if 'BTHENUM' in value_name or 'bluetooth' in value_name.lower():
                            device_name = f"Bluetooth Device ({port_name})"
                            if device_name not in bluetooth_com_ports:
                                bluetooth_com_ports[device_name] = port_name
                    except WindowsError:
                        break
            else:
                # 其他路径需要枚举子键
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        i += 1
                        
                        # 尝试打开子键寻找PortName
                        subkey = winreg.OpenKey(key, subkey_name)
                        try:
                            # 递归查找可能包含PortName的路径
                            for subpath in ['Device Parameters', 'Device Parameters\Bluetooth']:
                                try:
                                    param_key = winreg.OpenKey(subkey, subpath)
                                    try:
                                        port_name = winreg.QueryValueEx(param_key, 'PortName')[0]
                                        if port_name.startswith('COM'):
                                            device_name = f"Bluetooth Device ({subkey_name[:15]}...)"
                                            bluetooth_com_ports[device_name] = port_name
                                    except WindowsError:
                                        pass
                                    finally:
                                        param_key.Close()
                                except WindowsError:
                                    pass
                        finally:
                            subkey.Close()
                    except WindowsError:
                        break
            
            key.Close()
        except WindowsError as e:
            # 静默处理单个路径错误，继续尝试其他路径
            continue
    
    # 如果没有找到端口，尝试使用WMI（作为备用方案）
    if not bluetooth_com_ports:
        try:
            import wmi
            c = wmi.WMI()
            for port in c.Win32_SerialPort():
                if 'bluetooth' in port.Name.lower() or 'bth' in port.PNPDeviceID.lower():
                    bluetooth_com_ports[port.Name] = port.DeviceID.split('\\')[-1]
        except ImportError:
            # wmi模块不可用，跳过
            pass
        except Exception:
            # WMI查询失败，跳过
            pass
    
    return bluetooth_com_ports


def get_paired_bluetooth_devices():
    """
    获取所有已配对的蓝牙设备
    结合多种方法以获取最完整的信息
    返回格式: {MAC地址: 设备名称}
    """
    # 首先尝试从注册表获取
    paired_devices = get_paired_bluetooth_devices_from_registry()
    
    # 如果注册表方法获取不到足够的信息，尝试WMI方法
    if not paired_devices:
        paired_devices = get_paired_bluetooth_devices_wmi()
    
    # 如果两种方法都失败，尝试使用powershell命令（最后手段）
    if not paired_devices:
        try:
            # 使用PowerShell获取蓝牙设备信息
            powershell_command = '''
            Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq "OK"} | 
            Select-Object Name, DeviceID | ConvertTo-Json
            '''
            result = subprocess.check_output(
                ['powershell', '-Command', powershell_command],
                universal_newlines=True
            )
            
            # 解析JSON输出
            import json
            devices = json.loads(result)
            for device in devices:
                # 尝试从DeviceID中提取MAC地址
                if 'DeviceID' in device and 'BTHENUM' in device['DeviceID']:
                    # 格式通常为: BTHENUM\DEV_XXXXXXXXXXXXXX\...
                    mac_match = re.search(r'DEV_([0-9A-Fa-f]+)', device['DeviceID'])
                    if mac_match:
                        mac_address_raw = mac_match.group(1)
                        # 格式化MAC地址
                        mac_address = ':'.join([mac_address_raw[j:j+2] for j in range(0, 12, 2)]).upper()
                        paired_devices[mac_address] = device.get('Name', '未知')
        except Exception as e:
            print(f"使用PowerShell获取蓝牙设备时出错: {e}")
    
    return paired_devices


async def scan_paired_bluetooth_devices():
    """
    扫描并显示已配对的蓝牙设备及其关联的COM端口
    """
    print("正在获取已配对的蓝牙设备...")
    
    try:
        # 获取已配对的蓝牙设备
        paired_devices = get_paired_bluetooth_devices()
        
        # 获取蓝牙COM端口信息
        bluetooth_ports = get_bluetooth_com_ports()
        
        if not paired_devices:
            print("未发现已配对的蓝牙设备")
            return
        
        print(f"发现 {len(paired_devices)} 个已配对的蓝牙设备:")
        print("-" * 80)
        
        # 排序设备以便显示
        sorted_devices = sorted(paired_devices.items(), key=lambda x: x[1])
        
        for i, (mac_address, device_name) in enumerate(sorted_devices, 1):
            print(f"设备 {i}:")
            print(f"  名称: {device_name}")
            print(f"  MAC地址: {mac_address}")
            
            # 查找关联的COM端口
            associated_ports = []
            for port_name, port in bluetooth_ports.items():
                # 尝试通过名称匹配
                if device_name.lower() in port_name.lower():
                    associated_ports.append(port)
                # 尝试通过MAC地址匹配
                elif mac_address.replace(':', '') in port_name:
                    associated_ports.append(port)
                # 尝试反向匹配
                elif port_name.lower() in device_name.lower():
                    associated_ports.append(port)
            
            if associated_ports:
                print(f"  关联的COM端口: {', '.join(associated_ports)}")
            else:
                print("  未找到关联的COM端口")
            print("-" * 80)
        
        # 显示所有找到的蓝牙COM端口
        if bluetooth_ports:
            print("\n所有检测到的蓝牙COM端口:")
            for name, port in bluetooth_ports.items():
                print(f"  {port}: {name}")
        else:
            print("\n未检测到任何蓝牙COM端口")
            print("提示: 请确保蓝牙设备已正确配对并安装驱动")
            
    except Exception as e:
        print(f"扫描过程中出错: {e}")
        import traceback
        print("错误详情:")
        traceback.print_exc()


def get_paired_bluetooth_devices_with_ports():
    """
    同步版本的函数，返回配对蓝牙设备及其COM端口信息
    用于被其他模块导入使用
    """
    try:
        # 获取已配对的蓝牙设备
        paired_devices = get_paired_bluetooth_devices()
        
        # 获取蓝牙COM端口信息
        bluetooth_ports = get_bluetooth_com_ports()
        
        result = []
        for mac_address, device_name in paired_devices.items():
            device_info = {
                'name': device_name,
                'address': mac_address,
                'ports': []
            }
            
            # 查找关联的COM端口
            for port_name, port in bluetooth_ports.items():
                if device_name.lower() in port_name.lower():
                    device_info['ports'].append(port)
                elif mac_address.replace(':', '') in port_name:
                    device_info['ports'].append(port)
            
            result.append(device_info)
        
        return result, bluetooth_ports
    except Exception as e:
        print(f"获取蓝牙设备信息时出错: {e}")
        return [], {}


if __name__ == "__main__":
    try:
        asyncio.run(scan_paired_bluetooth_devices())
    except KeyboardInterrupt:
        print("\n操作已取消")
    except Exception as e:
        print(f"运行时出错: {e}")
        import traceback
        traceback.print_exc()
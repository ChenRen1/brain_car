
from cushy_serial import CushySerial
from BrainLinkParser import BrainLinkParser

def onRaw(raw):
    # print("raw = " + str(raw))
    return

def onEEG(data):
    print("attention = " + str(data.attention) +
          " meditation = " + str(data.meditation) +
          " delta = " + str(data.delta) +
          " theta = " + str(data.theta) +
          " lowAlpha = " + str(data.lowAlpha) +
          " highAlpha = " + str(data.highAlpha) +
          " lowBeta = " + str(data.lowBeta) +
          " highBeta = " + str(data.highBeta) +
          " lowGamma = " + str(data.lowGamma) +
          " highGamma = " + str(data.highGamma))
    return

def onExtendEEG(data):
    print("ap = " + str(data.ap) +
          " battery = " + str(data.battery) +
          " version = " + str(data.version) +
          " gnaw = " + str(data.gnaw) +
          " temperature = " + str(data.temperature) +
          " heart = " + str(data.heart))
    return

def onGyro(x, y, z):
    print("x = " + str(x) + " y = " + str(y) + " z = " + str(z))
    return

def onRR(rr1, rr2, rr3):
    print("rr1 = " + str(rr1) + " rr2 = " + str(rr2) + " rr3 = " + str(rr3))
    return

parser = BrainLinkParser(onEEG, onExtendEEG, onGyro, onRR, onRaw)

# Windows系统下通常使用COM端口
serial = CushySerial('COM8', 115200)  # 根据实际连接的COM端口修改
print(serial.baudrate)

@serial.on_message()
def handle_serial_message(msg: bytes):
    parser.parse(msg)
    # print(f"[serial] rec msg: {msg}")
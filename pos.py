import threading
import time
from nokov.nokovsdk import *
import sys
import getopt
from Utility import *

# 全局变量
last_extract_time = 0  # 上一次提取时间
car_positions = {}  # 存储车辆名称与位置
car_x_positions=[0,0,0,0,0] # 线性储存5车辆位置
car_positions_lock = threading.Lock()  # 锁，用于线程安全

# 提取位置的函数
def py_data_func(pFrameOfMocapData, pUserData):
    global last_extract_time, car_positions

    if pFrameOfMocapData is None:
        print("Not get the data frame.\n")
        return

    frameData = pFrameOfMocapData.contents
    current_time = time.time()

    # 每1秒执行一次提取
    if current_time - last_extract_time < 1.0:
        return
    last_extract_time = current_time  # 更新提取时间

    with car_positions_lock:  # 使用锁保证线程安全
        car_positions.clear()

        for iMarkerSet in range(frameData.nMarkerSets):
            markerset = frameData.MocapData[iMarkerSet]
            name = markerset.szName.decode('utf-8')  # 将 b'Car1' 解码为字符串

            # 只处理 Car1 ~ Car4
            if name in ["Car1", "Car2", "Car3", "Car4", "Car5"]:
                if markerset.nMarkers >= 1:
                    marker = markerset.Markers[0]  # 取第一个标记点为车的位置
                    x = marker[0]
                    car_positions[name] = x  # 存储x坐标

                    # 根据车辆名称更新到列表的相应位置
                    if name == "Car1":
                        car_x_positions[0] = x
                    elif name == "Car2":
                        car_x_positions[1] = x
                    elif name == "Car3":
                        car_x_positions[2] = x
                    elif name == "Car4":
                        car_x_positions[3] = x
                    elif name == "Car5":
                        car_x_positions[4] = x
                    

    # 打印提取的位置信息
    # print("== Extracted Car Positions at time %.2f ==" % current_time)
    for car, x in car_positions.items():
        print(f"{car}: x = {x:.2f}")
    # print(car_x_positions)
    print( )
    
    # 在此调用你的闭环控制函数，例如：
    # control_cars(car_positions)

# 控制线程的函数
def control_loop():
    while True:
        time.sleep(1)  # 每秒控制一次
        # with car_positions_lock:
        #     # if car_positions:
        #     #     print("== Control Loop ==")
        #     #     for car, x in car_positions.items():
        #     #         print(f"[Control] {car}: current x = {x:.2f}")
        #     #         # 控制逻辑可写在这里
        #     #         # 例如：
        #     #         # u = pid_control(...)
        #     #         # send_command_to_car(car, u)

# 消息回调函数
def py_msg_func(iLogLevel, szLogMessage):
    szLevel = "None"
    if iLogLevel == 4:
        szLevel = "Debug"
    elif iLogLevel == 3:
        szLevel = "Info"
    elif iLogLevel == 2:
        szLevel = "Warning"
    elif iLogLevel == 1:
        szLevel = "Error"

    print("[%s] %s" % (szLevel, cast(szLogMessage, c_char_p).value))

# 主函数
def main(argv):
    serverIp = '10.1.1.198'

    try:
        opts, args = getopt.getopt(argv, "hs:", ["server="])
    except getopt.GetoptError:
        print('Usage: NokovrSDKClient.py -s <serverIp>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage: NokovrSDKClient.py -s <serverIp>')
            sys.exit()
        elif opt in ("-s", "--server"):
            serverIp = arg

    print('Server IP is %s' % serverIp)
    print("Started the Nokovr_SDK_Client Demo")
    client = PySDKClient()

    ver = client.PyNokovVersion()
    print('NokovrSDK Sample Client 2.4.0.5428 (NokovrSDK ver. %d.%d.%d.%d)' % (ver[0], ver[1], ver[2], ver[3]))

    client.PySetVerbosityLevel(0)
    client.PySetMessageCallback(py_msg_func)
    client.PySetDataCallback(py_data_func, None)

    print("Initializing the SDK Client")
    ret = client.Initialize(bytes(serverIp, encoding="utf8"))

    if ret == 0:
        print("Connected to the Nokovr Succeed")
    else:
        print("Connection Failed: [%d]" % ret)
        exit(0)

    serDes = ServerDescription()
    client.PyGetServerDescription(serDes)

    # Give 5 seconds to initialize forceplate device
    ret = client.PyWaitForForcePlateInit(5000)
    if ret != 0:
        print("ForcePlate Initialization Failed[%d]" % ret)
        exit(0)

    client.PySetForcePlateCallback(py_force_plate_func, None)

    # 启动控制线程
    ctrl_thread = threading.Thread(target=control_loop)
    ctrl_thread.daemon = True  # 程序退出时自动关闭
    ctrl_thread.start()

    # 等待用户按 q 键退出
    while input("Press q to quit\n") != "q":
        pass

if __name__ == "__main__":
    main(sys.argv[1:])

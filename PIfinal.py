import asyncio, json, socket
from contextlib import suppress
from bleak import BleakScanner, BleakClient

# ===== 你的旧常量 =====
PI_NUM = 4
CONTROL_MODE = "udp"           # ★新增: keyboard / manual / auto / udp

PYBRICKS_COMMAND_EVENT_CHAR_UUID = "c5f50002-8280-46da-89f4-6d8051e4aeef"
HUB_NAME = "hub" + str(PI_NUM)

# ===== UDP 相关常量 =====
UDP_PORT = 5005                # ★新增: PC 端 sendto(..., 5005)
MAX_PACKET = 1024

# ===== 算法: wanted_pos() =====
import numpy as np

_comu = np.array([0, 1, 1, 1, 0])

def wanted_pos(xs):
    """
    xs : list[float] 5 辆车的 x 坐标
    返回值 : float    算出的目标速度/角速度 (自行定义)
    """
    ans=0
    num=0
    for i in range(5):
        if (_comu[i]==1):
            if (np.abs(xs[i])<2500):
                ans+=xs[i]
                num+=1
    return ans/num    # 你的原式

# ===== LEGO 指令封装 =====
def velocity_to_command(v, w):
    v = max(-1.0, min(1.0, v))
    w = max(-3.0, min(3.0, w))
    v_cmd = int(v * 500 + 500)
    w_cmd = int(w / 3 * 500 + 500)
    return f"{v_cmd:03d}{w_cmd:03d}"

# ------------------------------------------------------------------ #
#                        主入口 & BLE 逻辑                            #
# ------------------------------------------------------------------ #

async def main():
    main_task = asyncio.current_task()

    def handle_disconnect(_):
        print("Hub was disconnected.")
        if not main_task.done():
            main_task.cancel()

    ready_event = asyncio.Event()

    def handle_rx(_, data: bytearray):
        if data[0] == 0x01:
            payload = data[1:]
            if payload == b"rdy":
                ready_event.set()
            else:
                print("Received:", payload)

    print("搜索 LEGO Hub ...")
    device = await BleakScanner.find_device_by_name(HUB_NAME)
    if device is None:
        print(f"Could not find hub: {HUB_NAME}")
        return

    async with BleakClient(device, handle_disconnect) as client:
        await client.start_notify(PYBRICKS_COMMAND_EVENT_CHAR_UUID,
                                  handle_rx)

        async def send(data: bytes):
            await ready_event.wait()
            ready_event.clear()
            await client.write_gatt_char(
                PYBRICKS_COMMAND_EVENT_CHAR_UUID,
                b"\x06" + data,
                response=True
            )

        print("请在 Hub 上启动程序 ...")

        if CONTROL_MODE == "keyboard":
            await keyboard_control_mode(send)
        elif CONTROL_MODE == "manual":
            await manual_input_mode(send)
        elif CONTROL_MODE == "auto":
            await auto_mode(send)
        elif CONTROL_MODE == "udp":           # ★新增
            await udp_mode(send)
        else:
            print(f"未知 CONTROL_MODE: {CONTROL_MODE}")

# ------------------------------------------------------------------ #
#                       UDP 协程 (新增)                               #
# ------------------------------------------------------------------ #

async def udp_mode(send):
    """
    监听路由器发来的 JSON 数据:
        {"ts": 1720612345.0, "x": [x1,x2,x3,x4,x5]}
    每拿到一包即调用 wanted_pos() 计算速度, 并 BLE 发送
    """
    print(f"UDP mode: listening on 0.0.0.0:{UDP_PORT}")

    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: _UDPProtocol(send),
        local_addr=("0.0.0.0", UDP_PORT)
    )

    try:
        # 协程挂起即可; _UDPProtocol 内部做处理
        await asyncio.Future()
    finally:
        transport.close()

class _UDPProtocol(asyncio.DatagramProtocol):
    def __init__(self, send_cb):
        self.send = send_cb

    def datagram_received(self, data: bytes, addr):
        try:
            msg = json.loads(data.decode())
            xs = msg["x"]       
                                 # 5 个浮点
            tar_pos = wanted_pos(xs)                       # ★算法调用
            w = 0.0          
            kp=0.0005         
            tar_speed=kp*(tar_pos-xs[PI_NUM-1])               # 如需转向 控制，自己改
            cmd = velocity_to_command(tar_speed, w).encode()
            asyncio.create_task(self.send(cmd))
            print(f"<UDP {addr[0]}:{addr[1]}> {xs} → tar_pos={tar_pos:.2f},target_speed={tar_speed:.2f}")
        except Exception as e:
            print("Bad packet:", e, data)

# ------------------------------------------------------------------ #
#           下面三块 keyboard / manual / auto 原样保留                #
# ------------------------------------------------------------------ #
import keyboard

async def keyboard_control_mode(send):
    print("Keyboard control mode activated!  (WASD, ESC 退出)")
    try:
        while True:
            w_pressed = keyboard.is_pressed('w')
            s_pressed = keyboard.is_pressed('s')
            a_pressed = keyboard.is_pressed('a')
            d_pressed = keyboard.is_pressed('d')

            if w_pressed and not s_pressed:
                v = 0.5; forward = True
            elif s_pressed and not w_pressed:
                v = -0.5; forward = False
            else:
                v = 0.0; forward = True

            if a_pressed and not d_pressed:
                w = 1.5 if forward else -1.5
            elif d_pressed and not a_pressed:
                w = -1.5 if forward else 1.5
            else:
                w = 0.0

            await send(velocity_to_command(v, w).encode())
            if keyboard.is_pressed('esc'):
                await send(b"bye000"); break
            await asyncio.sleep(0.1)
    finally:
        await send(b"bye000")

async def manual_input_mode(send):
    print("Manual input mode: 输入 'v w'，exit 退出")
    while True:
        user_input = input(">>> ").strip()
        if user_input.lower() == 'exit':
            break
        try:
            v, w = map(float, user_input.split())
            await send(velocity_to_command(v, w).encode())
        except:
            print("格式应为: 0.5 1.5")
    await send(b"bye000")

async def auto_mode(send):
    print("Auto mode (demo)")
    Kp = 1.0; dt = 0.1
    current_pos = target_pos = 0.0
    try:
        while True:
            error = target_pos - current_pos
            v = max(-0.8, min(0.8, Kp * error))
            await send(velocity_to_command(v, 0.0).encode())
            await asyncio.sleep(dt)
    finally:
        await send(velocity_to_command(0, 0).encode())

# ------------------------------------------------------------------ #

if __name__ == "__main__":
    with suppress(asyncio.CancelledError):
        asyncio.run(main())

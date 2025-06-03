from pybricks.pupdevices import Motor
from pybricks.parameters import Port
from pybricks.tools import wait

from usys import stdin, stdout
from uselect import poll
from umath import atan, pi, fabs

# 初始化
left_motor = Motor(Port.E)
right_motor = Motor(Port.A)
steering_motor = Motor(Port.C)
steering_motor.reset_angle(0)

keyboard = poll()
keyboard.register(stdin)

v = 0
w = 0

d = 0.144 # 轮距，单位m
l = 0.11 # 轴距，单位m
r = 0.03 # 轮半径，单位m
def update_motors():
    if v != 0:
        left_speed = -(v - w * d / 2) / r / pi * 180 # 目标左轮速度
        right_speed = (v + w * d / 2) / r / pi * 180 # 目标右轮速度
        target_angle = atan(l * w / v) / pi * 180 # 目标转向角度
            
        left_motor.run(left_speed)
        right_motor.run(right_speed)
        steering_motor.run_target(800, target_angle, wait=False)
    else:
        left_motor.stop()
        right_motor.stop()
        steering_motor.run_target(800, 0, wait=False)

def limit_w(w, v):
    # max_range = fabs(tan(34 * pi / 180) * v / l)
    max_range = 6.13 * fabs(v)  # 最大角速度范围
    min_range = -max_range
    if w < min_range:
        w = min_range  
    elif w > max_range:
        w = max_range
    return w

while True:
    stdout.buffer.write(b"rdy")
    while not keyboard.poll(0):
        wait(10)

    cmd = stdin.buffer.read(6)
    if cmd == b"bye000":
        break
    try:
        # 指令解析
        v = (int(cmd[0:3]) - 500) / 500 # 单位m/s, 范围 -1到1
        w = (int(cmd[3:6]) - 500) / 500 * 3 # 单位rad/s, 范围 -3到3
        w = limit_w(w, v) # 限制角速度范围, 防撞限位

        update_motors()
        
    except Exception as e:
        left_motor.stop()
        right_motor.stop()
        steering_motor.stop()
        print("Error:", e)


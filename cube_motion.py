#!/usr/bin/python3

import odrive
from odrive.enums import *
from odrive.utils import dump_errors

import time
#import sys
import os

time_cost = {}
def show_time_cost(text, time):
#     print("%s time cost: %.2fs" % (text, time))
    if text in time_cost:
        time_cost[text] += time
    else:
        time_cost[text] = 0
    pass

# 步进电机/电磁铁控制
# 2021-01-17 更新，解决偶尔丢步问题，定时精度正负1us左右
# 加载内核模块产生精确的脉冲
def command(text):
    file_name = '/dev/step_moter0'
    if os.path.exists(file_name) == False:
        print("can not find /dev/step_moter0, try to load kernel module.")
        os.system("sudo insmod cube_robot_kernel_module/step_moter.ko")
        time.sleep(0.5)
        os.system("sudo chmod 666 /dev/step_moter0")
    #
    t0 = time.monotonic()
    splited_text = text.split(';')
    with open(file_name, 'w') as f:
        for x in splited_text:
            f.write(x)
            f.flush()
    show_time_cost("filp" , time.monotonic()-t0)

odrv0 = None
# 0层 1层 2层 3层 4层 5层 6层 7层
up_pos_tab = (0.01,0.133,0.216,0.299,0.382,0.465,0.548,0.820)
flip_safe_offset_2 = 1/94
flip_safe_offset = 10/94
up_pos_max_error = 0.025
route_pos_old = -0.3516 # 初始位置
route_pos_max_error = 0.02
# 寻找升降零点
def move_up_down_and_check_block(offset):
    odrv0.axis1.trap_traj.config.vel_limit = 1 # 设置较低的速度
    input_pos = odrv0.axis1.encoder.pos_estimate + offset
    odrv0.axis1.controller.input_pos = input_pos
    while True:
        time.sleep(0.01)
        # 超过5A电流就停止
        current = abs(odrv0.axis1.motor.current_control.Iq_measured)
        #print(current)
        if current > 10:
            pos = odrv0.axis1.encoder.pos_estimate
            # 回退一点，减小电流
            if offset < 0:
                odrv0.axis1.controller.input_pos = pos + up_pos_max_error
            else:
                odrv0.axis1.controller.input_pos = pos - up_pos_max_error
            # 返回零点
            return True, pos
        # 到达需求位置也停止
        if abs(odrv0.axis1.encoder.pos_estimate - input_pos) < up_pos_max_error:
            return False, input_pos

# 升降控制函数
def move_up_down(new_pos, mode='default'):
    global z_pos_old, z_offset, up_pos_max_error
    new_pos += z_offset
    if new_pos == z_pos_old:
        return
    if mode == 'fast up':
        odrv0.axis1.trap_traj.config.vel_limit = 50
        odrv0.axis1.trap_traj.config.accel_limit = 400
        odrv0.axis1.trap_traj.config.decel_limit = 60
        time_sleep = 0
    elif mode == 'fast down':
        odrv0.axis1.trap_traj.config.vel_limit = 50
        odrv0.axis1.trap_traj.config.accel_limit = 700
        odrv0.axis1.trap_traj.config.decel_limit = 700
        time_sleep = 0
    elif mode == 'slow':
        odrv0.axis1.trap_traj.config.vel_limit = 2
        odrv0.axis1.trap_traj.config.accel_limit = 15
        odrv0.axis1.trap_traj.config.decel_limit = 10
        time_sleep = 0.02
    elif mode == 'default':
        odrv0.axis1.trap_traj.config.vel_limit = 8 #20
        if new_pos > z_pos_old: #上升
            mode == 'default up'
            odrv0.axis1.trap_traj.config.accel_limit = 70 #70
            odrv0.axis1.trap_traj.config.decel_limit = 40 #40
            time_sleep = 0.015
        elif new_pos < z_pos_old: #下降
            mode == 'default down'
            odrv0.axis1.trap_traj.config.accel_limit = 30 #45
            odrv0.axis1.trap_traj.config.decel_limit = 100 #180
            time_sleep = 0.015
    else:
        raise Exception("unknown mode")
            
    z_pos_old = new_pos
    t0 = time.monotonic()
    odrv0.axis1.controller.input_pos = new_pos   
    while abs(odrv0.axis1.encoder.pos_estimate - new_pos) > up_pos_max_error:
        #print(odrv0.axis1.encoder.pos_estimate - new_pos)
        time.sleep(0.01)
        if time.monotonic() - t0 > 2:
            raise Exception("move_up_down timeout")
    time.sleep(time_sleep) # 等待位置稳定下来
    show_time_cost("up/down "+mode , time.monotonic()-t0)
    


# 旋转函数，可转90或者180度
def move_route(offset):
    global route_pos_old, route_pos_max_error
    #odrv0.axis0.trap_traj.config.vel_limit = 3 # 设置较低的速度
    t0 = time.monotonic()
    p90 = route_pos_old + offset
    odrv0.axis0.controller.input_pos = p90 # 尝试旋转
    while True:
        time.sleep(0.005)
        # 超过50A电流就停止
        current = abs(odrv0.axis0.motor.current_control.Iq_measured)
        #print(current)
        if current > 65:
            print("over current, current after 5ms is", current)
            # 回退位置
            odrv0.axis0.requested_state = AXIS_STATE_IDLE
            #dump_errors(odrv0,True)
            odrv0.axis0.trap_traj.config.vel_limit = 8
            time.sleep(0.1)
            odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
            odrv0.axis0.controller.input_pos = route_pos_old
            while abs(odrv0.axis0.encoder.pos_estimate - route_pos_old) > route_pos_max_error:
                time.sleep(0.01)
                if time.monotonic() - t0 > 2:
                    raise Exception("move_route timeout")
            print("retry...")
            odrv0.axis0.trap_traj.config.vel_limit = 50
            time.sleep(0.1)
            move_route(offset)
        # 到达需求位置
        if abs(odrv0.axis0.encoder.pos_estimate - p90) < route_pos_max_error:
            route_pos_old = p90
            time.sleep(0.01)
            show_time_cost("route" , time.monotonic()-t0)
            break
        if time.monotonic() - t0 > 2:
            raise Exception("move_route timeout")
# 上电初始化
def move_init():
    global route_pos_old, route_pos_max_error
    global z_pos_old, z_offset, odrv0
    print("finding an odrive...")
    odrv0 = odrive.find_any()
    print("Bus voltage is " + str(odrv0.vbus_voltage) + "V")
    dump_errors(odrv0,True)
    # 电磁铁释放
    command("2,0")
    # axis0
    odrv0.axis0.requested_state = AXIS_STATE_ENCODER_INDEX_SEARCH
    while odrv0.axis0.current_state != AXIS_STATE_IDLE:
        time.sleep(0.1)

    odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    odrv0.axis0.trap_traj.config.vel_limit = 2
    odrv0.axis0.trap_traj.config.accel_limit = 360 # 500 default
    odrv0.axis0.trap_traj.config.decel_limit = 550
    odrv0.axis0.controller.input_pos = route_pos_old
    while abs(odrv0.axis0.encoder.pos_estimate - route_pos_old) > route_pos_max_error:
        time.sleep(0.1)
    odrv0.axis0.requested_state = AXIS_STATE_IDLE
    odrv0.axis0.trap_traj.config.vel_limit = 50 #### 50

    # axis1
    odrv0.axis1.requested_state = AXIS_STATE_ENCODER_INDEX_SEARCH
    while odrv0.axis1.current_state != AXIS_STATE_IDLE:
        time.sleep(0.1)

    # 寻找机械零点
    odrv0.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    block, z_offset = move_up_down_and_check_block(-2)
    assert block == True
    z_pos_old = z_offset
    print("z_offset:", z_offset)
    odrv0.axis1.requested_state = AXIS_STATE_IDLE
    
def move_servo_on():
    odrv0.axis0.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
    odrv0.axis1.requested_state = AXIS_STATE_CLOSED_LOOP_CONTROL
def move_servo_off():
    odrv0.axis1.requested_state = AXIS_STATE_IDLE
    odrv0.axis0.requested_state = AXIS_STATE_IDLE
    
# 获取魔方六面图像
def move_get_image(step):
    if step == 0:
        move_up_down(up_pos_tab[7]-flip_safe_offset)
        move_up_down(up_pos_tab[7],mode = 'slow')
        command("2,1")
        time.sleep(0.02)
        move_up_down(up_pos_tab[5], mode = 'fast down')
    elif step == 1 or step == 2 or step == 3:
        command("1,-400")
    elif step == 4:
        command("1,-400")
        move_up_down(up_pos_tab[7]-flip_safe_offset_2, mode = 'fast up')
        command("2,0")
        move_up_down(up_pos_tab[0])
        move_route(1)
        move_up_down(up_pos_tab[7]-flip_safe_offset)
        move_up_down(up_pos_tab[7], mode = 'slow')
        command("2,1")
        time.sleep(0.02)
        move_up_down(up_pos_tab[5], mode = 'fast down')
        command("1,-400")
    elif step == 5:
        command("1,800")
    else:
        move_up_down(up_pos_tab[7]-flip_safe_offset_2, mode = 'fast up')
        command("2,0")
        move_up_down(up_pos_tab[0])

# 用于测试硬件
def move_test():
    move_servo_on()
    for i in range(2):
        print("--------------------翻转测试----------------------")
        move_up_down(up_pos_tab[7]-flip_safe_offset)
        move_up_down(up_pos_tab[7], mode = 'slow')
        command("2,1")
        move_up_down(up_pos_tab[5], mode = 'fast down')
        if i%2 == 0:
            command("1,-400") #向前
        else:
            command("1,400")  #向后
        move_up_down(up_pos_tab[7])
        command("2,0")
        move_up_down(up_pos_tab[0])
        
    for i in range(1):
        print("--------------------旋转测试----------------------")
        move_up_down(up_pos_tab[1])
        move_route(2) #正数，逆时针
        #time.sleep(0.01)
        move_up_down(up_pos_tab[2])
        move_route(2)
        #time.sleep(1)
        move_up_down(up_pos_tab[3])
        move_route(1)
        #time.sleep(1)
        move_up_down(up_pos_tab[4])
        move_route(1)
        #time.sleep(1)
        move_up_down(up_pos_tab[5])
        move_route(2)
        #time.sleep(1)
        move_up_down(up_pos_tab[6])
        move_route(2)
        time.sleep(0.2)
        move_up_down(up_pos_tab[4])
        move_route(2)
        #time.sleep(0.01)
        move_up_down(up_pos_tab[2])
        move_route(-2)
        #time.sleep(1)
        move_up_down(up_pos_tab[3])
        move_route(1)
        time.sleep(0.2)
        move_up_down(up_pos_tab[0])
    move_servo_off()

# 解析还原指令，例如3Uw 3Lw' 3Fw' L 3Lw2 3Dw L F B
def decode_cube_str(x):
    direction = None # 1 顺时针 -1 逆时针 2 两圈
    face = None      # U R F D L B
    layer = None     # 1 2 3
    if x[-1] == "'":
        direction = -1
    elif x[-1] == "2":
        direction = 2
    else:
        direction = 1
        
    for item in ('U', 'R', 'F', 'D', 'L', 'B'):
        if item in x:
            face = item
    
    if 'w' in x:
        if x[0] == '2':
            layer = 2
        elif x[0] == '3':
            layer = 3
        else:
            layer = 2
    else:
        layer = 1
    
    return face,layer,direction
    

# 向后翻转，向前翻转，顺时针旋转，逆时针旋转，180度旋转
#face_top/front : (f0, f1, cw, ccw, cw2)
cube_dict = {
    'UR': ('RD', 'LU', 'UB', 'UF', 'UL'),
    'UB': ('BD', 'FU', 'UL', 'UR', 'UF'),
    'UL': ('LD', 'RU', 'UF', 'UB', 'UR'),
    'UF': ('FD', 'BU', 'UR', 'UL', 'UB'),
    'RB': ('BL', 'FR', 'RU', 'RD', 'RF'),
    'RD': ('DL', 'UR', 'RB', 'RF', 'RU'),
    'RF': ('FL', 'BR', 'RD', 'RU', 'RB'),
    'RU': ('UL', 'DR', 'RF', 'RB', 'RD'),
    'FR': ('RB', 'LF', 'FU', 'FD', 'FL'),
    'FD': ('DB', 'UF', 'FR', 'FL', 'FU'),
    'FL': ('LB', 'RF', 'FD', 'FU', 'FR'),
    'FU': ('UB', 'DF', 'FL', 'FR', 'FD'),
    'DR': ('RU', 'LD', 'DF', 'DB', 'DL'),
    'DB': ('BU', 'FD', 'DR', 'DL', 'DF'),
    'DL': ('LU', 'RD', 'DB', 'DF', 'DR'),
    'DF': ('FU', 'BD', 'DL', 'DR', 'DB'),
    'LD': ('DR', 'UL', 'LF', 'LB', 'LU'),
    'LB': ('BR', 'FL', 'LD', 'LU', 'LF'),
    'LU': ('UR', 'DL', 'LB', 'LF', 'LD'),
    'LF': ('FR', 'BL', 'LU', 'LD', 'LB'),
    'BR': ('RF', 'LB', 'BD', 'BU', 'BL'),
    'BD': ('DF', 'UB', 'BL', 'BR', 'BU'),
    'BL': ('LF', 'RB', 'BU', 'BD', 'BR'),
    'BU': ('UF', 'DB', 'BR', 'BL', 'BD')}

def can_route(now, need):
    if (need == 'U' or need == 'D') and (now[0] == 'U' or now[0] == 'D'):
        return True
    if (need == 'L' or need == 'R') and (now[0] == 'L' or now[0] == 'R'):
        return True
    if (need == 'F' or need == 'B') and (now[0] == 'F' or now[0] == 'B'):
        return True
    return False

def move_solution_init():
    global cube_now
    cube_now = "LD" # 初始位置,上方颜色+前方颜色

def move_solution(test):
    global cube_now
    # 上黄下白，前蓝后绿，左橙右红
    # 上下UD 前后FB 左右LR
    flip_type_now = 1 # 两种翻转方式交替进行，后续可以考虑优化一下，计算下那种翻转方式更节约时间
    #test="L' 3Bw2 Lw' 3Dw2 U"
    test = test.strip()
    test = test.split()
    print('steps: %d '%len(test), end='')
    for item in test:
        print('-', end='')
        # 解析魔方指令
        face,layer,direction = decode_cube_str(item)
        # 将期望的面翻转到上方或者下方
        if can_route(cube_now, face):
            #print(item,'need not route')
            pass
        elif can_route(cube_dict[cube_now][flip_type_now], face):
            #print(item,'need route f0')
            cube_now = cube_dict[cube_now][flip_type_now]
            move_up_down(up_pos_tab[7]-flip_safe_offset)
            move_up_down(up_pos_tab[7],mode = 'slow')#移动到翻转区域
            command("2,1")
            time.sleep(0.02)
            move_up_down(up_pos_tab[5], mode = 'fast down')
            if flip_type_now == 0:
                command("1,400") # f0,向后翻转
                flip_type_now = 1
            else:
                command("1,-400") # f1,向前翻转
                flip_type_now = 0
            move_up_down(up_pos_tab[7]-flip_safe_offset_2, mode = 'fast up')
            command("2,0")
            #print(cube_now)
        else:
            #print(item,'need route cw f0')
            temp = cube_dict[cube_now][2]
            move_up_down(up_pos_tab[0])
            move_route(-1) #负数，顺时针
            cube_now = cube_dict[temp][flip_type_now]
            move_up_down(up_pos_tab[7]-flip_safe_offset)
            move_up_down(up_pos_tab[7],mode = 'slow') #移动到翻转区域
            command("2,1")
            time.sleep(0.02)
            move_up_down(up_pos_tab[5], mode = 'fast down')
            if flip_type_now == 0:
                command("1,400") # f0,向后翻转
                flip_type_now = 1
            else:
                command("1,-400") # f1,向前翻转
                flip_type_now = 0
            move_up_down(up_pos_tab[7]-flip_safe_offset_2, mode = 'fast up')
            command("2,0")
            #print(cube_now)
        # 旋转指令中描述的层
        if cube_now[0] == face:
            if layer == 1:
                move_up_down(up_pos_tab[1])
            elif layer == 2:
                move_up_down(up_pos_tab[2])
            elif layer == 3:
                move_up_down(up_pos_tab[3])
            if direction == 1:
                move_route(1)
                cube_now = cube_dict[cube_now][3]
            elif direction == -1:
                move_route(-1)
                cube_now = cube_dict[cube_now][2]
            elif direction == 2:
                move_route(2)
                cube_now = cube_dict[cube_now][4]
        else:
            if layer == 1:
                move_up_down(up_pos_tab[6])
            elif layer == 2:
                move_up_down(up_pos_tab[5])
            elif layer == 3:
                move_up_down(up_pos_tab[4])
            if direction == 1:
                move_route(1)
            elif direction == -1:
                move_route(-1)
            elif direction == 2:
                move_route(-2)
    print('=')

def performace_test():
    test_parten="3Uw 3Lw' 3Fw' L 3Lw2 3Dw L F B 3Rw2 3Uw U 3Lw2 U' Uw 3Rw2 Lw2 3Bw2 3Lw 3Uw2 3Fw2 Lw' 3Bw2 U' F Lw' Bw' L' Dw R D2 Fw2 Uw Bw B' 3Lw' 3Uw2 D 3Rw' U 3Lw' B 3Uw2 3Rw 3Uw2 3Bw2 Dw2 F' 3Lw2 F' D' 3Rw2 3Bw2 U2 D Lw2 F Lw' Fw2 Rw2 U2 B Lw L' 3Dw2 L"
    move_init()
    move_servo_on()
    t0 = time.monotonic()
    move_solution_init()
    print(test_parten)
    move_solution(test_parten)
    test_parten = test_parten.strip()
    test_parten = test_parten.split()
    test_parten.reverse()
    for i in range(0, len(test_parten)):
        direction = test_parten[i][-1]
        if direction == "'":
            test_parten[i] = test_parten[i][0:-1]
        elif direction == "2":
            pass
        else:
            test_parten[i] = test_parten[i] + "'"
    test_parten = ' '.join(test_parten)
    print(test_parten)
    move_solution(test_parten)
    t1 = time.monotonic()
    print("totel time cost: %.2fs" % (t1-t0))
    print(time_cost)
    move_servo_off()

if __name__=="__main__":
    performace_test()
# while True:
#     print("axis1.encoder.pos_estimate = %.3f"%(odrv0.axis1.encoder.pos_estimate-z_offset))
#     time.sleep(0.1)   
# while True:
#     print("axis0.encoder.pos_estimate = " + str(odrv0.axis0.encoder.pos_estimate))
#     time.sleep(0.1)

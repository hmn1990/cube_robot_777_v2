#!/usr/bin/python3
import subprocess
import time
import datetime
import os
import cube_robot_image
import cube_motion

# 机械位置回零
cap = cube_robot_image.init_camera()
cube_motion.move_init()

if cube_robot_image.wait_and_prevew_camera(cap) == 27:
    exit(1)
cube_motion.move_servo_on()
#file_name = "log/"+datetime.datetime.now().isoformat()+".log"
#print("log file is",file_name)

img = [None]*6
cube_motion.move_get_image(0)
cube_robot_image.cap_img(cap,img,0) #U
cube_motion.move_get_image(1)
cube_robot_image.cap_img(cap,img,5) #B
cube_motion.move_get_image(2)
cube_robot_image.cap_img(cap,img,3) #D
cube_motion.move_get_image(3)
cube_robot_image.cap_img(cap,img,2) #F
cube_motion.move_get_image(4)
cube_robot_image.cap_img(cap,img,1) #R
cube_motion.move_get_image(5)
cube_robot_image.cap_img(cap,img,4) #L
cube_motion.move_get_image(6)


cube_str = cube_robot_image.get_cube_string(img)
if cube_str == 'UUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUURRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB':
    print("solved rubik cube")
    cube_motion.move_servo_off()
    exit(0)
    
print(cube_str)
cube_motion.move_solution_init()
process = subprocess.Popen(['python3', 'rubiks-cube-solver.py', '--state', cube_str],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
steps_555_LR_centers_staged = 0
steps_555_FB_centers_staged = 0
steps_555_edges_EOed = 0
steps_555_first_four_edges_staged = 0
steps_555_first_four_edges_paired = 0
steps_555_last_eight_edges_paired = 0
all_steps = []
len_old = 0;
while True:
    line = process.stdout.readline().decode("ascii")
    if not line:
        continue
    line = line.strip()
    print('--------------------')
    print(line)
    if "Solution" in line:
        steps = line.split(":")[-1].strip().split(' ')
        solution_id = line.split(":")[0]
        totel_comment = 0
        index_last = 0
        index_CENTERS_SOLVED = 0
        # 截取最新的部分
        for i in range(len(steps)):
            if 'COMMENT' in steps[i]:
                totel_comment += 1
                if i != len(steps) - 1:
                    index_last = i + 1
            if 'CENTERS_SOLVED' in steps[i]:
                index_CENTERS_SOLVED = i + 1
        if totel_comment == 0:
            print("!!! Find solution:", ' '.join(steps))
            if steps != all_steps:
                print("solution should be:", ' '.join(all_steps))
                raise Exception("read rubiks-cube-NxNxN-solver steps error.")
        else:
            if solution_id != 'Solution':
                if len_old != len(steps):
                    len_old = len(steps) #偶尔会出现操作步骤为0的情况，忽略这种
                    comment = steps[-1]
                    steps = steps[index_last:-1]
                    all_steps += steps
                    to_write = ' '.join(steps)
                    #pipe.write(bytes( to_write + '\n' , encoding='ascii'))
                    #pipe.flush()
                    print("!!! %s: %s"%(solution_id, to_write))
                    cube_motion.move_solution(to_write)
#                     print("done")
#                     break
            else:
                steps = steps[index_CENTERS_SOLVED:-1]
                steps_temp = []
                for step in steps:
                    if 'COMMENT' not in step and 'EDGES_GROUPED' not in step:
                        steps_temp.append(step)
                all_steps += steps_temp
                to_write = ' '.join(steps_temp)
                #pipe.write(bytes( to_write + '\n' , encoding='ascii'))
                #pipe.flush()
                print("!!! %s: %s"%(solution_id, to_write))
                cube_motion.move_solution(to_write)
    if process.poll() is not None:
        break
        
cube_motion.move_servo_off()
exit(0)   


    

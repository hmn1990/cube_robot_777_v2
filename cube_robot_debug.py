#!/usr/bin/python3
import subprocess
import time
import datetime
import os

#file_name = "log/"+datetime.datetime.now().isoformat()+".log"
#print("log file is",file_name)



cube_str = "UULBBUBDBBDBDDLLLDLFULDRUULFRDUDFFFBBRULFLLBBRDURUUDLBRRFRFLURFFUBUDBUFBRRFULRDBDDDRRFBDFLDURRDUFFDRLBLFBFURFURDUBRFDULUFRFRRRFDFBUFFLDDFRBULDFFRBLFLUDDDFLLBLRBBDRRLULFFRLDUBRBRBBLULUULDUDRUBDDFLDLRBDBLBULUFRRRDFFLUBRLRBLURRBLDBRLLLFLUUUBFBRUBDDDBDUURBLUFLDFFRFRLFRFBBFBDUUDDBFLDUFLBBLDFRUUBLDR"
    
print(cube_str)

#process = subprocess.Popen(['python3', 'rubiks-cube-solver.py', '--state', cube_str],
#                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
process = subprocess.Popen(['cat', 'log/log1.txt'],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

all_steps = []
len_old_777 = 0;
len_old_555 = 0;
orbit_555 = 0;
while True:
    line = process.stdout.readline().decode("ascii")
    if not line:
        break
    line = line.strip()
    #print(line)
    if line.startswith("Solution"):
        steps_orig = line.split(":")[-1].strip().split(' ')
        solution_id = line.split(":")[0]
        if solution_id == "Solution":
            if all_steps != steps_orig:
                print("Solution Error !!!")
                print("Solution should be:", ' '.join(steps_orig))
                #raise Exception("read rubiks-cube-NxNxN-solver steps error.")
                break
            else:
                print("Everything ok, exit.")
                print("Totel steps:", len(all_steps))
                break
        elif solution_id.startswith("Solution_777"):
            steps = []
            # 移除CENTERS_SOLVED COMMENT_* EDGES_GROUPED
            for item in steps_orig:
                if len(item) < 7 and len(item) > 0:
                    steps.append(item)
            # 截取新增部分
            len_steps = len(steps)
            steps = steps[len_old_777:]
            len_old_777 = len_steps
            all_steps += steps
            to_write = ' '.join(steps)
            print("%s: %s"%(solution_id, to_write))
        elif solution_id.startswith("Solution_555"):
            steps = []
            if solution_id.endswith('orbit'):
                len_old_555 = 0
                orbit_555 = int(steps_orig[0]) + 2
            else:
                # 移除CENTERS_SOLVED COMMENT_* EDGES_GROUPED
                for item in steps_orig[0:-1]:
                    if len(item) < 7 and len(item) > 0:
                        if 'w' in item:
                            steps.append(str(orbit_555) + item)
                        else:
                            steps.append(item)
                # 截取新增部分
                len_steps = len(steps)
                steps = steps[len_old_555:]
                len_old_555 = len_steps
                all_steps += steps
                to_write = ' '.join(steps)
                print("%s: %s"%(solution_id, to_write))
        elif solution_id.startswith("Solution_333"):
            steps = []
            for item in steps_orig[0:-1]:
                if len(item) < 7 and len(item) > 0:
                    steps.append(item)
                elif len(item) > 7:
                    steps = []
            all_steps += steps
            to_write = ' '.join(steps)
            print("%s: %s"%(solution_id, to_write))

process.wait()
#exit(0)   


    

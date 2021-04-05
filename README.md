# cube_robot_7x7x7

#### 介绍
使用树莓派控制的魔方机器人，可以在平均？？？分钟的时间内完成7阶魔方的还原。
使用C + Python开发，含有结构设计、软件部分，实物照片，演示视频。
算法使用rubiks-cube-NxNxN-solver，可还原任意阶数魔方，在原版基础上略有修改。

#### 系统架构
<pre>
树莓派4 ----- TB6560步进电机驱动器×2 --- 42步进电机×2
         +-- Odrive无刷电机驱动器 ----- C4250 560KV 无刷电机×2
         |                       +-- TLE5012编码器×2
         +-- 电磁铁驱动器（功率三极管）-- 电磁铁×2
         +-- USB摄像头
         +-- USB转mSATA卡 ----------- mSATA固态硬盘
</pre>

#### 演示视频：
七阶魔方（这一版本）

待补充

七阶魔方（第一版）

http://v.youku.com/v_show/id_XNTA3NDcyNjU5Ng==.html?x&sharefrom=android&sharekey=1a05666036d4e04ea54c2c59a5a633d63

三阶魔方

http://v.youku.com/v_show/id_XNDg5NTM2OTg5Mg==.html?x&sharefrom=android&sharekey=72dc6125e1c21ec2b96ba7e84085a9bb3

#### 配置与运行步骤：
1、安装python3-opencv

sudo apt-get install python3-opencv

2、安装ckociemba

cd kociemba/

make

sudo make install

3、安装rubiks-cube-NxNxN-solver（该版本相对于原始版本有修改，添加了边计算边输出中间结果的功能，去除了对python venv的需求）

make init

./rubiks-cube-solver.py --state DBDBDDFBDDLUBDLFRFRBRLLDUFFDUFRBRDFDRUFDFDRDBDBULDBDBDBUFBUFFFULLFLDURRBBRRBRLFUUUDUURBRDUUURFFFLRFLRLDLBUFRLDLDFLLFBDFUFRFFUUUFURDRFULBRFURRBUDDRBDLLRLDLLDLUURFRFBUBURBRUDBDDLRBULBULUBDBBUDRBLFFBLRBURRUFULBRLFDUFDDBULBRLBUFULUDDLLDFRDRDBBFBUBBFLFFRRUFFRLRRDRULLLFRLFULBLLBBBLDFDBRBFDULLULRFDBR

第二个步骤很慢，需要联网下载大量数据，解压后需要占用6.2GB空间。

4、编译内核模块，在此之前请安装好linux内核头文件，如需调整步进电机旋转速度，修改step_moter.py，make table后重新编译内核模块

cd cube_robot_kernel_module

make

5、运行主程序

./cube_robot.py

等待出现预览画面后，放入魔方，按空格键开始还原，ESC退出。

#### 其他：

1、树莓派不建议用TF卡，读取速率很差，会形成瓶颈，可以用USB接固态硬盘。

2、2GB内存的树莓派，可能出现内存不足的情况，修改下swap的设置，把/etc/dphys-swapfile下的CONF_SWAPSIZE改为CONF_SWAPSIZE=2048

3、可以适当超频，方法是修改/boot/config.txt，添加如下内容，重启生效

over_voltage=3

arm_freq=1800








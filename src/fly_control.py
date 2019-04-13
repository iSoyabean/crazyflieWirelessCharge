# -*- coding: utf-8 -*-
"""
这个类负责无人机的调度轮换，通过传入无人机的URI和Status list对充电无人机和飞行的无人机进行轮换调度。

"""

import time
import math
import copy
from fly_attr import FlyPosture
from customcflib.duplicable_hl_commander import DuplicablePositionHlCommander

class FlyControl():

    @staticmethod
    def switch_to_charge(formation_cf, charging_cf, status_list):
        # 获取两个uri的scf
        formation_cf_uri = formation_cf.link_uri
        charging_cf_uri = charging_cf.link_uri
        charging_cf_position = []  # 充电中的无人机位置 注：下文所有注释都用‘charging_cf’表示这一架无人机
        const_charging_cf_position = []
        formation_cf_position = []  # 编队中的无人机位置 注：下文所有注释都用‘formation_cf’表示这一架无人机
        const_formation_cf_position = []
        min_x_distance = 0.15  # 当前无人机和队列中其他x轴上的最小距离
        min_y_distance = 0.15
        min_z_distance = 0.15
        min_xy_distance = math.sqrt(min_x_distance**2 + min_y_distance**2)    # 当前无人机和队伍中其他无人机在xy平面上的最小距离
        current_z_distance = 0
        current_xy_distance = 0
        print('all variable initialize')
        print('inswitch',status_list)
        for j in range(len(status_list)):
            print('at the start of changing')
            print(status_list[j].current_position)
            print(status_list[j].uri)
            print(status_list[j].current_battery)
        # 根据uri获取'charging_cf'的位置
        for sts in status_list:
            if charging_cf_uri==sts.uri:
                charging_cf_position = sts.current_position     #建立引用
                const_charging_cf_position = copy.copy(sts.current_position)    #按值传递

        # 根据uri获取'formation_cf'无人机位置
        for sts in status_list:
            if formation_cf_uri==sts.uri:
                formation_cf_position = sts.current_position
                const_formation_cf_position = copy.copy(sts.current_position)


        # 注册Status list
        DuplicablePositionHlCommander.set_class_status_list(status_list)

        # 初始化formation_hl_commander
        formation_hl_commander = DuplicablePositionHlCommander(formation_cf, formation_cf_position[0],
                                                              formation_cf_position[1], formation_cf_position[2],0.3, formation_cf_position[2],
                                                              controller=DuplicablePositionHlCommander.CONTROLLER_MELLINGER)
        print(formation_cf_uri ,'formation_hl_commander create')
        print(formation_cf_uri ,'formation start changing xy position')
        # 1.1记录formation_cf和队列中任意一架飞机在xy平面方向的距离
        # 扫描所有飞行中x负半轴方向的飞机，如果x轴的距离太近，判断y轴方向的距离
        while current_xy_distance < min_xy_distance:
            for i in range(len(status_list)):
                if(formation_cf_uri != status_list[i].uri
                        and status_list[i].current_posture == FlyPosture.hovering
                        and abs(status_list[i].current_position[0] - formation_cf_position[0]) < min_x_distance):
                    if (status_list[i].current_position[1] - formation_cf_position[1] >0 and
                        status_list[i].current_position[1] - formation_cf_position[1] < min_y_distance):
                        #y轴正方向min_y_distance距离内有无人机，要向负方向飞行一段,实际场景中无人机不能靠的太近
                        formation_hl_commander.go_to(formation_cf_position[0],formation_cf_position[1]-0.1,
                                                     formation_cf_position[2],0.3)
                        time.sleep(1)
                    elif (formation_cf_position[1] - status_list[i].current_position[1] > 0 and
                        formation_cf_position[1] - status_list[i].current_position[1] < min_y_distance):
                        #y轴负方向上有无人机且距离过近，要向y正方向飞行一段
                        formation_hl_commander.go_to(formation_cf_position[0], formation_cf_position[1] + 0.1,
                                                     formation_cf_position[2],0.3)
                        time.sleep(1)

            # xy方向调整完成之后
            # 计算所有无人机和编队无人机之间的最短距离
            current_xy_distance = 999999    #重新赋值一个大数方便判断
            for i in range(len(status_list)):
                if(formation_cf_uri != status_list[i].uri and status_list[i].current_posture == FlyPosture.hovering):
                    #current_xy_distance = 根号（dx*dy)
                    if(math.sqrt((formation_cf_position[0]-status_list[i].current_position[0])**2
                                 +(formation_cf_position[1]-status_list[i].current_position[1])**2) < current_xy_distance):
                        current_xy_distance = math.sqrt((formation_cf_position[0]-status_list[i].current_position[0])**2\
                                 +(formation_cf_position[1]-status_list[i].current_position[1])**2)
        print(formation_cf_uri ,'formation start changing z position')
        # 1.2formation_cf调整z轴,如果z方向有距离无人机太近的无人机，当前无人机向下飞行
        while current_z_distance < min_z_distance:
             for i in range(len(status_list)):
                 if (abs(formation_cf_position[2]-status_list[i].current_position[2]) < min_z_distance
                         and formation_cf_uri != status_list[i].uri
                         and status_list[i].current_posture == FlyPosture.hovering):
                     formation_hl_commander.go_to(formation_cf_position[0], formation_cf_position[1],
                                                  formation_cf_position[2]-0.1,0.3)
                     print('I have go to z-0.1')
                     print(formation_cf_position[2])
                     time.sleep(1)
            # 进行完for循环之后formation_cf与其他无人机不在同一个Z上
             current_z_distance = 999999
             for i in range(len(status_list)):
                if status_list[i].uri != formation_cf_uri and status_list[i].current_posture == FlyPosture.hovering:
                    print(status_list[i].uri,'and',formation_cf_uri,'is comparing')
                    if abs(formation_cf_position[2] - status_list[i].current_position[2]) < current_z_distance:
                        print(formation_cf_position[2],status_list[i].current_position[2],'about to minus each other')
                        for j in range(len(status_list)):
                            print(status_list[j].current_position)
                        current_z_distance = abs(formation_cf_position[2]-status_list[i].current_position[2])
                        print(current_z_distance)
        # z轴调整完毕
        # 在这里悬停，等待charging_cf的调整。先从xy方向飞到充电板正上方，再降落
        # 这里能不能用多线程?


        # 2.1初始化charging_cf控制
        charging_hl_commander = DuplicablePositionHlCommander(charging_cf, charging_cf_position[0],
                                          charging_cf_position[1], charging_cf_position[2],0.3, 0.5,
                                          controller=DuplicablePositionHlCommander.CONTROLLER_MELLINGER)

        print('charging_hl_commander create')
        
        charging_hl_commander.take_off()
        print('already take off')
        time.sleep(1)
        print(charging_cf_position[0],charging_cf_position[1],charging_cf_position[2])
        print('charging_hl_commander create changing z position')
        # 2.2控制charging_cf归队,往上飞
        current_z_distance = 0
        while current_z_distance < min_z_distance:
            for i in range(len(status_list)):
                if status_list[i].uri != charging_cf_uri and status_list[i].current_posture == FlyPosture.hovering:
                    if abs(charging_cf_position[2] - status_list[i].current_position[2]) < min_z_distance:
                        charging_hl_commander.go_to(charging_cf_position[0],
                                                charging_cf_position[1],charging_cf_position[2]+0.1,0.3)
            # 计算charging_cf与集群中无人机在z轴方向上的距离
            current_z_distance = 999999
            for i in range(len(status_list)):
                if status_list[i].uri != charging_cf_uri and status_list[i].current_posture == FlyPosture.hovering:
                    if abs(charging_cf_position[2] - status_list[i].current_position[2]) < current_z_distance:
                        current_z_distance = abs(charging_cf_position[2] - status_list[i].current_position[2])

        print('charging_hl_commander go to formation xy')
        #2.3charging_cf飞到现在formation_cf的xy位置，因为它已经经过了多轮调整
        charging_hl_commander.go_to(formation_cf_position[0],
                                    formation_cf_position[1],charging_cf_position[2])

        #1.3formation_cf降落到充电座上
        formation_hl_commander.go_to(const_charging_cf_position[0], const_charging_cf_position[1], formation_cf_position[2], 0.3)
        #这里其实应该看一下降落的时候会不会碰到东西但是不看也行
        formation_hl_commander.land(0.3)

        #2.4判断min_xy_distance,飞到formation_cf原来的z的高度，再回到xy位置

        # current_xy_distance = 0
        # while current_xy_distance < min_xy_distance:
        #     #记录当前飞机和队列中任意一架飞机在xy平面方向的距离
        #     #扫描所有x负半轴方向的飞机，如果x轴的距离太近，判断y轴方向的距离
        #     for i in range(len(status_list)):
        #         if(charging_cf_uri == status_list[i].uri):
        #             pass
        #         elif (status_list[i].current_position[0] - charging_cf_position[0] >-min_x_distance and
        #                 status_list[i].current_position[0] - charging_cf_position[0] <min_x_distance):
        #             if (status_list[i].current_position[1] - charging_cf_position[1] >0 and
        #                 status_list[i].current_position[1] - charging_cf_position[1] < min_y_distance):
        #                 #y轴正方向min_y_distance距离内有无人机，要向负方向飞行一段,实际场景中无人机不能靠的太近
        #                 charging_hl_commander.go_to(charging_cf_position[0],
        #                                             charging_cf_position[1]-0.1,charging_cf_position[2],0.3)
        #             elif (charging_cf_position[1] - status_list[i].current_position[1] > 0 and
        #                 charging_cf_position[1] - status_list[i].current_position[1] < min_y_distance):
        #                 #y轴负方向上有无人机且距离过近，要向y正方向飞行一段
        #                 charging_hl_commander.go_to(charging_cf_position[0],
        #                                             charging_cf_position[1] + 0.1, charging_cf_position[2], 0.3)
        #
        #     current_xy_distance = 999999    #重新赋值一个大数方便判断
        #     for i in range(len(status_list)):
        #         if(charging_cf_uri != status_list[i].uri):
        #             #current_xy_distance = sqrt（dx**2+dy**2)
        #             if(math.sqrt(abs((charging_cf_position[0]-status_list[i].current_position[0])\
        #                          *(charging_cf_position[1]-status_list[i].current_position[1]))) < current_xy_distance):
        #                 current_xy_distance = math.sqrt(abs((charging_cf_position[0]-status_list[i].current_position[0])**2\
        #                          +(charging_cf_position[1]-status_list[i].current_position[1])**2))
        #end while

        #charging_cf飞到formation_cf原来的高度，然后返回相同的xy位置，
        # 这里也没有进行更多判断，存在危险
        #charging_hl_commander.go_to(charging_cf_position[0],charging_cf_position[1],const_formation_cf_position[2],0.3)
        charging_hl_commander.go_to(const_formation_cf_position[0],const_formation_cf_position[1],const_formation_cf_position[2],0.3)


        #传递sequence















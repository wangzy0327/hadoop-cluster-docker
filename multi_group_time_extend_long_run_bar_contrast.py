import numpy as np
import matplotlib.pyplot as plt
import matplotlib


x2 = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
#auto_scaling = [21.326,55.548,54.235,52.982,55.063,59.871,62.999,85.377,106.564,101.499]

from_0_auto_scaling = [70.757,76.630,78.212,74.223,74.272,73.701,75.170,92.714,101.522,114.410,113.793,124.259,124.203,139.540,142.932]
x3 = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
#long_run = [21.308,44.21,46.562,51.364,52.063,55.871,62.365,85.377,106.564,101.499]

long_run = [43.803,43.993,45.653,50.866,55.572,56.218,58.943,62.632,67.491,72.281,71.123,70.421,73.694,78.451,80.490]

auto_scale_from_0_multi_compute = [65.554,58.649,61.790,65.177,62.811,71.838,73.860,73.961,79.639,81.998,82.563,83.191,102.655,102.915,98.424]
# distribute = [<0,1>,<0,2>,<2,1>,<1,3>,<3,2>,<1,5>,<5,2>,<3,5>,<3,6>,<4,6>,<6,5>,<6,6>,<5,8>,<6,8>,<7,8>]


name_list = ['0 & 1 group','0 & 2 group','0 & 3 group','0 & 4 group','0 & 5 group','0 & 6 group','0 & 7 group','0 & 8 group','0 & 9 group','0 & 10 group']

font1 = {
'family' : 'Times New Roman',
'weight' : 'normal',
'size'   : 28,
}

font2 = {
'family' : 'Times New Roman',
'weight' : 'normal',
'size'   : 20,
}



# 设置中文字体和负号正常显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

label_list = ['1任务','2任务','3任务','4任务','5任务','6任务','7任务','8任务','9任务','10任务','11任务','12任务','13任务','14任务','15任务']    # 横坐标刻度显示值
# num_list1 = [70.757,76.630,78.212,74.223,74.272,73.701,75.170,101.127,119.346,123.429]      # 纵坐标值1
# num_list2 = [43.803,43.993,45.653,50.866,55.572,56.218,58.943,85.883,95.091,94.657]      # 纵坐标值2

num_list1 = [70.757,76.630,78.212,74.223,74.272,73.701,75.170,92.714,101.522,114.410,113.793,124.259,124.203,139.540,142.932]      # 纵坐标值1
num_list2 = [43.803,43.993,45.653,50.866,55.572,56.218,58.943,62.632,67.491,72.281,71.123,70.421,73.694,78.451,80.490]      # 纵坐标值2
num_list3 = [65.554,58.649,61.790,65.177,62.811,71.838,73.860,73.961,79.639,81.998,82.563,83.191,102.655,102.915,98.424]
x = [i *3 for i in range(len(num_list1))]
"""
绘制条形图
left:长条形中点横坐标
height:长条形高度
width:长条形宽度，默认值0.8
label:为后面设置legend准备cm
"""
rects1 = plt.bar(x=x, height=num_list1, width=0.8, alpha=0.8, color='red', label="从0扩容")
rects2 = plt.bar(x=[i + 0.8 for i in x], height=num_list2, width=0.8, color='green', label="无需扩容")
rects3 = plt.bar(x=[i + 0.8*2 for i in x], height=num_list3, width=0.8, color='blue', label="2节点从0扩容")
plt.ylim(0, 180)     # y轴取值范围
plt.ylabel("任务处理时间  单位(秒)")
"""
设置x轴刻度显示值
参数一：中点坐标
参数二：显示值
"""
plt.xticks([index + 0.8 for index in x], label_list)
plt.xlabel("hadoop容器组数量  单位(1)")
plt.title("hadoop扩容——处理任务时间对比")
plt.legend()     # 设置题注
# 编辑文本
for rect in rects1:
    height = rect.get_height()
    plt.text(rect.get_x() + rect.get_width() / 2, height+1, str(round(height,1)), ha="center", va="bottom")
for rect in rects2:
    height = rect.get_height()
    plt.text(rect.get_x() + rect.get_width() / 2, height+1, str(round(height,1)), ha="center", va="bottom")
for rect in rects3:
    height = rect.get_height()
    plt.text(rect.get_x() + rect.get_width() / 2, height+1, str(round(height,1)), ha="center", va="bottom")
plt.show()
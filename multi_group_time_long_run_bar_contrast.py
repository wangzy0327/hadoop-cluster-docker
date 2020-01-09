import numpy as np
import matplotlib.pyplot as plt
import matplotlib

x1 = [1,2,3,4,5,6,7,8,9,10]
#single = [21.314,42.573,63.922,85.241,106.107,127.412,148.722,170.032,191.343,212.658]

single = [51.337,104.294,157.023,207.280,260.002,312.343,364.296,416.161,469.033,522.037]

x2 = [1,2,3,4,5,6,7,8,9,10]
#auto_scaling = [21.326,55.548,54.235,52.982,55.063,59.871,62.999,85.377,106.564,101.499]

auto_scaling = [51.337,58.605,63.374,69.149,78.983,83.725,91.456,131.605,133.803,143.027]
x3 = [1,2,3,4,5,6,7,8,9,10]
#long_run = [21.308,44.21,46.562,51.364,52.063,55.871,62.365,85.377,106.564,101.499]

long_run = [51.337,56.038,60.730,68.932,76.647,81.935,91.079,131.156,135.352,137.517]

name_list = ['1 task','2 task','3 task','4 task','5 task','6 task','7 task','8 task','9 task','10 task']

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

label_list = ['1 task','2 task','3 task','4 task','5 task','6 task','7 task','8 task','9 task','10 task']    # 横坐标刻度显示值
num_list1 = [51.337,58.605,63.374,69.149,78.983,83.725,91.456,131.605,133.803,143.027]      # 纵坐标值1
num_list2 = [51.337,56.038,60.730,68.932,76.647,81.935,91.079,131.156,135.352,137.517]      # 纵坐标值2
x = range(len(num_list1))
"""
绘制条形图
left:长条形中点横坐标
height:长条形高度
width:长条形宽度，默认值0.8
label:为后面设置legend准备
"""
rects1 = plt.bar(x=x, height=num_list1, width=0.4, alpha=0.8, color='red', label="任务扩容")
rects2 = plt.bar(x=[i + 0.4 for i in x], height=num_list2, width=0.4, color='green', label="提前扩容")
plt.ylim(0, 160)     # y轴取值范围
plt.ylabel("任务处理时间  单位(秒)")
"""
设置x轴刻度显示值
参数一：中点坐标
参数二：显示值
"""
plt.xticks([index + 0.2 for index in x], label_list)
plt.xlabel("hadoop任务数量  单位(1)")
plt.title("hadoop任务处理时间对比")
plt.legend()     # 设置题注
# 编辑文本
for rect in rects1:
    height = rect.get_height()
    plt.text(rect.get_x() + rect.get_width() / 2, height+1, str(round(height,1)), ha="center", va="bottom")
for rect in rects2:
    height = rect.get_height()
    plt.text(rect.get_x() + rect.get_width() / 2, height+1, str(round(height,1)), ha="center", va="bottom")
plt.show()
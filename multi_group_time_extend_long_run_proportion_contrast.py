import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体和负号正常显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 将横、纵坐标轴标准化处理，保证饼图是一个正圆，否则为椭圆
plt.axes(aspect='equal')

# data = [43.803/70.757,26.954/70.757]
# data = [43.993/76.630,(76.630-43.993)/76.630]
# data = [45.653/78.212,(78.212-45.653)/78.212]
# data = [50.866/74.223,(74.223-50.866)/74.222]
# data = [56.218/74.272,(74.272-56.218)/74.272]
# data = [58.943/73.701,(73.701-58.943)/73.701]
# data = [85.883/101.127,(101.127-85.883)/101.127]
data = [95.091/119.346,(119.346-95.091)/119.346]
# data = [94.657/123.429,(123.429-94.657)/123.429]

labels = ['任务处理','扩容']

explode = [0,0.1]  # 用于突出显示扩容
colors=['#9999ff','#ff9999'] # 自定义颜色
# colors=['#9999ff','#ff9999','#7777aa','#2442aa','#dd5555'] # 自定义颜色
#auto_scaling = [21.326,55.548,54.235,52.982,55.063,59.871,62.999,85.377,106.564,101.499]

from_0_auto_scaling = [70.757,76.630,78.212,74.223,74.272,73.701,75.170,101.127,119.346,123.429]
#long_run = [21.308,44.21,46.562,51.364,52.063,55.871,62.365,85.377,106.564,101.499]

long_run = [43.803,43.993,45.653,50.866,55.572,56.218,58.943,85.883,95.091,94.657]


# 控制x轴和y轴的范围
plt.xlim(0,4)
plt.ylim(0,4)
 
# 绘制饼图
plt.pie(x = data, # 绘图数据
        explode=explode, # 突出显示大专人群
        labels=labels, # 添加教育水平标签
        colors=colors, # 设置饼图的自定义填充色
        autopct='%.1f%%', # 设置百分比的格式，这里保留一位小数
        pctdistance=0.8,  # 设置百分比标签与圆心的距离
        labeldistance = 1.15, # 设置教育水平标签与圆心的距离
        startangle = 180, # 设置饼图的初始角度
        radius = 1.5, # 设置饼图的半径
        counterclock = False, # 是否逆时针，这里设置为顺时针方向
        wedgeprops = {'linewidth': 1.5, 'edgecolor':'green'},# 设置饼图内外边界的属性值
        textprops = {'fontsize':12, 'color':'k'}, # 设置文本标签的属性值
        center = (1.8,1.8), # 设置饼图的原点
        frame = 1 )# 是否显示饼图的图框，这里设置显示
 
# 删除x轴和y轴的刻度
plt.xticks(())
plt.yticks(())
# 添加图标题
plt.title('多容器组处理任务占比分布')
 
# 显示图形
plt.show()
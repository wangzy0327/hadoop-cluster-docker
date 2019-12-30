import numpy as np
import matplotlib.pyplot as plt

t = np.arange(5,70,7)


# CPU_1 = [0.037, 0.035, 0.038, 0.042, 0.038, 0.037, 0.038, 0.039, 0.040, 0.038]
# CPU_2 = [0.096, 0.038, 0.038, 0.038, 0.038, 0.039, 0.038, 0.038, 0.038, 0.038]
# CPU_3 = [0.147, 0.033, 0.039, 0.04, 0.041, 0.038, 0.039, 0.038, 0.038, 0.038]
# CPU_4 = [0.214, 0.084, 0.037, 0.04, 0.039, 0.038, 0.037, 0.038, 0.038, 0.038]
# CPU_5 = [0.314, 0.149, 0.039, 0.04, 0.039, 0.04, 0.04, 0.038, 0.038, 0.038]
# CPU_6 = [0.376, 0.188, 0.062, 0.037, 0.038, 0.038, 0.038, 0.042, 0.04, 0.038]
# CPU_7 = [0.439, 0.244, 0.141, 0.035, 0.038, 0.038, 0.039, 0.038, 0.038, 0.038]

CPU_1 = [0.04, 0.038, 0.044, 0.042, 0.045, 0.04, 0.042, 0.04, 0.04, 0.04]
CPU_2 = [0.033, 0.064, 2.686, 1.569, 1.759, 6.3, 0.077, 0.094, 0.081, 0.097]
CPU_3 = [0.042, 0.03, 6.022, 6.151, 2.274, 8.678, 1.015, 0.124, 0.136, 0.154]
CPU_4 = [0.028, 0.076, 5.497, 6.746, 7.6, 9.545, 4.736, 0.184, 0.194, 0.176]
CPU_5 = [0.038, 0.052, 5.901, 9.328, 11.862, 7.962, 9.82, 0.343, 0.265, 0.255]
CPU_6 = [0.035, 0.089, 4.47, 7.365, 13.839, 11.099, 10.691, 3.768, 2.016, 0.326]
CPU_7 = [0.124, 6.537, 8.115, 14.497, 13.829, 8.3, 9.388, 1.233, 0.365, 0.35]


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

plt.title('extend processing CPU% Analysis',font1)
l1, = plt.plot(t,CPU_1,color='green',marker="o",label='1 hadoop group')
l2, = plt.plot(t,CPU_2,color='darkorange',marker="o",label='2 hadoop group')
l3, = plt.plot(t,CPU_3,color='yellow',marker="o",label='3 hadoop group')
l4, = plt.plot(t,CPU_4,color='greenyellow',marker="o",label='4 hadoop group')
l5, = plt.plot(t,CPU_5,color='springgreen',marker="o",label='5 hadoop group')
l6, = plt.plot(t,CPU_6,color='darkslategrey',marker="o",label='6 hadoop group')
l7, = plt.plot(t,CPU_7,color='red',marker="o",label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')
# color: darkorange lightcoral darkgoldenrod yellow greenyellow springgreen darkslategrey deepskyblue fushsia blue

x_ticks = range(5,75,5)
y_ticks = np.arange(0,21,1)

plt.legend(handles=[l1,l2,l3,l4,l5,l6,l7],labels=['1-hadoop-group-CPU','2-hadoop-group-CPU','3-hadoop-group-CPU','4-hadoop-group-CPU','5-hadoop-group-CPU','6-hadoop-group-CPU','7-hadoop-group-CPU'],loc="best")
plt.xlabel('time unit(seconds)',font2)
plt.ylabel('hadoop occupy CPU unit(% 32Processor)',font2)

plt.xticks(x_ticks)
plt.yticks(y_ticks)

#plt.savefig('.CPU%.png')

plt.show()

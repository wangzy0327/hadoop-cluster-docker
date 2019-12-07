import numpy as np
import matplotlib.pyplot as plt

t = np.arange(4.38,44,4.38)
# CPU_1 = [0.042, 0.045, 0.043, 0.044, 0.04, 0.041, 0.043, 0.042, 0.04, 0.04]
# CPU_2 = [0.124, 0.044, 0.042, 0.042, 0.046, 0.04, 0.041, 0.041, 0.041, 0.04]
# CPU_3 = [0.185, 0.112, 0.041, 0.043, 0.042, 0.041, 0.043, 0.041, 0.043, 0.043]
# CPU_4 = [0.232, 0.168, 0.114, 0.041, 0.048, 0.046, 0.046, 0.05, 0.042, 0.04]
# CPU_5 = [0.262, 0.184, 0.072, 0.042, 0.039, 0.048, 0.041, 0.044, 0.043, 0.042]
# CPU_6 = [0.314, 0.24, 0.133, 0.066, 0.061, 0.048, 0.04, 0.047, 0.04, 0.04]
# CPU_7 = [0.389, 0.35, 0.24, 0.204, 0.162, 0.122, 0.044, 0.041, 0.042, 0.042]



CPU_1 = [0.037, 0.035, 0.038, 0.042, 0.038, 0.037, 0.038, 0.039, 0.040, 0.038]
CPU_2 = [0.096, 0.038, 0.038, 0.038, 0.038, 0.039, 0.038, 0.038, 0.038, 0.038]
CPU_3 = [0.147, 0.033, 0.039, 0.04, 0.041, 0.038, 0.039, 0.038, 0.038, 0.038]
CPU_4 = [0.214, 0.084, 0.037, 0.04, 0.039, 0.038, 0.037, 0.038, 0.038, 0.038]
CPU_5 = [0.314, 0.149, 0.039, 0.04, 0.039, 0.04, 0.04, 0.038, 0.038, 0.038]
CPU_6 = [0.376, 0.188, 0.062, 0.037, 0.038, 0.038, 0.038, 0.042, 0.04, 0.038]
CPU_7 = [0.439, 0.244, 0.141, 0.035, 0.038, 0.038, 0.039, 0.038, 0.038, 0.038]


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

plt.title('reduce processing CPU% Analysis',font1)
l1, = plt.plot(t,CPU_1,color='green',marker="o",label='1 hadoop group')
l2, = plt.plot(t,CPU_2,color='darkorange',marker="o",label='2 hadoop group')
l3, = plt.plot(t,CPU_3,color='yellow',marker="o",label='3 hadoop group')
l4, = plt.plot(t,CPU_4,color='greenyellow',marker="o",label='4 hadoop group')
l5, = plt.plot(t,CPU_5,color='springgreen',marker="o",label='5 hadoop group')
l6, = plt.plot(t,CPU_6,color='darkslategrey',marker="o",label='6 hadoop group')
l7, = plt.plot(t,CPU_7,color='red',marker="o",label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')
# color: darkorange lightcoral darkgoldenrod yellow greenyellow springgreen darkslategrey deepskyblue fushsia blue

x_ticks = range(5,50,5)
y_ticks = np.arange(0,0.6,0.1)

plt.legend(handles=[l1,l2,l3,l4,l5,l6,l7],labels=['1-hadoop-group-CPU','2-hadoop-group-CPU','3-hadoop-group-CPU','4-hadoop-group-CPU','5-hadoop-group-CPU','6-hadoop-group-CPU','7-hadoop-group-CPU'],loc="best")
plt.xlabel('time unit(seconds)',font2)
plt.ylabel('hadoop occupy CPU unit(% 32Processor)',font2)

plt.xticks(x_ticks)
plt.yticks(y_ticks)

#plt.savefig('.CPU%.png')

plt.show()

import numpy as np
import matplotlib.pyplot as plt

t = range(5,135,5)
CPU_1 = [0.042,1.515,1.253,1.124,0.041,1.918,3.281,3.319,1.675,1.236,1.933,1.910,2.60,0.946,2.134,1.52,0.072,1.366,2.052,2.439,0.105,1.323,1.743,2.233,0.042,0.042]
CPU_7 = [0.041,1.60,5.733,4.334,9.935,10.904,10.082,22.259,17.520,16.623,5.388,14.138,12.635,8.811,3.124,2.150,1.909,2.509,1.014,0.659,0.562,0.545,0.475,0.435,0.415,0.433]
x2 = [1,2,3,5,7,10]
multi = [43.819,51.812,61.774,88.472,96.445,107.444]

plt.title('processing CPU% Analysis')
l1, = plt.plot(t,CPU_1,color='green',label='1 hadoop group')
l7, = plt.plot(t,CPU_7,color='red',label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')

x_ticks = np.arange(0,140,5)
y_ticks = np.arange(0,25,0.5)

plt.legend(handles=[l1,l7],labels=['1-hadoop-group-CPU','7-hadoop-group-CPU'],loc="best")
plt.xlabel('time unit(seconds)')
plt.ylabel('hadoop occupy CPU unit(1)')

plt.xticks(x_ticks)
plt.yticks(y_ticks)

plt.show()

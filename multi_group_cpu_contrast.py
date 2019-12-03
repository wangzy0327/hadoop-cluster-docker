import numpy as np
import matplotlib.pyplot as plt

t = range(5,175,5)
CPU_1 = [0.044, 2.13, 2.547, 1.862, 0.044, 2.31, 2.021, 2.233, 0.044, 2.146, 2.16, 1.629, 0.041, 2.021, 2.424, 2.292, 0.042, 2.081, 2.172, 1.947, 0.04, 2.004, 2.221, 2.084, 0.043, 2.133, 2.219, 2.125, 0.041, 0.04, 0.042, 0.042, 0.044, 0.042]
CPU_2 = [0.046, 1.745, 5.602, 3.034, 3.649, 2.019, 1.975, 0.431, 2.772, 3.138, 4.13, 0.277, 3.5, 2.581, 2.076, 2.029, 0.128, 3.266, 3.846, 4.197, 4.612, 1.929, 0.938, 1.326, 0.105, 1.755, 1.916, 1.806, 0.111, 0.108, 0.101, 0.102, 0.104, 0.106]
CPU_3 = [0.042, 1.786, 5.027, 8.873, 9.895, 5.632, 4.811, 5.485, 3.964, 2.239, 2.226, 1.725, 5.081, 4.485, 5.497, 5.478, 8.201, 4.51, 3.104, 2.54, 0.176, 1.654, 2.022, 1.884, 0.189, 0.166, 0.2, 0.205, 0.204, 0.182, 0.161, 0.159, 0.192, 0.18]
CPU_4 = [0.038, 2.128, 2.821, 5.838, 14.7, 13.999, 8.499, 3.762, 2.7, 5.535, 5.369, 3.896, 0.295, 6.142, 7.283, 4.526, 7.568, 2.212, 1.301, 2.171, 1.573, 0.256, 0.26, 0.238, 0.232, 0.224, 0.254, 0.248, 0.259, 0.227, 0.229, 0.230, 0.230, 0.230]
CPU_5 = [0.041, 1.945, 4.505, 4.567, 11.23, 17.233, 13.638, 10.353, 5.235, 5.866, 7.402, 5.141, 1.494, 0.379, 3.606, 5.334, 4.471, 0.421, 0.45, 2.026, 1.106, 1.273, 0.289, 0.318, 0.288, 0.255, 0.292, 0.344, 0.327, 0.312, 0.287, 0.283, 0.283, 0.285]
CPU_6 = [0.041, 2.139, 4.479, 5.162, 8.76, 10.771, 20.178, 13.755, 13.583, 4.954, 15.834, 13.597, 8.947, 4.87, 2.37, 2.302, 1.706, 2.444, 2.565, 0.345, 0.345, 0.324, 0.308, 0.366, 0.323, 0.296, 0.296, 0.307, 0.325, 0.305, 0.300, 0.300, 0.300, 0.300]
CPU_7 = [0.041, 1.598, 5.734, 4.334, 9.935, 10.904, 10.082, 22.259, 17.52, 16.623, 5.388, 14.138, 12.635, 8.811, 3.124, 2.15, 1.909, 2.509, 1.014, 0.659, 0.562, 0.545, 0.475, 0.435, 0.415, 0.433, 0.420, 0.420, 0.420, 0.420, 0.420, 0.420, 0.420, 0.420]


plt.title('processing CPU% Analysis')
l1, = plt.plot(t,CPU_1,color='green',label='1 hadoop group')
l2, = plt.plot(t,CPU_2,color='darkorange',label='2 hadoop group')
l3, = plt.plot(t,CPU_3,color='yellow',label='3 hadoop group')
l4, = plt.plot(t,CPU_4,color='greenyellow',label='4 hadoop group')
l5, = plt.plot(t,CPU_5,color='springgreen',label='5 hadoop group')
l6, = plt.plot(t,CPU_6,color='darkslategrey',label='6 hadoop group')
l7, = plt.plot(t,CPU_7,color='red',label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')
# color: darkorange lightcoral darkgoldenrod yellow greenyellow springgreen darkslategrey deepskyblue fushsia blue

x_ticks = np.arange(0,175,5)
y_ticks = np.arange(0,25,0.5)

plt.legend(handles=[l1,l2,l3,l4,l5,l6,l7],labels=['1-hadoop-group-CPU','2-hadoop-group-CPU','3-hadoop-group-CPU','4-hadoop-group-CPU','5-hadoop-group-CPU','6-hadoop-group-CPU','7-hadoop-group-CPU'],loc="best")
plt.xlabel('time unit(seconds)')
plt.ylabel('hadoop occupy CPU unit(% 32Processor)')

plt.xticks(x_ticks)
plt.yticks(y_ticks)

plt.savefig('.CPU%.png')

plt.show()

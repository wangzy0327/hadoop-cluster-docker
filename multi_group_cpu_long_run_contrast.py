import numpy as np
import matplotlib.pyplot as plt

t = range(5,175,5)
CPU_1 = [0.33, 1.8, 1.89, 1.488, 0.322, 1.496, 1.5, 1.514, 0.81, 1.703, 2.174, 2.355, 1.446, 2.063, 2.392, 2.383, 2.047, 2.401, 2.43, 2.398, 2.228, 2.296, 2.206, 1.942, 2.523, 2.258, 2.663, 1.603, 0.38, 0.34, 0.323, 0.384, 0.356, 0.359]
CPU_2 = [0.358, 4.275, 3.572, 3.444, 0.95, 0.401, 0.562, 2.326, 0.33, 2.498, 2.816, 3.772, 0.598, 0.756, 1.921, 1.366, 0.409, 4.872, 3.499, 3.489, 0.818, 0.892, 2.459, 1.371, 1.348, 2.049, 2.38, 2.509, 2.491, 0.322, 0.359, 0.366, 0.356, 0.321]
CPU_3 = [0.351, 5.852, 5.201, 4.962, 7.174, 2.846, 2.187, 3.433, 0.347, 5.652, 4.945, 5.367, 2.065, 0.574, 0.821, 4.52, 2.111, 0.36, 2.339, 2.201, 2.155, 0.33, 0.321, 0.339, 0.369, 0.371, 0.345, 0.321, 0.343, 0.415, 0.353, 0.353, 0.353, 0.353]
CPU_4 = [0.516, 6.266, 7.361, 8.066, 14.773, 7.225, 5.703, 5.724, 0.368, 6.182, 5.946, 4.415, 1.304, 0.859, 2.68, 4.391, 0.32, 0.325, 0.349, 0.35, 0.331, 0.329, 0.331, 0.375, 0.374, 0.353, 0.333, 0.333, 0.333, 0.333, 0.333, 0.333, 0.333, 0.333]
CPU_5 = [0.322, 5.097, 7.227, 8.07, 2.842, 2.794, 6.655, 5.278, 1.49, 0.357, 4.388, 4.218, 3.58, 4.454, 3.229, 2.778, 2.243, 2.402, 0.331, 0.371, 0.358, 0.33, 0.338, 0.313, 0.349, 0.346, 0.366, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.32]
CPU_6 = [0.356, 10.589, 10.522, 11.36, 8.255, 0.584, 8.784, 2.707, 5.32, 2.816, 0.388, 2.214, 2.307, 2.458, 2.107, 0.374, 0.399, 0.374, 0.341, 0.34, 0.353, 0.354, 0.349, 0.357, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35, 0.35]
CPU_7 = [0.355, 0.486, 10.794, 11.838, 10.079, 15.143, 14.092, 12.506, 7.551, 2.382, 0.595, 0.365, 0.331, 0.346, 0.366, 0.347, 0.334, 0.323, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33, 0.33]

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

plt.title('long run processing CPU% Analysis',font1)
l1, = plt.plot(t,CPU_1,color='green',marker="o",label='1 hadoop group')
l2, = plt.plot(t,CPU_2,color='darkorange',marker="o",label='2 hadoop group')
l3, = plt.plot(t,CPU_3,color='yellow',marker="o",label='3 hadoop group')
l4, = plt.plot(t,CPU_4,color='greenyellow',marker="o",label='4 hadoop group')
l5, = plt.plot(t,CPU_5,color='springgreen',marker="o",label='5 hadoop group')
l6, = plt.plot(t,CPU_6,color='darkslategrey',marker="o",label='6 hadoop group')
l7, = plt.plot(t,CPU_7,color='red',marker="o",label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')
# color: darkorange lightcoral darkgoldenrod yellow greenyellow springgreen darkslategrey deepskyblue fushsia blue

x_ticks = np.arange(5,175,10)
y_ticks = np.arange(0,25,5)

plt.legend(handles=[l1,l2,l3,l4,l5,l6,l7],labels=['1-hadoop-group-CPU','2-hadoop-group-CPU','3-hadoop-group-CPU','4-hadoop-group-CPU','5-hadoop-group-CPU','6-hadoop-group-CPU','7-hadoop-group-CPU'],loc="best")
plt.xlabel('time unit(seconds)',font2)
plt.ylabel('hadoop occupy CPU unit(% 32Processor)',font2)

plt.xticks(x_ticks)
plt.yticks(y_ticks)

#plt.savefig('.CPU%.png')

plt.show()

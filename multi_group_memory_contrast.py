import numpy as np
import matplotlib.pyplot as plt

t = range(5,175,5)
MEM_1 = [0.031, 0.034, 0.034, 0.034, 0.031, 0.034, 0.034, 0.034, 0.031, 0.033, 0.035, 0.034, 0.031, 0.033, 0.034, 0.034, 0.031, 0.033, 0.034, 0.034, 0.031, 0.033, 0.034, 0.034, 0.031, 0.033, 0.034, 0.034, 0.031, 0.031, 0.031, 0.031, 0.031, 0.031]
MEM_2 = [0.031, 0.033, 0.045, 0.054, 0.057, 0.068, 0.068, 0.066, 0.071, 0.071, 0.077, 0.079, 0.089, 0.083, 0.079, 0.073, 0.07, 0.076, 0.076, 0.083, 0.086, 0.083, 0.078, 0.074, 0.071, 0.073, 0.073, 0.073, 0.071, 0.071, 0.071, 0.071, 0.071, 0.071]
MEM_3 = [0.032, 0.034, 0.049, 0.073, 0.082, 0.099, 0.121, 0.132, 0.133, 0.123, 0.109, 0.111, 0.114, 0.114, 0.116, 0.132, 0.148, 0.139, 0.13, 0.116, 0.112, 0.113, 0.114, 0.114, 0.112, 0.112, 0.112, 0.112, 0.112, 0.112, 0.112, 0.112, 0.112, 0.112]
MEM_4 = [0.032, 0.035, 0.05, 0.073, 0.105, 0.126, 0.149, 0.17, 0.176, 0.18, 0.171, 0.151, 0.145, 0.152, 0.153, 0.166, 0.177, 0.173, 0.166, 0.152, 0.152, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148, 0.148]
MEM_5 = [0.032, 0.034, 0.049, 0.068, 0.106, 0.141, 0.166, 0.194, 0.221, 0.238, 0.235, 0.213, 0.185, 0.185, 0.189, 0.193, 0.197, 0.2, 0.201, 0.201, 0.197, 0.19, 0.19, 0.19, 0.19, 0.19, 0.19, 0.19, 0.19, 0.19, 0.19, 0.190, 0.190, 0.190]
MEM_6 = [0.032, 0.034, 0.049, 0.069, 0.102, 0.133, 0.179, 0.193, 0.233, 0.264, 0.299, 0.297, 0.279, 0.237, 0.226, 0.226, 0.228, 0.231, 0.232, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23, 0.23]
MEM_7 = [0.03, 0.032, 0.047, 0.066, 0.098, 0.131, 0.169, 0.219, 0.234, 0.281, 0.314, 0.344, 0.337, 0.318, 0.271, 0.264, 0.263, 0.264, 0.265, 0.266, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267, 0.267]

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

plt.title('processing Memory% Analysis',font1)
l1, = plt.plot(t,MEM_1,color='green',marker="o",label='1 hadoop group')
l2, = plt.plot(t,MEM_2,color='darkorange',marker="o",label='2 hadoop group')
l3, = plt.plot(t,MEM_3,color='yellow',marker="o",label='3 hadoop group')
l4, = plt.plot(t,MEM_4,color='greenyellow',marker="o",label='4 hadoop group')
l5, = plt.plot(t,MEM_5,color='springgreen',marker="o",label='5 hadoop group')
l6, = plt.plot(t,MEM_6,color='darkslategrey',marker="o",label='6 hadoop group')
l7, = plt.plot(t,MEM_7,color='red',marker="o",label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')

# color: darkorange lightcoral darkgoldenrod yellow greenyellow springgreen darkslategrey deepskyblue fushsia blue

x_ticks = np.arange(5,175,20)
y_ticks = np.arange(0,0.5,0.1)

plt.legend(handles=[l1,l2,l3,l4,l5,l6,l7],labels=['1-hadoop-group-MEM','2-hadoop-group-MEM','3-hadoop-group-MEM','4-hadoop-group-MEM','5-hadoop-group-MEM','6-hadoop-group-MEM','7-hadoop-group-MEM'],loc="best")
plt.xlabel('time unit(seconds)',font2)
plt.ylabel('hadoop occupy MEM unit(% 62G)',font2)

plt.xticks(x_ticks)
plt.yticks(y_ticks)

#plt.savefig('.MEM%.png')

plt.show()

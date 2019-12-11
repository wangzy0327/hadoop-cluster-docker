import numpy as np
import matplotlib.pyplot as plt

t = np.arange(0,70,7)

# MEM_1 = [0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
# MEM_2 = [0.067, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
# MEM_3 = [0.102, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
# MEM_4 = [0.14, 0.067, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
# MEM_5 = [0.175, 0.103, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
# MEM_6 = [0.21, 0.139, 0.05, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
# MEM_7 = [0.247, 0.175, 0.103, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]

MEM_1 = [0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
MEM_2 = [0.067, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
MEM_3 = [0.102, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
MEM_4 = [0.14, 0.067, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
MEM_5 = [0.175, 0.103, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
MEM_6 = [0.21, 0.139, 0.05, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]
MEM_7 = [0.247, 0.175, 0.103, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03]



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

plt.title('reduce processing MEM% Analysis',font1)
l1, = plt.plot(t,MEM_1,color='green',marker="o",label='1 hadoop group')
l2, = plt.plot(t,MEM_2,color='darkorange',marker="o",label='2 hadoop group')
l3, = plt.plot(t,MEM_3,color='yellow',marker="o",label='3 hadoop group')
l4, = plt.plot(t,MEM_4,color='greenyellow',marker="o",label='4 hadoop group')
l5, = plt.plot(t,MEM_5,color='springgreen',marker="o",label='5 hadoop group')
l6, = plt.plot(t,MEM_6,color='darkslategrey',marker="o",label='6 hadoop group')
l7, = plt.plot(t,MEM_7,color='red',marker="o",label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')
# color: darkorange lightcoral darkgoldenrod yellow greenyellow springgreen darkslategrey deepskyblue fushsia blue

x_ticks = range(5,75,5)
y_ticks = np.arange(0,0.35,0.05)

plt.legend(handles=[l1,l2,l3,l4,l5,l6,l7],labels=['1-hadoop-group-MEM','2-hadoop-group-MEM','3-hadoop-group-MEM','4-hadoop-group-MEM','5-hadoop-group-MEM','6-hadoop-group-MEM','7-hadoop-group-MEM'],loc="best")
plt.xlabel('time unit(seconds)',font2)
plt.ylabel('hadoop occupy MEM unit(% 32Processor)',font2)

plt.xticks(x_ticks)
plt.yticks(y_ticks)

#plt.savefig('.MEM%.png')

plt.show()

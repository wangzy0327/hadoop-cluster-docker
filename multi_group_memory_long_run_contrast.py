import numpy as np
import matplotlib.pyplot as plt

t = range(5,175,5)
MEM_1 = [0.292, 0.295, 0.296, 0.292, 0.292, 0.293, 0.293, 0.294, 0.292, 0.294, 0.294, 0.294, 0.293, 0.294, 0.294, 0.295, 0.294, 0.295, 0.295, 0.295, 0.294, 0.295, 0.295, 0.296, 0.295, 0.296, 0.296, 0.293, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292]
MEM_2 = [0.292, 0.299, 0.295, 0.302, 0.304, 0.304, 0.304, 0.295, 0.292, 0.293, 0.298, 0.301, 0.303, 0.303, 0.303, 0.3, 0.292, 0.3, 0.297, 0.3, 0.303, 0.304, 0.306, 0.299, 0.296, 0.294, 0.295, 0.295, 0.296, 0.292, 0.292, 0.292, 0.292, 0.292]
MEM_3 = [0.294, 0.304, 0.3, 0.314, 0.324, 0.319, 0.314, 0.299, 0.294, 0.302, 0.302, 0.31, 0.318, 0.317, 0.316, 0.301, 0.298, 0.295, 0.298, 0.298, 0.298, 0.295, 0.295, 0.295, 0.295, 0.295, 0.295, 0.295, 0.295, 0.295, 0.295, 0.293, 0.293, 0.293]
MEM_4 = [0.294, 0.303, 0.308, 0.328, 0.348, 0.334, 0.323, 0.303, 0.293, 0.304, 0.302, 0.307, 0.315, 0.315, 0.315, 0.313, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293]
MEM_5 = [0.293, 0.304, 0.309, 0.32, 0.337, 0.337, 0.337, 0.327, 0.295, 0.294, 0.299, 0.3, 0.303, 0.308, 0.309, 0.307, 0.303, 0.296, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293, 0.293]
MEM_6 = [0.291, 0.311, 0.312, 0.345, 0.369, 0.347, 0.357, 0.327, 0.292, 0.3, 0.292, 0.296, 0.296, 0.295, 0.294, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292, 0.292]
MEM_7 = [0.292, 0.292, 0.313, 0.317, 0.353, 0.402, 0.374, 0.354, 0.311, 0.292, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289, 0.289]

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

plt.title('long run processing Memory% Analysis',font1)
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
y_ticks = np.arange(0.25,0.5,0.1)

plt.legend(handles=[l1,l2,l3,l4,l5,l6,l7],labels=['1-hadoop-group-MEM','2-hadoop-group-MEM','3-hadoop-group-MEM','4-hadoop-group-MEM','5-hadoop-group-MEM','6-hadoop-group-MEM','7-hadoop-group-MEM'],loc="best")
plt.xlabel('time unit(seconds)',font2)
plt.ylabel('hadoop occupy MEM unit(% 62G)',font2)

plt.xticks(x_ticks)
plt.yticks(y_ticks)

#plt.savefig('.MEM%.png')

plt.show()

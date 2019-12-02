import numpy as np
import matplotlib.pyplot as plt

t = range(5,135,5)
MEM_1 = [0.030,0.035,0.030,0.031,0.030,0.034,0.034,0.036,0.032,0.031,0.032,0.032,0.034,0.031,0.033,0.030,0.031,0.032,0.034,0.030,0.032,0.032,0.033,0.030,0.030,0.030]
MEM_7 = [0.030,0.032,0.047,0.066,0.098,0.131,0.169,0.219,0.234,0.281,0.314,0.344,0.337,0.318,0.271,0.264,0.263,0.264,0.265,0.266,0.267,0.267,0.267,0.267,0.267,0.267]
x2 = [1,2,3,5,7,10]
multi = [43.819,51.812,61.774,88.472,96.445,107.444]

plt.title('processing Memory% Analysis')
l1, = plt.plot(t,MEM_1,color='green',label='1 hadoop group')
l7, = plt.plot(t,MEM_7,color='red',label='7 hadoop group')
#l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')

x_ticks = np.arange(0,140,5)
y_ticks = np.arange(0,0.4,0.01)

plt.legend(handles=[l1,l7],labels=['1-hadoop-group-MEM','7-hadoop-group-MEM'],loc="best")
plt.xlabel('time unit(seconds)')
plt.ylabel('hadoop occupy MEM unit(% 62G)')

plt.xticks(x_ticks)
plt.yticks(y_ticks)

plt.show()

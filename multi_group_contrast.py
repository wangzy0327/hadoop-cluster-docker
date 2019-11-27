import numpy as np
import matplotlib.pyplot as plt

x1 = [1,2,3,5,10]
single = [43.789,86.514,129.265,214.644,435.734]
x2 = [1,2,3,5,7,10]
multi = [43.819,51.812,61.774,88.472,96.445,107.444]

plt.title('processing time Analysis')
l1, = plt.plot(x1,single,color='green',label='single hadoop group')
l2, = plt.plot(x2,multi,color='red',label='multi hadoop group')

x_ticks = np.arange(0,11,1)
y_ticks = np.arange(0,470,20)

plt.legend(handles=[l1,l2,],labels=['single','multi'],loc="best")
plt.xlabel('hadoop task request numbers  unit(1)')
plt.ylabel('processing time  unit(seconds)')

plt.xticks(x_ticks)
plt.yticks(y_ticks)

plt.show()

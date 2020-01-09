import numpy as np
import matplotlib.pyplot as plt

x1 = [1,2,3,4,5,6,7,8,9,10]
#single = [21.314,42.573,63.922,85.241,106.107,127.412,148.722,170.032,191.343,212.658]

single = [51.337,104.294,157.023,207.280,260.002,312.343,364.296,416.161,469.033,522.037]

x2 = [1,2,3,4,5,6,7,8,9,10]
#auto_scaling = [21.326,55.548,54.235,52.982,55.063,59.871,62.999,85.377,106.564,101.499]

auto_scaling = [51.337,58.605,63.374,69.149,78.983,83.725,91.456,131.605,133.803,143.027]
x3 = [1,2,3,4,5,6,7,8,9,10]
#long_run = [21.308,44.21,46.562,51.364,52.063,55.871,62.365,85.377,106.564,101.499]

long_run = [51.337,56.038,60.730,68.932,76.647,81.935,91.079,131.156,135.352,137.517]

name_list = ['1 task','2 task','3 task','4 task','5 task','6 task','7 task','8 task','9 task','10 task']

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

plt.title('long run processing time Analysis',font1)
#l1, = plt.plot(x1,single,color='green',marker="o",label='single hadoop group')
l2, = plt.plot(x2,auto_scaling,color='red',marker="o",label='auto-scaling hadoop group')
l3, = plt.plot(x3,long_run,color='deepskyblue',marker='o',label='long run group')

# color: darkorange lightcoral darkgoldenrod yellow greenyellow springgreen darkslategrey deepskyblue fushsia blue

x_ticks = np.arange(1,11,1)
y_ticks = np.arange(50,150,5)

plt.legend(handles=[l2,l3,],labels=['auto-scaling','long-run'],loc="best")
plt.xlabel('hadoop task request numbers  unit(1)',font2)
plt.ylabel('processing time  unit(seconds)',font2)

plt.xticks(x_ticks)
plt.yticks(y_ticks)

plt.show()
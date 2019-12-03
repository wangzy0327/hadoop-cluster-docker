import pandas as pd
import os
filePath = ("resource_1/")
dirs = os.listdir(filePath)
cpus = []
for i,dir in enumerate(dirs):
    data = pd.read_csv(filePath+dir)
    df = pd.DataFrame(data)
    p_float = df['CPU %'].str.strip("%").astype(float)/100
    cpu_sum = p_float.sum()
    cpus.append(round(cpu_sum,3))
    print(dir+" CPU : "+str(cpu_sum))
print(cpus[0:34])

import pandas as pd
import os
filePath = ("resource_1/")
dirs = os.listdir(filePath)
mems = []
for i,dir in enumerate(dirs):
    data = pd.read_csv(filePath+dir)
    df = pd.DataFrame(data)
    p_float = df['MEM %'].str.strip("%").astype(float)/100
    mem_sum = p_float.sum()
    mems.append(round(mem_sum,3))
    print(dir+"  MEM : "+str(mem_sum))
print(mems[0:34])

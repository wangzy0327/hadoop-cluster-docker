import pandas as pd
import os
filePath = ("resource/")
dirs = os.listdir(filePath)
for i,dir in enumerate(dirs):
    data = pd.read_csv(filePath+dir)
    df = pd.DataFrame(data)
    p_float = df['MEM %'].str.strip("%").astype(float)/100
    cpu_sum = p_float.sum()
    print(dir+"  MEM : "+str(cpu_sum))

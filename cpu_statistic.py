import pandas as pd
import os
filePath = ("resource/")
dirs = os.listdir(filePath)
for i,dir in enumerate(dirs):
    data = pd.read_csv(filePath+dir)
    df = pd.DataFrame(data)
    p_float = df['CPU %'].str.strip("%").astype(float)/100
    cpu_sum = p_float.sum()
    print(dir+" CPU : "+str(cpu_sum))

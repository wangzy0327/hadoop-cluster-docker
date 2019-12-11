import subprocess
import time


class Statistics():
    log_file = "resource/resource_log"

    def parse_shell(self, shcmd):
        p = subprocess.Popen(shcmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print(str(stderr, encoding="utf-8").strip('\n'))
            return str(stderr, encoding="utf-8").strip('\n')
        return str(stdout, encoding="utf-8".strip('\n'))
        pass
    pass

    def collect_resource_log(self,flag,index):
        #if flag == 0:
        res = self.parse_shell(
            "docker stats --no-stream --format 'table {{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}' | head -1;\
            docker stats --no-stream --format 'table {{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}' | grep 'hadoop-[a-z]*-[0-9]?*' ")
        #else:
            #res = self.parse_shell(
            #"docker stats --no-stream --format 'table {{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}' | grep 'hadoop-[a-z]*-[0-9]?*' ")
        if flag == "":
            self.file_operator(res,index,flag)
        else:
            self.file_operator(res,index,flag)
        pass

    def file_operator(self, content,index,flag):
        if flag == "":
            f = open(self.log_file+"_"+str(index), 'a')
        else:
            f = open(self.log_file+"_"+flag+"_"+str(index),'a')
        f.write(content)
        f.close()
    
    def judge_end(self):
        symbol = open('symbol','r+')
        info = symbol.readlines()
        symbol.close()
        return "".join(info).strip()

    def clear_symbol(self):
        symbol = open('symbol','r+')
        symbol.truncate()
        print("clear symbol")

    def go(self):
        #flag = 0
        i = 1
        while True:
            time.sleep(0.2)
            print("time  "+str(i)+" : "+str(round(time.time(),3)))
            info = self.judge_end()
            print("info : "+info)
            if info == 'end':
                print("end")
                j = 1
                while j < 5:
                    print(j)
                    time.sleep(0.2)
                    print("time end "+str(j)+" : "+str(round(time.time(),3)))
                    self.collect_resource_log("end",j)
                    j+=1
                self.clear_symbol()
                break
            else:
                self.collect_resource_log("",i)
                i+=1
            pass

if __name__ == "__main__":
    statictis = Statistics()
    startTime = round(time.time(),3)
    print('\033[1;35m 开始时间戳:'+str(startTime)+" \033[0m")
    statictis.go()
    endTime = round(time.time(),3)
    print('\033[1;35m 结束时间戳:'+str(endTime)+" \033[0m")
    diffTime = endTime - startTime
    print("processing time : "+str(diffTime))

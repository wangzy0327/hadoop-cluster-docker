import subprocess
import time


class Statistics():
    log_file = "resource_log"

    def parse_shell(self, shcmd):
        p = subprocess.Popen(shcmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            print(str(stderr, encoding="utf-8").strip('\n'))
            return str(stderr, encoding="utf-8").strip('\n')
        return str(stdout, encoding="utf-8".strip('\n'))
        pass
    pass

    def collect_resource_log(self):
        res = self.parse_shell(
            "docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' | head -1;\
            docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' | grep 'hadoop-[a-z]*-[0-9]?*' ")
        self.file_operator(res)
        pass

    def file_operator(self, content):
        f = open(self.log_file, 'a')
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
        while True:
            time.sleep(1)
            self.collect_resource_log()
            info = self.judge_end()
            if info == 'end':
                self.clear_symbol()
                break
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

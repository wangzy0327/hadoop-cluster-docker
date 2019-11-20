import subprocess

import os
import time

class State():
    count = 10
    publish_output = "publish/publish.txt"
    subscribe_output = "subscribe/subscribe.txt"
    one_count = 0
    shcmd = []
    uuid = []
    hadoop_list = []
    exec_state = []
    max_num = 10

    def get_shcmd(self,file_name):
        f = open(file_name)
        self.shcmd = []
        self.uuid = []
        for i in range(self.count):
            sstr = f.readline().strip()
            if sstr != None and sstr.strip()!='':
                self.shcmd.append(sstr)
                print("shcmd : "+sstr)
                self.uuid.append(sstr.split()[-1])
                print("uuid : "+sstr.split()[-1])
        pass

    def get_hadoop(self):
        hadoop_count = int(self.parse_shell("docker ps | grep hadoop-master | wc -l"))
        self.hadoop_list = []
        for i in range(hadoop_count):
            self.hadoop_list.append("hadoop-master-"+str(i))
        pass
 
    def init_hadoop(self,count):
        while True:
            hadoop_count = int(self.parse_shell("docker ps | grep hadoop-master | wc -l"))
            if hadoop_count >= count:
                self.hadoop_list = []
                for i in range(hadoop_count):
                    self.hadoop_list.append("hadoop-master-" + str(i))
                print("init complete!")
                return 
    
    def resize(self):
        print("shcmd num : "+str(self.shcmd))
        print("hadoop group num : "+str(self.hadoop_list))
        if len(self.shcmd) <= 1:
            self.one_count += 1
            if self.one_count >= 50 and len(self.hadoop_list) > 1:
                # todo   compress hadoop-docker group size
                print("\033[1;35m reduce hadoop group ...... \033[1;35m")
                self.reduce_group()
                self.init_hadoop(1)
                self.one_count = 0
        if len(self.shcmd) > len(self.hadoop_list)*2:
            # todo  extend hadoop-docker group size
            print("\033[1;35m extend hadoop group ...... \033[1;35m")
            self.extend_group(len(self.shcmd))
            self.init_hadoop(len(self.shcmd))
            pass
        pass
    
    def parse_shell(self,shcmd):
        p = subprocess.Popen(shcmd,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)	
        stdout,stderr = p.communicate()
        if p.returncode != 0:
           print(str(stderr,encoding="utf-8").strip('\n'))
           return str(stderr,encoding="utf-8").strip('\n')
        return str(stdout,encoding="utf-8".strip('\n'))
        pass

    def extend_group(self,num):
        print("max_num : "+str(self.max_num))
        num = num if num <= self.max_num else self.max_num
        print("num : "+str(num))
        print("start exec extend....")
        self.parse_shell("sh extend-container.sh "+str(num))
        print("end exec extend....")
        #subprocess.check_output(["sh","extend-container.sh",str(num)])
        pass

    def reduce_group(self):
        print("start exec reduce....")
        self.parse_shell("sh reduce-container.sh")
        print("end exec reduce....")
        #subprocess.check_output(["sh","reduce-container.sh"])
        pass

    def get_last_lines(self,file_name,count):
        file_size = os.path.getsize(file_name)
        block_size = 1024
        file = open(file_name,'r')
        # last_line = ""
        if file_size > block_size:
            # maxseekpoint = (file_size//block_size)
            maxseekpoint = file_size - block_size if file_size >= block_size else 0
            # remainder = (file_size%block_size)
            file.seek(maxseekpoint)
        elif file_size:
            file.seek(0,0)
        lines = file.readlines()
        if lines :
            last_line = [ s.strip() for s in lines[-1*count:]]
            #print("last_line : ",last_line)
        file.close()
        time.sleep(1.5)
        return lines
        pass


    def exec_cmd(self):
        sh_num = len(self.shcmd)
        print("sh_num is "+str(sh_num))
        hadoop_num = len(self.hadoop_list)
        print("hadoop_num is "+str(hadoop_num))
        self.exec_state = [None]*hadoop_num
        i = 0
        j = 0
        while i < sh_num:
            res = ""
            if self.exec_state[j] is None:
                self.exec_state[j] = self.uuid[i]
                #subprocess.check_output(['docker','exec','hadoop-master-'+j,'bash','-c',self.shcmd[i]])
                print("exec_state is None!")
                print("docker exec  hadoop-master-"+str(j)+" ......")
                res = self.parse_shell("docker exec -d hadoop-master-"+str(j)+" bash -c '"+self.shcmd[i]+"'")
                print("docker exec -d hadoop-master-" +str(j)+" bash -c '"+self.shcmd[i]+"'")
                print("docker exec hadoop-master-"+str(j)+" end .......")
                i+=1
            else:
                last_lines = self.get_last_lines(self.subscribe_output,sh_num)
                time.sleep(1)
                for line in last_lines:
                    uuid = line.split()[-1]
                    #print("subscribe uuid : "+uuid)
                    if self.exec_state[j] == uuid:
                        self.exec_state[j] = self.uuid[i]
                        #subprocess.check_output(['docker', 'exec', 'hadoop-master-' + j, 'bash', '-c', self.shcmd[i]])
                        print("subscribe docker exec hadoop-master-"+str(j)+" .....")
                        res = self.parse_shell("docker exec -d hadoop-master-" +str(j)+" bash -c '"+self.shcmd[i]+"'")
                        print("docker exec -d hadoop-master-" +str(j)+" bash -c '"+self.shcmd[i]+"'")
                        print("subscribe docker exec hadoop-master-"+str(j)+" end......")
                        i+=1
                print("___________________________")
                pass
            #print("j 自增!")
            j = (j + 1) % hadoop_num
            #print("j : "+str(j))        
            pass
        pass
        while True:
            time.sleep(1)
            if not any(self.exec_state):
                print("all uuid are None!")
                break
            else:
                for i,sh_state in enumerate(self.exec_state):
                    if sh_state is not None:
                        last_lines = self.get_last_lines(self.subscribe_output, sh_num)
                        for line in last_lines:
                            uuid = line.split()[-1]
                            #print("check uuid : "+uuid)
                            if sh_state == uuid:
                                print("uuid [ "+uuid+" ] set None")
                                self.exec_state[i] = None
            print("____________________")
        print("current loop check complete...")
        pass        

    def go(self):
        while True:
            print("\033[1;35m get_shcmd \033[0m")
            self.get_shcmd(self.publish_output)
            print("\033[1;35m get_hadoop \033[0m")
            self.get_hadoop()
            print("\033[1;35m resize \033[0m")
            self.resize()
            print("\033[1;35m exec_cmd \033[0m")
            self.exec_cmd()
        pass


if __name__ == "__main__":
    state = State()
    #state.get_shcmd(State.publish_output)
    #state.extend_group(3)
    #state.reduce_group()
    #lines = state.get_last_lines(state.subscribe_output,10)
    #state.shcmd=['sh run-wordcount2.sh input/input1 output/output1 908f7dee-0a6e-11ea-84ff-35f681938c05','sh run-wordcount2.sh input/input1 output/output1 a2d1d326-0a6e-11ea-84ff-35f681938c05','sh run-wordcount2.sh input/input2 output/output2 aed091c6-0a6e-11ea-84ff-35f681938c05','sh run-wordcount2.sh input/input3 output/output3 ab970ad0-0a6e-11ea-84ff-35f681938c05']
    #state.hadoop_list=['hadoop-master-0','hadoop-master-1','hadoop-master-2']
    #state.uuid=['908f7dee-0a6e-11ea-84ff-35f681938c05','a2d1d326-0a6e-11ea-84ff-35f681938c05','aed091c6-0a6e-11ea-84ff-35f681938c05','ab970ad0-0a6e-11ea-84ff-35f681938c05']
    #state.exec_cmd()
    #state.parse_shell("docker exec -d hadoop-master-0 bash -c 'sh run-wordcount2.sh input/input1 output/output1 908f7dee-0a6e-11ea-84ff-35f681938c05' ")
    state.go()
    print("______________end______________")

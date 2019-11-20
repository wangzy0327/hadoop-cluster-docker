## Run Hadoop Cluster within Docker Containers Update

```
声明：此项目是基于kiwenlau的hadoop-cluster-docker进行改进的，在此对kiwenlau表示最诚挚的感谢，下面附上kiwenlau源项目地址。
在这里我作的改进有：基于docker容器组的hadoop集群根据访问队列请求的数量来动态扩缩hadoop容器组数量，以达到根据请求量动态分配相应的资源进行处理。这里设置的最大hadoop容器组数量为10。



```
- hadoop-cluster-docker: [kiwenlau hadoop-cluster-docker](https://github.com/kiwenlau/hadoop-cluster-docker)
- Blog: [Run Hadoop Cluster in Docker Update](http://kiwenlau.com/2016/06/26/hadoop-cluster-docker-update-english/)
- 博客: [基于Docker搭建Hadoop集群之升级版](http://kiwenlau.com/2016/06/12/160612-hadoop-cluster-docker-update/)

- Related Links: [scratchHadoop](http://github.com/wangzy0327/scratchHadoopProject)


![alt tag](https://raw.githubusercontent.com/wangzy0327/hadoop-cluster-docker/master/hadoop-cluster-docker.png)


### 3 Nodes Hadoop Cluster

##### 1. pull docker image

```
sudo docker pull kiwenlau/hadoop:1.0

or 

docker build -f Dockerfile -t kiwenlau/hadoop:1.0 .

```

##### 2. clone github repository

```
git clone https://github.com/wangzy0327/hadoop-cluster-docker
```

##### 3. publish queue && subscribe queue

```
publish queue:
hadoop-cluster-docker/publish/publish.txt 

subscribe queue:
hadoop-cluster-docker/subscribe/subscribe.txt

handler processing:
After the request task arrives, it enters the publish queue. The hadoop container group takes the task from the publish queue for processing, and enters the subscribe queue after the processing is completed.

content example:
sh run-wordcount2.sh input/input1 output/output1 908f7dee-0a6e-11ea-84ff-35f681938c05
sh run-wordcount2.sh input/input2 output/output2 a2d1d326-0a6e-11ea-84ff-35f681938c05
sh run-wordcount2.sh input/input3 output/output3 aed091c6-0a6e-11ea-84ff-35f681938c05
sh run-wordcount2.sh input/input2 output/output2 ab970ad0-0a6e-11ea-84ff-35f681938c05
sh run-wordcount2.sh input/input1 output/output1 dd50c952-0aa1-11ea-9823-d9b82c75bb49

parameter description:
run-wordcount2.sh is hadoop case which handler wordcount
input/input1 is hadoop case input path
output/output1 is hadoop case output path(persistence hdfs data)

xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx(uuid)[unique identify]

```

##### 4. start container groups

```
example :
start a container group
sh extend-container.sh 1
```

**output:**

```
create hadoop-1 network
start hadoop-master container...
start hadoop-slave1 container...
start hadoop-slave2 container...
root@hadoop-master:~# 
```
- start 3 containers with 1 master and 2 slaves
- you will get into the /root directory of hadoop-master container

##### 5. manual submit task to publish queue

```
echo "sh run-wordcount2.sh input/input1 output/output1 908f7dee-0a6e-11ea-84ff-35f681938c05" >> publish/publish.txt
echo "sh run-wordcount2.sh input/input2 output/output2 a2d1d326-0a6e-11ea-84ff-35f681938c05" >> publish/publish.txt
echo "sh run-wordcount2.sh input/input3 output/output3 aed091c6-0a6e-11ea-84ff-35f681938c05" >> publish/publish.txt 
   ... ...   

```

##### 6. submit task to publish queue with REST API

```
**construct proxy container:**
cd server/
docker build -f Dockerfile -t plserver_ubuntu .
note: 
modify for your path(run_server_container.sh start_server.sh)

sh run_server_container.sh

REPT API：
POST http://xxx.xxx.xxx.xxx:8081/hadoop
Body JSON
{
   	"input":"input/input3",
	"output":"output/output3"
}

```

##### 7. run wordcount with auto resize hadoop group

```
python3 state_machine.py
```

**output**

![alt tag](https://raw.githubusercontent.com/wangzy0327/hadoop-cluster-docker/master/resize-hadoop-group-1.png)
![alt tag](https://raw.githubusercontent.com/wangzy0327/hadoop-cluster-docker/master/resize-hadoop-group-2.png)
![alt tag](https://raw.githubusercontent.com/wangzy0327/hadoop-cluster-docker/master/resize-hadoop-group-3.png)
![alt tag](https://raw.githubusercontent.com/wangzy0327/hadoop-cluster-docker/master/resize-hadoop-group-4.png)





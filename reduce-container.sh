#!/bin/bash

# the default node number is 3
N=${1:-1}
num=3

current=`date "+%Y-%m-%d %H:%M:%S"`
timeStamp=`date -d "$current" +%s`
currentTimeStamp=$((10#$timeStamp*1000+10#`date "+%N"`/1000000))
beforeStartTime=`echo "scale=3;$currentTimeStamp/1000"|bc`
echo "开始时间戳:"$beforeStartTime
reduce_num=$N
current_num=`docker ps | grep hadoop-master | wc -l`
echo 'current num : '${current_num}
j=$(($current_num-1))
while [ $j -ge ${reduce_num} ]
do
   #remove hadoop master container
   sudo docker rm -f hadoop-master-${j} &> /dev/null
   echo "remove hadoop-master-${j} container..."
   #remove hadoop slave container
   i=1
   text=""
   while [ $i -lt $num ]
   do
        sudo docker rm -f hadoop-slave-$j-$i &> /dev/null
        echo "remove hadoop-slave-$j-$i container..."
        i=$(( $i + 1 ))
   done
   #remove docker network
   docker network rm hadoop-${j}
   echo "hadoop-${j} network remove"
   sleep 0.1

   echo "hadoop-${j} remove complete"
   j=$(( $j - 1 ))
   echo -e "\n***********************************\n"

done
current=`date "+%Y-%m-%d %H:%M:%S"`
timeStamp=`date -d "$current" +%s`
currentTimeStamp=$((10#$timeStamp*1000+10#`date "+%N"`/1000000))
endStartTime=`echo "scale=3;$currentTimeStamp/1000"|bc`
echo "结束时间戳:"$endStartTime
echo "end" > symbol

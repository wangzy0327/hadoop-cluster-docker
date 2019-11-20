#!/bin/bash

# the default node number is 3
N=${1:-3}


reduce_num=1
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
   while [ $i -lt $N ]
   do
        sudo docker rm -f hadoop-slave-$j-$i &> /dev/null
        echo "remove hadoop-slave-$j-$i container..."
        i=$(( $i + 1 ))
   done
   #remove docker network
   docker network rm hadoop-${j}
   echo "hadoop-${j} network remove"
   sleep 3

   echo "hadoop-${j} remove complete"
   j=$(( $j - 1 ))
   echo -e "\n***********************************\n"

done

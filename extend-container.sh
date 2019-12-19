#!/bin/bash

# the default node number is 3
#N=${1:-3}
N=3


extend_num=$1
current_num=`docker ps | grep hadoop-master | wc -l`
echo 'current num : '${current_num}
j=$current_num
while [ $j -lt ${extend_num} ]
do
   #remove docker network
   docker network rm hadoop-${j}
   #create docker network bridge
   docker network create hadoop-${j}
   echo "create hadoop-${j} network "
   #hadoop home config
   hadoop_home_config="/usr/local/hadoop/etc/hadoop"
   # start hadoop master container
   sudo docker rm -f hadoop-master-${j} &> /dev/null
   echo "start hadoop-master-${j} container..."
   sudo docker run -itd \
                --net=hadoop-${j} \
                -p 5006${j}:50070 \
                -p 900${j}:8088 \
                -v /home/wzy/hadoop-cluster-docker/input:/root/input \
                -v /home/wzy/hadoop-cluster-docker/output:/root/output \
                -v /home/wzy/hadoop-cluster-docker/run-wordcount2.sh:/root/run-wordcount2.sh \
                -v /home/wzy/hadoop-cluster-docker/publish:/root/publish \
                -v /home/wzy/hadoop-cluster-docker/subscribe:/root/subscribe \
                --name hadoop-master-${j} \
                --hostname hadoop-master-${j} \
                kiwenlau/hadoop:1.0 &> /dev/null
#                kiwenlau/hadoop:1.0 &> /dev/null 

# start hadoop slave container
   i=1
   text=""
   while [ $i -lt $N ]
   do
        sudo docker rm -f hadoop-slave-$j-$i &> /dev/null
        echo "start hadoop-slave-$j-$i container..."
        if [ $i -eq $[N-1] ]
        then
           text=$text"hadoop-slave-$j-"$i
           #text=$text"hadoop-slave"$i
        else
           text=$text"hadoop-slave-$j-"$i"\n"
           #text=$text"hadoop-slave"$i"\n"
        fi
        sudo docker run -itd \
                        --net=hadoop-${j} \
                        --name hadoop-slave-$j-$i \
                        --hostname hadoop-slave-$j-$i \
                        kiwenlau/hadoop:1.0 &> /dev/null
#                       kiwenlau/hadoop:1.0 &> /dev/null
        i=$(( $i + 1 ))
   done

   echo "____________________________________"
   echo -e $text
   echo "___________________________________"

   # get into hadoop master container
   i=1
   while [ $i -lt $N ]
   do
      sudo docker exec -dit hadoop-slave-$j-$i /bin/bash -c "sed -i 's/hadoop-master/hadoop-master-'${j}'/g' '${hadoop_home_config}'/yarn-site.xml  && sed -i 's/hadoop-master/hadoop-master-'${j}'/g' '${hadoop_home_config}'/core-site.xml  && echo  -e '$text' | tee '${hadoop_home_config}'/slaves"
      i=$(( $i + 1 ))
   done
#   sudo docker exec -it hadoop-slave-0-1 /bin/bash -c "sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/yarn-site.xml > '${hadoop_home_config}'/yarn-site.xml.tmp && mv -f '${hadoop_home_config}'/yarn-site.xml.tmp '${hadoop_home_config}'/yarn-site.xml && sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/core-site.xml > '${hadoop_home_config}'/core-site.xml.tmp && mv -f '${hadoop_home_config}'/core-site.xml.tmp '${hadoop_home_config}'/core-site.xml  && echo  -e '$text' | tee '${hadoop_home_config}'/slaves"
#  sudo docker exec -it hadoop-slave-0-2 /bin/bash -c "sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/yarn-site.xml > '${hadoop_home_config}'/yarn-site.xml.tmp && mv -f '${hadoop_home_config}'/yarn-site.xml.tmp '${hadoop_home_config}'/yarn-site.xml && sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/core-site.xml > '${hadoop_home_config}'/core-site.xml.tmp && mv -f '${hadoop_home_config}'/core-site.xml.tmp '${hadoop_home_config}'/core-site.xml  && echo  -e '$text' | tee '${hadoop_home_config}'/slaves"
   sudo docker exec -dit hadoop-master-$j /bin/bash -c "sed -i 's/hadoop-master/hadoop-master-'${j}'/g' '${hadoop_home_config}'/yarn-site.xml  && sed -i 's/hadoop-master/hadoop-master-'${j}'/g' '${hadoop_home_config}'/core-site.xml  && echo  -e '$text' | tee '${hadoop_home_config}'/slaves && ./start-hadoop.sh"
    sleep 3

    echo "hadoop-${j} init complete"
    j=$(( $j + 1 ))
    echo -e "\n***********************************\n"

done

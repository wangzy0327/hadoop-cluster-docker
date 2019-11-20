#!/bin/bash

# the default node number is 3
N=${1:-3}

#hadoop home config
hadoop_home_config="/usr/local/hadoop/etc/hadoop"
# start hadoop master container
sudo docker rm -f hadoop-master-0 &> /dev/null
echo "start hadoop-master container..."
sudo docker run -itd \
                --net=hadoop \
                -p 50070:50070 \
                -p 8000:8088 \
                -v /home/wzy/hadoop-cluster-docker/input:/root/input \
                -v /home/wzy/hadoop-cluster-docker/output:/root/output \
                -v /home/wzy/hadoop-cluster-docker/run-wordcount2.sh:/root/run-wordcount2.sh \
                -v /home/wzy/hadoop-cluster-docker/publish:/root/publish \
                -v /home/wzy/hadoop-cluster-docker/subscribe:/root/subscribe \
                --name hadoop-master-0 \
                --hostname hadoop-master-0 \
                kiwenlau/hadoop:1.0 &> /dev/null
#                kiwenlau/hadoop:1.0 &> /dev/null


# start hadoop slave container
i=1
text=""
while [ $i -lt $N ]
do
	sudo docker rm -f hadoop-slave-0-$i &> /dev/null
	echo "start hadoop-slave$i container..."
        if [ $i -eq $[N-1] ]
        then
           text=$text"hadoop-slave-0-"$i
           #text=$text"hadoop-slave"$i
        else
           text=$text"hadoop-slave-0-"$i"\n"
           #text=$text"hadoop-slave"$i"\n"
        fi
	sudo docker run -itd \
	                --net=hadoop \
	                --name hadoop-slave-0-$i \
	                --hostname hadoop-slave-0-$i \
	                kiwenlau/hadoop:1.0 &> /dev/null
#	                kiwenlau/hadoop:1.0 &> /dev/null
	i=$(( $i + 1 ))
done 

echo "____________________________________"
echo -e $text
echo "___________________________________"
#echo $text


# get into hadoop master container
sudo docker exec -it hadoop-slave-0-1 /bin/bash -c "sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/yarn-site.xml > '${hadoop_home_config}'/yarn-site.xml.tmp && mv -f '${hadoop_home_config}'/yarn-site.xml.tmp '${hadoop_home_config}'/yarn-site.xml && sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/core-site.xml > '${hadoop_home_config}'/core-site.xml.tmp && mv -f '${hadoop_home_config}'/core-site.xml.tmp '${hadoop_home_config}'/core-site.xml  && echo  -e '$text' | tee '${hadoop_home_config}'/slaves"
sudo docker exec -it hadoop-slave-0-2 /bin/bash -c "sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/yarn-site.xml > '${hadoop_home_config}'/yarn-site.xml.tmp && mv -f '${hadoop_home_config}'/yarn-site.xml.tmp '${hadoop_home_config}'/yarn-site.xml && sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/core-site.xml > '${hadoop_home_config}'/core-site.xml.tmp && mv -f '${hadoop_home_config}'/core-site.xml.tmp '${hadoop_home_config}'/core-site.xml  && echo  -e '$text' | tee '${hadoop_home_config}'/slaves"
sudo docker exec -it hadoop-master-0 /bin/bash -c "sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/yarn-site.xml > '${hadoop_home_config}'/yarn-site.xml.tmp && mv -f '${hadoop_home_config}'/yarn-site.xml.tmp '${hadoop_home_config}'/yarn-site.xml && sed 's/hadoop-master/hadoop-master-0/g' '${hadoop_home_config}'/core-site.xml > '${hadoop_home_config}'/core-site.xml.tmp && mv -f '${hadoop_home_config}'/core-site.xml.tmp '${hadoop_home_config}'/core-site.xml  && echo  -e '$text' | tee '${hadoop_home_config}'/slaves && ./start-hadoop.sh"

sleep 3

echo "hadoop init complete"

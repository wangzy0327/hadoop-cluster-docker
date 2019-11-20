#!/bin/bash

# test the hadoop cluster by running wordcount

echo "input dir : "$1
echo "output dir : "$2
echo "uuid : "$3

echo -e "\ndelete publish"
sed -i '1d' publish/publish.txt

# create input files 

# create input directory on HDFS
echo -e "\n create input dir on hdfs"
hdfs dfs -mkdir -p $1

# put input files to HDFS
echo -e "\n put input to hdfs"
hdfs dfs -put -f ./$1/* $1

# remove output result
echo -e "\n remove hdfs output file"
hdfs dfs -rm -f -r $2

# run wordcount 
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/sources/hadoop-mapreduce-examples-2.7.2-sources.jar org.apache.hadoop.examples.WordCount $1 $2

# print the input files

echo -e "\ninput :"
hdfs dfs -cat $1/*


# print the output of wordcount
echo -e "\nwordcount output:"
#hdfs dfs -cat $2/*
hdfs dfs -cat $2/part*

echo -e "\nmkdir output.txt:"
touch $2/output.txt

echo -e "\nsave hdfs to disk"
hdfs dfs -cat $2/part* > $2/output.txt


echo -e "\nadd subscribe"
sed -i '$a'"sh run-wordcount2.sh $1 $2 $3" subscribe/subscribe.txt

echo "--------------------end-----------------------------"

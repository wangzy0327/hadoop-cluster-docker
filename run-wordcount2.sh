#!/bin/bash

# test the hadoop cluster by running wordcount

# 定义日志文件路径（UUID作为文件名）
LOG_DIR="logs"
mkdir -p $LOG_DIR  # 确保日志目录存在
LOG_FILE="$LOG_DIR/$3.txt"  # 第三个参数为UUID

echo "input dir : "$1
echo "output dir : "$2
echo "uuid : "$3
echo "日志文件: $LOG_FILE"

echo -e "\ndelete publish"
sed -i '1d' publish/publish.txt

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

# 写入输入内容到日志文件
echo "input :" > $LOG_FILE  # 使用>覆盖，确保文件干净
hdfs dfs -cat $1/* >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE  # 空行分隔

# 写入WordCount输出到日志文件
echo "wordcount output:" >> $LOG_FILE
hdfs dfs -cat $2/part* >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE  # 空行分隔

# 写入操作日志到日志文件
echo "mkdir output.txt:" >> $LOG_FILE
touch $2/output.txt >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE  # 空行分隔

echo "save hdfs to disk" >> $LOG_FILE
(
  flock -x 2
  hdfs dfs -cat $2/part* > $2/output.txt
)2<>$2/output.txt >> $LOG_FILE 2>&1

# 将日志文件路径写入订阅文件，供server.py识别
SUBSCRIBE_FILE="subscribe/subscribe.txt"
(
  flock -x 3
  # 格式：UUID:::日志文件路径（便于server.py解析）
  echo "$3:::$LOG_FILE" >> $SUBSCRIBE_FILE
)3<$SUBSCRIBE_FILE

echo -e "\n结果已保存到: $LOG_FILE"
echo "--------------------end-----------------------------"

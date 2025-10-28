#!/bin/bash
# test hadoop grep: search lines matching a regex

LOG_DIR="logs"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/$3.txt"

echo "input dir : $1"
echo "output dir : $2"
echo "uuid : $3"
echo "日志文件: $LOG_FILE"

# 清理订阅文件
sed -i '1d' publish/publish.txt

# 创建输入目录
echo -e "\n create input dir on hdfs"
hdfs dfs -mkdir -p $1

# 上传输入文件
echo -e "\n put input to hdfs"
hdfs dfs -put -f ./$1/* $1

# 删除输出目录
echo -e "\n remove hdfs output file"
hdfs dfs -rm -f -r $2

# 执行 Grep 示例（查找包含 'error' 或 'fail' 的行）
echo -e "\n running grep example"
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar grep $1 $2 'error|fail|ERROR|FAIL'

# 记录输入内容
echo "input :" > $LOG_FILE
hdfs dfs -cat $1/* >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

# 记录输出结果
echo "grep output:" >> $LOG_FILE
hdfs dfs -cat $2/part* >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

# 保存结果到本地
echo "save hdfs to disk" >> $LOG_FILE
(
  flock -x 2
  hdfs dfs -cat $2/part* > $2/output.txt
)2<>$2/output.txt >> $LOG_FILE 2>&1

# 写入订阅文件
SUBSCRIBE_FILE="subscribe/subscribe.txt"
(
  flock -x 3
  echo "$3:::$LOG_FILE" >> $SUBSCRIBE_FILE
)3<$SUBSCRIBE_FILE

echo -e "\n结果已保存到: $LOG_FILE"
echo "--------------------end-----------------------------"

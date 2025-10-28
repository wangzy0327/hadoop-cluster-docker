#!/bin/bash
# test hadoop randomwriter: generate random data to HDFS

LOG_DIR="logs"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/$3.txt"

echo "output dir : $2"
echo "uuid : $3"
echo "日志文件: $LOG_FILE"

# 清理订阅文件
sed -i '1d' publish/publish.txt

# 删除输出目录
echo -e "\n remove hdfs output file"
hdfs dfs -rm -f -r $2

# 执行 RandomWriter
echo -e "\n running randomwriter"
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar randomwriter $2

# 记录输出（randomwriter 会生成多个 part 文件）
echo "randomwriter output:" > $LOG_FILE
hdfs dfs -ls $2 >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

# 保存部分数据到本地（可选）
echo "save hdfs to disk" >> $LOG_FILE
(
  flock -x 2
  hdfs dfs -cat $2/part* | head -100 > $2/output.txt
)2<>$2/output.txt >> $LOG_FILE 2>&1

# 写入订阅文件
SUBSCRIBE_FILE="subscribe/subscribe.txt"
(
  flock -x 3
  echo "$3:::$LOG_FILE" >> $SUBSCRIBE_FILE
)3<$SUBSCRIBE_FILE

echo -e "\n结果已保存到: $LOG_FILE"
echo "--------------------end-----------------------------"

#!/bin/bash
# test hadoop wordmedian: calculate median word length

LOG_DIR="logs"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/$3.txt"

echo "input dir : $1"
echo "output dir : $2"
echo "uuid : $3"
echo "日志文件: $LOG_FILE"

# 清理订阅文件
sed -i '1d' publish/publish.txt

# 创建输入目录并上传
hdfs dfs -mkdir -p $1
hdfs dfs -put -f ./$1/* $1

# 删除输出目录
hdfs dfs -rm -f -r $2

# 执行 WordMedian
echo -e "\n running wordmedian"
# 使用 tee 同时输出到终端和日志
OUTPUT=$(hadoop jar "$HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar" wordmedian "$1" "$2" 2>&1)
EXIT_CODE=$?

# 输出到终端
echo "$OUTPUT"

#hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar wordmedian $1 $2

# 记录输入和输出（同上）
echo "input :" > $LOG_FILE
hdfs dfs -cat $1/* >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

echo "wordmedian output:" >> $LOG_FILE
hdfs dfs -cat $2/part* >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

# 单独提取最后一行 "The median is: ..." 并明确标记（可选）
MEDIAN_LINE=$(echo "$OUTPUT" | tail -1 | grep "^The median is:")
if [ -n "$MEDIAN_LINE" ]; then
  echo -e "\n✅ $MEDIAN_LINE" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
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

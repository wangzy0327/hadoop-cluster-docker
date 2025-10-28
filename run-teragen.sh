#!/bin/bash
# test hadoop teragen: generate controlled-size data to HDFS

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

# ✅ 使用 teragen 生成指定数量的记录
# 参数说明：teragen <记录数> <输出路径>
# 每条记录约 100 字节，所以：
#   100000 条 ≈ 10MB
#   1000000 条 ≈ 100MB
#   10000000 条 ≈ 1GB
#   100000000 条 ≈ 10GB
echo -e "\n running teragen to generate 1GB data"
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar teragen \
  -D mapreduce.job.name=teragen-$3 \
  10000000 $2  # 生成 10,000 条记录 ≈ 10MB

# 记录输出
echo "teragen output:" > $LOG_FILE
hdfs dfs -ls $2 >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

# 获取总大小
echo "Generated data size:" >> $LOG_FILE
hdfs dfs -du -h $2 >> $LOG_FILE 2>&1
echo "" >> $LOG_FILE

# 保存部分数据到本地
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

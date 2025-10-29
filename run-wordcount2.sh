#!/bin/bash

# test the hadoop cluster by running wordcount

# 定义日志文件路径（UUID作为文件名）
LOG_DIR="logs"
mkdir -p $LOG_DIR  # 确保日志目录存在
LOG_FILE="$LOG_DIR/$3.txt"  # 第三个参数为UUID

# =================== 关键修改：自定义日志格式（仅保留时:分:秒） ===================
# 创建临时 log4j 配置文件
LOG4J_CONF="hadoop-log4j.conf"
cat > "$LOG4J_CONF" << 'EOF'
# 设置根日志器，输出到控制台
log4j.rootLogger=INFO, console

# 定义控制台输出器
log4j.appender.console=org.apache.log4j.ConsoleAppender
log4j.appender.console.target=System.err
log4j.appender.console.layout=org.apache.log4j.PatternLayout

# 关键：仅输出 时间(时:分:秒) + 日志级别 + 消息
# %d{HH:mm:ss} 表示只输出 时:分:秒
# %p 是日志级别 (INFO, WARN, ERROR)
# %m 是消息内容
# %n 是换行
log4j.appender.console.layout.ConversionPattern=%d{HH:mm:ss} %p %m%n
EOF

# 关键：全局设置HADOOP_OPTS，覆盖所有Hadoop命令的log4j配置
export HADOOP_OPTS="-Dlog4j.configuration=file:./$LOG4J_CONF"

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

#!/bin/bash
# test hadoop pi estimator: Monte Carlo estimation of π

LOG_DIR="logs"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/$3.txt"

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

echo "output dir : $2"
echo "uuid : $3"
echo "日志文件: $LOG_FILE"

# 清理订阅文件
sed -i '1d' publish/publish.txt

# 删除输出目录（pi 示例不需要输入）
echo -e "\n remove hdfs output file"
hdfs dfs -rm -f -r $2

# 执行 Pi 估算（10 个 Map，每个投 1000000 点）
echo -e "\n running pi estimation"
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar pi -Dmapreduce.job.name=pi-$3 10 1000000 | tee $LOG_FILE

# Pi 示例直接输出到终端，不写入 HDFS，但仍记录日志
echo "Pi estimation result saved to log." >> $LOG_FILE

# 写入订阅文件（即使没有 HDFS 输出）
SUBSCRIBE_FILE="subscribe/subscribe.txt"
(
  flock -x 3
  echo "$3:::$LOG_FILE" >> $SUBSCRIBE_FILE
)3<$SUBSCRIBE_FILE

echo -e "\n结果已保存到: $LOG_FILE"
echo "--------------------end-----------------------------"


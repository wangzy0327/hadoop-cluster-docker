#!/bin/bash
# 用法：./run-sort3.sh <本地文本目录> <HDFS输入目录> <HDFS输出目录> <uuid>
# 示例：./run-sort3.sh ./local-text-data input/input-sort-text output/output-sort-text wzy-sort-text

# 检查参数
if [ $# -ne 4 ]; then
  echo "用法错误：$0 <本地文本目录> <HDFS输入目录> <HDFS输出目录> <uuid>"
  exit 1
fi

LOCAL_TEXT_DIR="$1"
HDFS_IN="$2"
HDFS_OUT="$3"
UUID="$4"
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/$UUID.txt"
LOCAL_RESULT="./sort-results/$UUID/sorted-text.txt"
mkdir -p "$(dirname "$LOCAL_RESULT")"

# 定义队列路径（与server.py保持一致）
PUBLISH_FILE="publish/publish.txt"
SUBSCRIBE_FILE="subscribe/subscribe.txt"

# 清空日志文件
> "$LOG_FILE"

# 记录基本信息
echo "local text data: $LOCAL_TEXT_DIR" > "$LOG_FILE"
echo "HDFS input dir: $HDFS_IN" >> "$LOG_FILE"
echo "HDFS output dir: $HDFS_OUT" >> "$LOG_FILE"
echo "UUID: $UUID"
echo "日志文件: $LOG_FILE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 清理发布队列（移除首行，与示例保持一致）
echo "清理发布队列..."
sed -i '1d' "$PUBLISH_FILE" >> "$LOG_FILE" 2>&1

# 1. 生成/复用本地文本
if [ ! -d "$LOCAL_TEXT_DIR" ] || [ -z "$(ls -A "$LOCAL_TEXT_DIR")" ]; then
  echo "生成本地文本数据..."
  mkdir -p "$LOCAL_TEXT_DIR"
  for i in $(seq 1 10000); do
    echo "$i,$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)"
  done > "$LOCAL_TEXT_DIR/text-data.txt"
else
  echo "复用本地文本数据..."
fi

# 写入日志
echo "=== 本地文本目录内容 ===" >> "$LOG_FILE"
ls -lh "$LOCAL_TEXT_DIR" >> "$LOG_FILE" 2>&1
echo "" >> "$LOG_FILE"

# 2. 上传到HDFS
echo "上传文本到HDFS..."
echo "upload to HDFS..." >> "$LOG_FILE"
hdfs dfs -mkdir -p "$HDFS_IN"
hdfs dfs -put -f "$LOCAL_TEXT_DIR"/* "$HDFS_IN/" 2>&1
hdfs dfs -ls "$HDFS_IN" 2>&1
echo "" >> "$LOG_FILE"

# 3. 清理旧输出
echo "清理HDFS输出..."
echo "clean HDFS output..." >> "$LOG_FILE"
hdfs dfs -rm -f -r "$HDFS_OUT" 2>&1
echo "" >> "$LOG_FILE"

# 4. 执行排序
echo "执行文本排序..."
echo "执行文本排序..." >> "$LOG_FILE"
hadoop jar "$HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.2.jar" sort \
  -D mapreduce.job.name=text-sort-"$UUID" \
  -D mapreduce.map.input.format.class=org.apache.hadoop.mapreduce.lib.input.KeyValueTextInputFormat \
  -D mapreduce.input.keyvaluelinerecordreader.key.value.separator=@@@@@ \
  -D mapreduce.output.format.class=org.apache.hadoop.mapreduce.lib.output.TextOutputFormat \
  -D mapreduce.map.output.key.class=org.apache.hadoop.io.Text \
  -D mapreduce.map.output.value.class=org.apache.hadoop.io.Text \
  -D mapreduce.reduce.output.key.class=org.apache.hadoop.io.Text \
  -D mapreduce.reduce.output.value.class=org.apache.hadoop.io.Text \
  -inFormat org.apache.hadoop.mapreduce.lib.input.KeyValueTextInputFormat \
  -outFormat org.apache.hadoop.mapreduce.lib.output.TextOutputFormat \
  "$HDFS_IN" "$HDFS_OUT" \
  2>&1

SORT_EXIT_CODE=$?

# 5. 检查结果并输出
if [ $SORT_EXIT_CODE -eq 0 ]; then
  echo -e "\n✅ 排序成功！"
  echo "✅ 排序成功！" >> "$LOG_FILE"

  # 获取前20行排序结果（只取 key 部分）
  echo -e "\n=== 前20行排序结果（文本格式）==="
  echo -e "\n=== 前20行排序结果（文本格式）===" >> "$LOG_FILE"

  sorted_lines=$(hdfs dfs -cat "$HDFS_OUT"/part-* 2>/dev/null | head -20 | awk '{print $1}')

  # 输出到终端
  echo "$sorted_lines"
  # 写入日志文件
  echo "$sorted_lines" >> "$LOG_FILE"

  # 保存完整结果到本地（加文件锁避免并发写入冲突）
  echo -e "\n保存完整结果到本地..."
  (
    flock -x 2  # 排他锁，确保写入原子性
    hdfs dfs -cat "$HDFS_OUT"/part-* 2>/dev/null | awk '{print $1}' > "$LOCAL_RESULT"
  ) 2<> "$LOCAL_RESULT" >> "$LOG_FILE" 2>&1  # 锁文件与输出文件绑定

  echo -e "\n✅ 完整排序结果已保存到本地：$LOCAL_RESULT"
  echo "本地完整结果：$LOCAL_RESULT" >> "$LOG_FILE"
else
  echo -e "\n❌ 排序失败！"
  echo "❌ 排序失败！请检查 Hadoop 环境或 JAR 路径。" >> "$LOG_FILE"
fi

# 6. 写入订阅队列（加文件锁确保原子写入，避免多行混杂）
echo -e "\n写入订阅队列..."
(
  flock -x 3  # 排他锁，防止多任务同时写入订阅文件
  echo "$UUID:::$LOG_FILE" >> "$SUBSCRIBE_FILE"
) 3< "$SUBSCRIBE_FILE"  # 锁文件与订阅文件绑定

echo "订阅信息已写入: $SUBSCRIBE_FILE" >> "$LOG_FILE"
echo -e "\n结果已保存到: $LOG_FILE"
echo "-------------------- 结束 --------------------"

exit $SORT_EXIT_CODE

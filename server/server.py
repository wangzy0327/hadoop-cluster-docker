#coding:utf-8
import subprocess  # 保留并统一使用subprocess
import os
import requests
import threading
import logging
import sys
import codecs  # 补充codecs模块导入（原代码中使用但未导入）
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
import uuid
import time
import re
import traceback

# 修复中文编码问题：强制stdout/stderr使用UTF-8
try:
    sys.stdout.buffer.write('\ufffd'.encode('utf-8'))  # 测试编码支持
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
except Exception as e:
    logging.warning(f"编码配置失败: {str(e)}")  # 补充异常捕获并日志记录

# 配置日志（时间格式改为时分秒）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',  # 只显示时分秒
    handlers=[
        logging.FileHandler("server.log", encoding='utf-8'),  # 日志文件强制UTF-8
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)
# 配置参数
PUBLISH_QUEUE = "/home/wzy/hadoop-cluster-docker/publish/publish.txt"
SUBSCRIBE_QUEUE = "/home/wzy/hadoop-cluster-docker/subscribe/subscribe.txt"
MAX_HADOOP_GROUPS = 6  # 最大容器组数量
CHECK_INTERVAL = 10  # 监控间隔（秒）
# 创建线程池控制并发任务数
executor = ThreadPoolExecutor(max_workers=10)


class ClusterManager:
    """Hadoop集群动态扩缩容管理器"""
    def __init__(self):
        self.task_queue = []  # 内存任务队列
        self.lock = threading.Lock()  # 线程安全锁

    def get_task_count(self):
        """获取任务队列中的任务数量"""
        with self.lock:
            return len(self.task_queue)

    def get_hadoop_count(self):
        """获取当前运行的Hadoop容器组数量"""
        try:
            # 修复text参数问题，使用universal_newlines替代
            output = subprocess.check_output(
                "docker ps | grep hadoop-master | wc -l",
                shell=True,
                stderr=subprocess.STDOUT,
                universal_newlines=True  # 兼容旧版本Python，返回字符串
            )
            return int(output.strip())
        except subprocess.CalledProcessError as e:
            # 捕获命令执行失败异常（返回非0退出码）
            logger.error(f"获取Hadoop容器数量命令执行失败: {e.returncode}, 输出: {e.output}")
            return 1
        except Exception as e:
            logger.error(f"获取Hadoop容器数量失败: {str(e)}")
            return 1

    def extend_cluster(self, target_num):
        """扩容Hadoop集群到目标数量"""
        if target_num > MAX_HADOOP_GROUPS:
            target_num = MAX_HADOOP_GROUPS
        current_num = self.get_hadoop_count()
        if target_num > current_num:
            logger.info(f"扩容集群: {current_num} -> {target_num}")
            try:
                # 使用universal_newlines替代text参数
                result = subprocess.run(
                    f"sh /home/wzy/hadoop-cluster-docker/extend-container.sh {target_num}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    timeout=300  # 增加超时控制（5分钟）
                )
                if result.returncode != 0:
                    logger.error(f"扩容脚本执行失败，退出码: {result.returncode}, 输出: {result.stdout}")
                else:
                    logger.info(f"扩容脚本执行成功，输出: {result.stdout}")
                time.sleep(5)
            except subprocess.TimeoutExpired:
                logger.error(f"扩容脚本执行超时（超过5分钟）")
            except Exception as e:
                logger.error(f"扩容集群失败: {str(e)}")

    def reduce_cluster(self, target_num):
        """缩容Hadoop集群到目标数量"""
        if target_num < 1:
            target_num = 1
        current_num = self.get_hadoop_count()
        if target_num < current_num:
            logger.info(f"缩容集群: {current_num} -> {target_num}")
            try:
                # 使用universal_newlines替代text参数
                result = subprocess.run(
                    f"sh /home/wzy/hadoop-cluster-docker/reduce-container.sh {target_num}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    timeout=300
                )
                if result.returncode != 0:
                    logger.error(f"缩容脚本执行失败，退出码: {result.returncode}, 输出: {result.stdout}")
                else:
                    logger.info(f"缩容脚本执行成功，输出: {result.stdout}")
                time.sleep(5)
            except subprocess.TimeoutExpired:
                logger.error(f"缩容脚本执行超时（超过5分钟）")
            except Exception as e:
                logger.error(f"缩容集群失败: {str(e)}")

    def add_task(self, task):
        """添加任务到队列"""
        with self.lock:
            self.task_queue.append(task)

    def remove_task(self, uuid):
        """从队列移除已完成任务"""
        with self.lock:
            self.task_queue = [t for t in self.task_queue if t['uuid'] != uuid]

    def monitor_and_adjust(self):
        """监控任务队列并动态调整集群规模"""
        while True:
            task_count = self.get_task_count()
            current_groups = self.get_hadoop_count()
            logger.info(f"当前任务数: {task_count}, 当前容器组数: {current_groups}")

            # 扩容策略
            if task_count > current_groups:
                self.extend_cluster(task_count)
            # 缩容策略
            elif task_count < current_groups // 2 and current_groups > 1:
                self.reduce_cluster(max(1, task_count))

            time.sleep(CHECK_INTERVAL)

    def process_tasks(self):
        """处理队列中的任务"""
        while True:
            with self.lock:
                tasks = list(self.task_queue)  # 复制当前任务列表（避免迭代中修改）

            for task in tasks:
                try:
                    # 执行Hadoop任务（后台执行，不阻塞）
                    cmd = f"docker exec -d {task['container']} bash -c '{task['command']}'"
                    logger.info(f"执行任务: {cmd}")
                    # 使用universal_newlines替代text参数
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        timeout=60  # 执行命令超时控制（1分钟）
                    )
                    if result.returncode != 0:
                        logger.error(f"任务启动失败，退出码: {result.returncode}, 输出: {result.stdout}")
                        self.send_callback(task['callback_url'], task['uuid'], False, f"任务启动失败: {result.stdout}")
                        self.remove_task(task['uuid'])
                        continue
                    
                    # 监控任务完成状态
                    self.monitor_task_completion(task)
                    
                except subprocess.TimeoutExpired:
                    logger.error(f"任务启动命令超时（超过1分钟）: {task['uuid']}")
                    self.send_callback(task['callback_url'], task['uuid'], False, "任务启动超时")
                    self.remove_task(task['uuid'])
                except Exception as e:
                    logger.error(f"任务处理失败 {task['uuid']}: {str(e)}")
                    self.send_callback(task['callback_url'], task['uuid'], False, str(e))
                    self.remove_task(task['uuid'])

            time.sleep(2)  # 检查间隔

    def monitor_task_completion(self, task):
        """监控任务完成状态并从独立日志文件提取结果（修复路径重复问题）"""
        max_wait_time = 3600  # 最大等待时间(秒)
        check_interval = 5     # 检查间隔(秒)
        start_time = time.time()
        # 定义日志目录的绝对路径（根据实际目录结构计算）
        # server.py位于/home/wzy/hadoop-cluster-docker/server
        # logs目录位于/home/wzy/hadoop-cluster-docker
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        LOGS_ABS_DIR = os.path.join(BASE_DIR, "logs")
        logger.info(f"日志文件根目录: {LOGS_ABS_DIR}")

        while time.time() - start_time < max_wait_time:
            if os.path.exists(SUBSCRIBE_QUEUE):
                try:
                    with open(SUBSCRIBE_QUEUE, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 查找格式：UUID:::日志文件路径
                        pattern = f"{task['uuid']}:::(.*?)\n"
                        log_match = re.search(pattern, content, re.DOTALL)
                        
                        if log_match:
                            # 获取相对路径或文件名
                            log_file_rel_path = log_match.group(1).strip()
                            
                            # 关键修复：移除路径中可能包含的"logs/"前缀
                            # 防止与LOGS_ABS_DIR拼接后出现重复的logs目录
                            log_file_rel_path = re.sub(r'^logs\/', '', log_file_rel_path)
                            
                            # 拼接绝对路径
                            if os.path.isabs(log_file_rel_path):
                                log_file_path = log_file_rel_path
                            else:
                                log_file_path = os.path.join(LOGS_ABS_DIR, log_file_rel_path)
                            
                            logger.info(f"尝试读取日志文件: {log_file_path}")
                            
                            # 检查日志文件是否存在且非空
                            if os.path.exists(log_file_path):
                                if os.path.getsize(log_file_path) > 0:
                                    with open(log_file_path, 'r', encoding='utf-8') as log_f:
                                        result_msg = log_f.read().strip()
                                    
                                    logger.info(f"任务完成: {task['uuid']}, 成功提取结果")
                                    self.send_callback(
                                        task['callback_url'], 
                                        task['uuid'], 
                                        True, 
                                        result_msg
                                    )
                                    self.remove_task(task['uuid'])
                                    return
                                else:
                                    logger.info(f"日志文件存在但为空: {log_file_path}，等待重试...")
                            else:
                                logger.info(f"日志文件尚未生成: {log_file_path}，等待重试...")
                except Exception as e:
                    logger.error(f"处理订阅文件失败: {str(e)}")
                    time.sleep(check_interval)
                    continue
            time.sleep(check_interval)

        # 超时处理
        logger.error(f"任务超时 {task['uuid']}")
        self.send_callback(
            task['callback_url'], 
            task['uuid'], 
            False, 
            "任务执行超时（超过1小时）"
        )
        self.remove_task(task['uuid'])

    def send_callback(self, url, uuid, success, message):
        """发送回调结果给轻容器"""
        try:
            data = {
                "uuid": uuid,
                "success": success,
                "message": message,
                "timestamp": time.strftime("%H:%M:%S")  # 时间格式改为时分秒
            }
            response = requests.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()  # 触发HTTP错误（如4xx/5xx）
            logger.info(f"回调结果发送成功 {uuid}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"回调结果发送失败 {uuid}: {str(e)}")
        except Exception as e:
            logger.error(f"回调处理异常 {uuid}: {str(e)}")


def parse_shell(shcmd):
    """Execute command and parse output"""
    try:
        logger.info("Executing command: %s" % shcmd)
        # 使用universal_newlines替代text参数
        p = subprocess.Popen(
            shcmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8'
        )
        # 超时控制（5分钟）
        stdout, stderr = p.communicate(timeout=300)
        combined = stdout + "\n" + stderr

        if p.returncode != 0:
            logger.error("Command failed (return code: %s), output: %s" % (p.returncode, combined))
            return False, combined
        else:
            logger.info("Command executed successfully, return code: %s" % p.returncode)

        # Extract model information
        pattern = r"(I\d{4} \d{2}:\d{2}:\d{2}\.\d{6} +\d+ caffe\.cpp:495\] execution time: .*? us)"
        match = re.search(pattern, combined, re.DOTALL | re.IGNORECASE)

        if match:
            model_info = match.group(0).strip()
            logger.info("Extracted model info: %s" % model_info)
            return True, model_info
        else:
            logger.warning("No execution time found, returning full output")
            return True, combined

    except subprocess.TimeoutExpired:
        p.kill()
        # 确保读取剩余输出（避免僵尸进程）
        stdout, stderr = p.communicate()
        error_msg = f"Command timed out (5 minutes), partial output: {stdout}\n{stderr}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = "Command execution error: %s" % str(e)
        logger.error(error_msg)
        logger.error("Traceback: %s" % traceback.format_exc())
        return False, error_msg


def async_process_task(input_path, output_path, uuid_str, callback_url):
    """Process task asynchronously"""
    try:
        logger.info("[Async Task] Starting processing UUID: %s" % uuid_str)
        logger.info("[Async Task] Input path: %s, Output path: %s" % (input_path, output_path))

        # Execute inference command
        inference_cmd = "cd /opt/cambricon/caffe/src/caffe && bash gen_offline_model.sh"
        success, result_output = parse_shell(inference_cmd)
        
        # Build task result
        task_result = {
            "status": "success" if success else "failed",
            "cmd": inference_cmd,
            "output": result_output,
            "input_path": input_path,
            "output_path": output_path,
            "execution_time": time.strftime("%H:%M:%S")  # 时间格式改为时分秒
        }

        # Callback to client
        if callback_url:
            logger.info("[Async Task] Calling back client: %s" % callback_url)
            callback_data = {
                "uuid": uuid_str,
                "task_status": task_result["status"],
                "result": task_result
            }

            response = requests.post(
                url=callback_url,
                json=callback_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            logger.info("[Async Task] Callback completed, status code: %s, response: %s" % (response.status_code, response.text))
        else:
            logger.warning("[Async Task] No callback URL provided, skipping callback")

    except requests.exceptions.RequestException as e:
        error_msg = f"Callback request failed: {str(e)}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = "Task processing error: %s" % str(e)
        logger.error(error_msg)
        logger.error("Traceback: %s" % traceback.format_exc())
        if callback_url:
            try:
                requests.post(
                    url=callback_url,
                    json={
                        "uuid": uuid_str,
                        "task_status": "error",
                        "error_msg": error_msg
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            except Exception as ce:
                logger.error("Failed to send error callback: %s" % str(ce))
    finally:
        logger.info("[Async Task] Processing finished UUID: %s" % uuid_str)


# 初始化集群管理器并启动后台线程
cluster_manager = ClusterManager()

# 启动集群监控线程
monitor_thread = threading.Thread(target=cluster_manager.monitor_and_adjust, daemon=True)
monitor_thread.start()

# 启动任务处理线程
task_thread = threading.Thread(target=cluster_manager.process_tasks, daemon=True)
task_thread.start()


@app.route('/pipeline', methods=['POST'])
def handle_pipeline():
    try:
        data = request.get_json()
        logger.info("Received /pipeline request: %s" % data)

        # 检查参数是否存在（避免KeyError）
        ipy_path = data.get("ipy_path")
        pipeline_name = data.get("pipeline")
        if not ipy_path or not pipeline_name:
            error_msg = "Missing parameters: 'ipy_path' and 'pipeline' are required"
            logger.error(error_msg)
            return error_msg, 400
        logger.info("ipy_path: %s, pipeline_name: %s" % (ipy_path, pipeline_name))

        root_path = "/home/pipeline_server/shells/"
        cmd = "%sstart.sh %s" % (root_path, ipy_path)
        # 使用universal_newlines替代text参数
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8',
            timeout=300  # 5分钟超时
        )
        return jsonify({
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout + result.stderr
        })

    except KeyError as e:
        error_msg = "Missing parameter: %s" % e
        logger.error(error_msg)
        return error_msg, 400
    except Exception as e:
        error_msg = "Server error: %s" % str(e)
        logger.error(error_msg)
        logger.error("Traceback: %s" % traceback.format_exc())
        return error_msg, 500


@app.route('/micro', methods=['POST'])
def handle_micro():
    try:
        # Log request details
        logger.info("Received /micro request, headers: %s" % request.headers)
        data = request.get_json()
        if not data:
            data = request.form  # Compatible with form-data
        logger.info("Received /micro request data: %s" % data)

        # Validate required parameters
        required_params = ["input", "callback_url"]
        for param in required_params:
            if param not in data:
                error_msg = "Missing parameter: %s" % param
                logger.error(error_msg)
                return error_msg, 400

        input_path = data["input"]
        output_path = data.get("output", "")
        callback_url = data["callback_url"]

        # Generate UUID
        uuid_str = str(uuid.uuid1())
        logger.info("Generated UUID: %s" % uuid_str)

        # Submit async task
        executor.submit(
            async_process_task,
            input_path,
            output_path,
            uuid_str,
            callback_url
        )

        return uuid_str

    except KeyError as e:
        error_msg = "Missing parameter: %s" % e
        logger.error(error_msg)
        return error_msg, 400
    except Exception as e:
        error_msg = "Server error: %s" % str(e)
        logger.error(error_msg)
        logger.error("Traceback: %s" % traceback.format_exc())
        return error_msg, 500


@app.route('/hadoop', methods=['POST'])
def handler_hadoop():
    """处理Hadoop任务提交（写入任务队列）"""
    try:
        data = request.get_json()
        logger.info(f"Received /hadoop request: {data}")

        required = ["input", "output", "callback_url"]
        for param in required:
            if param not in data:
                return f"缺少参数: {param}", 400

        uuid_str = str(uuid.uuid1())
        # 获取可用的容器
        container = "hadoop-master-0"
        
        # 添加任务到队列
        cluster_manager.add_task({
            "uuid": uuid_str,
            "command": f"sh /root/run-wordcount2.sh {data['input']} {data['output']} {uuid_str}",
            "container": container,
            "callback_url": data["callback_url"],
            "timestamp": time.time()
        })

        return jsonify({"uuid": uuid_str})

    except Exception as e:
        logger.error(f"/hadoop 错误: {str(e)}")
        return str(e), 500

if __name__ == "__main__":
    logger.info("Starting MLU inference server...")
    app.run(
        debug=False,
        threaded=True,
        host="0.0.0.0",
        port=8800
    )


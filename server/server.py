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

# -------------------------- 修复：适配Werkzeug 1.0.1，自定义访问日志格式 --------------------------
import time
from flask import request, g

# 1. 禁用Flask默认的访问日志（避免重复输出，且默认日志含年月日）
# 获取werkzeug的日志记录器，设置级别为WARNING，不输出INFO级别的访问日志
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)

# 2. 在请求开始时记录开始时间（用于计算耗时）
@app.before_request
def record_start_time():
    g.start_time = time.time()  # 将开始时间存入g对象（请求上下文共享）

# 3. 在请求结束后，自定义输出访问日志（仅含时分秒）
@app.after_request
def custom_access_log(response):
    # 跳过Flask自身的健康检查请求（如/favicon.ico），避免无用日志
    if request.path == '/favicon.ico':
        return response

    # 计算请求耗时（毫秒）
    elapsed_time = (time.time() - g.start_time) * 1000

    # 获取日志所需字段
    current_time = time.strftime('%H:%M:%S')  # 仅时分秒
    remote_addr = request.remote_addr  # 客户端IP
    request_line = f"{request.method} {request.path} {request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1')}"  # 请求行（如POST /hadoop HTTP/1.1）
    status_code = response.status_code  # 响应状态码（如200）
    content_length = response.headers.get('Content-Length', '-')  # 响应长度

    # 自定义日志格式（与业务日志时间格式统一）
    log_msg = f"{current_time} - INFO - [访问日志] {remote_addr} - \"{request_line}\" {status_code} {content_length} - {elapsed_time:.2f}ms"
    
    # 输出日志（使用自定义的logger，确保格式统一）
    logger.info(log_msg)

    return response
# -----------------------------------------------------------------------------------

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

    def is_container_available(self, container_name):
        """检查容器是否已启动且Hadoop服务正常（避免分配未初始化的容器）"""
        try:
            # 1. 检查容器是否在运行中
            container_running = subprocess.run(
                f"docker inspect --format '{{{{.State.Running}}}}' {container_name}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            ).stdout.strip() == "true"
            if not container_running:
                logger.info(f"容器 {container_name} 未运行，跳过分配")
                return False

            # 2. 增加内部重试：等待Hadoop启动（最多重试5次，每次间隔2秒）
            hadoop_running = False
            for _ in range(5):
                result = subprocess.run(
                    f"docker exec {container_name} jps | grep NameNode",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8'
                )
                if result.returncode == 0:
                    hadoop_running = True
                    break
                time.sleep(2)  # 等待2秒后重试

            if not hadoop_running:
                logger.info(f"容器 {container_name} 内Hadoop未启动（重试5次后仍失败），跳过分配")
                return False

            return True
        except Exception as e:
            logger.warning(f"检查容器 {container_name} 可用性失败: {str(e)}")
            return False
        
    def update_available_containers(self):
        """更新可用容器列表（仅保留运行中且Hadoop正常的容器）"""
        try:
            # 获取所有 hadoop-master 容器
            all_masters = subprocess.check_output(
                "docker ps --filter 'name=hadoop-master-' --format '{{.Names}}' | sort",
                shell=True,
                encoding='utf-8'
            ).splitlines()
            # 过滤可用容器
            self.available_containers = [
                master for master in all_masters 
                if self.is_container_available(master)
            ]
            logger.info(f"更新可用容器列表: {self.available_containers}")
        except Exception as e:
            logger.error(f"更新可用容器列表失败: {str(e)}")
            self.available_containers = ["hadoop-master-0"]  # 兜底

    def reassign_pending_tasks(self):
        """重新分配队列中未执行的任务到新容器（扩容后调用）"""
        with self.lock:
            # 先更新可用容器列表
            self.update_available_containers()
            if len(self.available_containers) <= 1:
                return  # 仅1个容器，无需重分配

            # 遍历任务队列，重分配未执行的任务
            for idx, task in enumerate(self.task_queue):
                # 仅重分配绑定到旧容器（hadoop-master-0）且未执行的任务
                if task.get("container") == "hadoop-master-0":
                    # 轮询分配到新容器（基于任务索引取模，避免集中）
                    new_container = self.available_containers[idx % len(self.available_containers)]
                    logger.info(f"任务 {task['uuid']} 从 hadoop-master-0 重分配到 {new_container}")
                    self.task_queue[idx]["container"] = new_container  # 更新任务的容器字段        
        
    def extend_cluster(self, target_num):
        """扩容Hadoop集群到目标数量"""
        if target_num > MAX_HADOOP_GROUPS:
            target_num = MAX_HADOOP_GROUPS
        current_num = self.get_hadoop_count()
        if target_num > current_num:
            logger.info(f"扩容集群: {current_num} -> {target_num}")
            try:
                result = subprocess.run(
                    f"bash /home/wzy/hadoop-cluster-docker/extend-container2.sh {target_num}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    timeout=300
                )
                if result.returncode != 0:
                    logger.error(f"扩容脚本执行失败，退出码: {result.returncode}, 输出: {result.stdout}")
                else:
                    logger.info(f"扩容脚本执行成功，输出: {result.stdout}")
                    # 扩容完成后，等待新容器Hadoop启动
                    time.sleep(10)
                    # 主动检查新容器可用性
                    new_masters = [f"hadoop-master-{i}" for i in range(current_num, target_num)]
                    for master in new_masters:
                        if self.is_container_available(master):
                            logger.info(f"新容器 {master} 已就绪，可分配任务")
                        else:
                            logger.warning(f"新容器 {master} 尚未就绪，需等待Hadoop启动")
                    # 核心新增：重分配队列中未执行的任务
                    self.reassign_pending_tasks()
            except subprocess.TimeoutExpired:
                logger.error(f"扩容脚本执行超时（超过5分钟）")
            except Exception as e:
                logger.error(f"扩容集群失败: {str(e)}")

    def get_tasks_running_containers(self):
        """获取正在运行任务的容器列表"""
        with self.lock:
            # 收集所有状态为 running 的任务绑定的容器
            running_containers = set()
            for task in self.task_queue:
                if task.get("status") == "running":
                    running_containers.add(task["container"])
            return list(running_containers)

    def reduce_cluster(self, target_num):
        """缩容Hadoop集群到目标数量（仅在任务列表为空时执行）"""
        # 关键修复：检查任务列表是否为空，非空则不执行缩容
        with self.lock:
            if len(self.task_queue) > 0:
                logger.info(f"任务列表非空（{len(self.task_queue)}个任务），不执行缩容")
                return

        if target_num < 1:
            target_num = 1
        current_num = self.get_hadoop_count()
        if target_num >= current_num:
            logger.info(f"目标数量{target_num}不小于当前数量{current_num}，不执行缩容")
            return

        logger.info(f"任务列表为空，执行缩容集群: {current_num} -> {target_num}")
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
        """监控任务队列并动态调整集群规模（修改缩容触发条件)"""
        while True:
            task_count = self.get_task_count()
            current_groups = self.get_hadoop_count()
            logger.info(f"当前任务数: {task_count}, 当前容器组数: {current_groups}")

            # 扩容策略
            if task_count > current_groups:
                self.extend_cluster(task_count)
            # 缩容策略修改：仅当任务数为0时才考虑缩容
            elif task_count == 0 and current_groups > 1:
                # 任务为空时缩容到1个容器组（或根据实际需求调整）
                self.reduce_cluster(1)

            time.sleep(CHECK_INTERVAL)

    def process_tasks(self):
        """处理队列中的任务 （并行监控，非阻塞）"""
        while True:
            with self.lock:
                # 只取未启动的任务（新增任务状态标记，避免重复启动）
                pending_tasks = [t for t in self.task_queue if t.get("status") != "running"]
                # 标记任务为已启动（避免重复处理）
                for task in pending_tasks:
                    task["status"] = "running"

            for task in pending_tasks:
                try:
                    # 1. 启动任务（后台执行）
                    cmd = f"docker exec -d {task['container']} bash -c '{task['command']}'"
                    logger.info(f"执行任务: {cmd}")
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                        timeout=60
                    )
                    if result.returncode != 0:
                        logger.error(f"任务启动失败 {task['uuid']}: {result.stdout}")
                        task["status"] = "failed"
                        self.send_callback(...)
                        self.remove_task(task['uuid'])
                        continue

                    # 2. 关键修复：用线程池并行监控任务完成（非阻塞）
                    executor.submit(
                        self.monitor_task_completion,  # 提交监控逻辑到线程池
                        task
                    )

                except Exception as e:
                    logger.error(f"任务处理失败 {task['uuid']}: {str(e)}")
                    task["status"] = "failed"
                    self.send_callback(...)
                    self.remove_task(task['uuid'])

            time.sleep(2)  # 降低循环频率，减少资源占用

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

    def send_callback(self, url, uuid, success, message, max_retries=3, retry_interval=5):
        """发送回调结果，支持失败重试"""
        for attempt in range(max_retries):
            try:
                data = {
                    "uuid": uuid,
                    "success": success,
                    "message": message,
                    "timestamp": time.strftime("%H:%M:%S")
                }
                response = requests.post(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10  # 单次请求超时10秒
                )
                response.raise_for_status()
                logger.info(f"回调结果发送成功（第{attempt+1}次） {uuid}: {response.status_code}")
                return  # 成功则退出重试
            except requests.exceptions.RequestException as e:
                logger.warning(f"回调结果发送失败（第{attempt+1}次） {uuid}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)  # 重试间隔5秒
        # 所有重试失败
        logger.error(f"回调结果发送失败（已重试{max_retries}次） {uuid}")


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
        selected_master = None
        retry_count = 0
        max_retry = 5  # 增加重试次数
        retry_interval = 5

        while retry_count < max_retry and not selected_master:
            try:
                # 调用 ClusterManager 的方法更新可用容器列表
                cluster_manager.update_available_containers()
                available_masters = cluster_manager.available_containers
                if not available_masters:
                    logger.warning(f"第{retry_count+1}次尝试：无可用容器")
                    retry_count += 1
                    time.sleep(retry_interval)
                    continue

                # 新任务优先分配到“非hadoop-master-0”的容器（负载均衡）
                # 过滤出除 hadoop-master-0 外的可用容器
                non_default_masters = [m for m in available_masters if m != "hadoop-master-0"]
                if non_default_masters:
                    # 新任务分配到非默认容器（轮询）
                    task_count = cluster_manager.get_task_count()
                    selected_master = non_default_masters[task_count % len(non_default_masters)]
                else:
                    # 仅默认容器可用，分配到 hadoop-master-0
                    selected_master = available_masters[0]

                logger.info(f"新任务 {uuid_str} 分配到容器: {selected_master}（可用容器：{available_masters}）")

            except Exception as e:
                logger.warning(f"第{retry_count+1}次尝试获取容器失败: {str(e)}")
                retry_count += 1
                time.sleep(retry_interval)

        # 兜底：若重试失败，使用默认容器
        if not selected_master:
            selected_master = "hadoop-master-0"
            logger.warning(f"所有重试失败，新任务 {uuid_str} 分配到默认容器: {selected_master}")

        # 添加任务到队列
        cluster_manager.add_task({
            "uuid": uuid_str,
            "command": f"sh /root/run-wordcount2.sh {data['input']} {data['output']} {uuid_str}",
            "container": selected_master,  # 绑定到新选择的容器
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


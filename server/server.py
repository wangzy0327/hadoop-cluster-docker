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
        self.request_count = 0  # 新增：记录总请求数
        self.start_time = time.time()  # 新增：服务启动时间戳
        # IP请求计数字典，key=客户端IP，value=请求次数
        self.ip_request_count = {}  # 格式示例：{"192.168.1.100": 5, "10.0.0.5": 3}

    def get_task_count(self):
        """获取任务队列中的任务数量"""
        with self.lock:
            return len(self.task_queue)

    # def increment_request_count(self):
    #     """新增：请求计数加1（线程安全）"""
    #     with self.lock:
    #         self.request_count += 1
            
    def increment_ip_request_count(self, client_ip):
        """新增：按客户端IP累加请求计数（线程安全）"""
        with self.lock:
            self.request_count += 1
            # 若IP已存在则计数+1，不存在则初始化为1
            if client_ip in self.ip_request_count:
                self.ip_request_count[client_ip] += 1
            else:
                self.ip_request_count[client_ip] = 1            

    def print_hourly_stats(self):
        """新增：打印每小时统计信息"""
        """修改：每半小时打印一次统计，已运行时长以小时为单位（保留小数）"""
        while True:
            time.sleep(1800)  # 每半小时执行一次
            current_time = time.time()
            # 计算总运行时长（小时，保留一位小数）
            elapsed_hours = (current_time - self.start_time) / 3600
            with self.lock:
                logger.info(f"=== 运行统计 ===")
                logger.info(f"当前时间: {time.strftime('%H:%M:%S')}")
                logger.info(f"已运行时长: {elapsed_hours:.1f} 个小时")  # 显示0.5、1.5等格式
                logger.info(f"累积处理请求数: {self.request_count}")  
                logger.info(f"各客户端IP请求明细:")
                # 遍历IP计数字典，打印每个IP的请求量
                if self.ip_request_count:
                    for ip, count in self.ip_request_count.items():
                        logger.info(f"  {ip}: {count} 次请求")
                else:
                    logger.info(f"  暂无客户端请求")      
                # logger.info(f"正常处理请求数: {self.request_count}")        

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

            # 遍历任务队列，仅重分配「未启动」且绑定到旧容器（hadoop-master-0）的任务
            for idx, task in enumerate(self.task_queue):
                # 仅重分配绑定到旧容器（hadoop-master-0）且未执行的任务 增加 task.get("status") != "running" 判断
                if task.get("container") == "hadoop-master-0" and task.get("status") != "running":
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
                    universal_newlines='utf-8', # 显式指定解码编码为 UTF-8，匹配脚本输出
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
                    # 核心新增：扩容后强制更新可用容器列表
                    self.update_available_containers()
                    logger.info(f"扩容后可用容器列表: {self.available_containers}")
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
                    f"bash /home/wzy/hadoop-cluster-docker/reduce-container.sh {target_num}",
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines='utf-8', # 显式指定解码编码为 UTF-8，匹配脚本输出
                    timeout=300
                )
                if result.returncode != 0:
                    logger.error(f"缩容脚本执行失败，退出码: {result.returncode}, 输出: {result.stdout}")
                else:
                    logger.info(f"缩容脚本执行成功，输出: {result.stdout}")
                time.sleep(5)
                # 新增：缩容后强制更新可用容器列表
                self.update_available_containers()
                logger.info(f"缩容后可用容器列表: {self.available_containers}")
            except subprocess.TimeoutExpired:
                logger.error(f"缩容脚本执行超时（超过5分钟）")
            except Exception as e:
                logger.error(f"缩容集群失败: {str(e)}")
        # with self.lock:
        #     if target_num < current_num:
        #         logger.info(f"缩容集群: {current_num} -> {target_num}")
        #         try:
        #             # 使用universal_newlines替代text参数
        #             result = subprocess.run(
        #                 f"bash /home/wzy/hadoop-cluster-docker/reduce-container.sh {target_num}",
        #                 shell=True,
        #                 stdout=subprocess.PIPE,
        #                 stderr=subprocess.STDOUT,
        #                 universal_newlines='utf-8', # 显式指定解码编码为 UTF-8，匹配脚本输出
        #                 timeout=300
        #             )
        #             if result.returncode != 0:
        #                 logger.error(f"缩容脚本执行失败，退出码: {result.returncode}, 输出: {result.stdout}")
        #             else:
        #                 logger.info(f"缩容脚本执行成功，输出: {result.stdout}")
        #             time.sleep(5)
        #             # 新增：缩容后强制更新可用容器列表
        #             self.update_available_containers()
        #             logger.info(f"缩容后可用容器列表: {self.available_containers}")
        #         except subprocess.TimeoutExpired:
        #             logger.error(f"缩容脚本执行超时（超过5分钟）")
        #         except Exception as e:
        #             logger.error(f"缩容集群失败: {str(e)}")

    def add_task(self, task):
        """添加任务到队列"""
        with self.lock:
            self.task_queue.append(task)

    def remove_task(self, uuid):
        """从队列移除已完成任务"""
        with self.lock:
            self.task_queue = [t for t in self.task_queue if t['uuid'] != uuid]

    def monitor_and_adjust(self):
        # """监控任务队列并动态调整集群规模（修改缩容触发条件)"""
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
                            self.send_callback(
                                task['callback_url'],
                                task['uuid'],
                                False,
                                "任务执行出错"
                            )
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
                        self.send_callback(
                            task['callback_url'],
                            task['uuid'],
                            False,
                            "任务处理失败"
                        )
                        self.remove_task(task['uuid'])
                    
                # for task in pending_tasks:
                #     try:
                #         # 1. 启动任务（后台执行）
                #         cmd = f"docker exec -d {task['container']} bash -c '{task['command']}'"
                #         logger.info(f"执行任务: {cmd}")
                #         result = subprocess.run(
                #             cmd,
                #             shell=True,
                #             stdout=subprocess.PIPE,
                #             stderr=subprocess.STDOUT,
                #             universal_newlines=True,
                #             timeout=60
                #         )
                #         if result.returncode != 0:
                #             logger.error(f"任务启动失败 {task['uuid']}: {result.stdout}")
                #             task["status"] = "failed"
                #             self.send_callback(task['callback_url'],
                #                 task['uuid'],
                #                 False,
                #                 "任务执行出错"
                #             )
                #             self.remove_task(task['uuid'])
                #             continue

                #         # 2. 关键修复：用线程池并行监控任务完成（非阻塞）
                #         executor.submit(
                #             self.monitor_task_completion,  # 提交监控逻辑到线程池
                #             task
                #         )

                #     except Exception as e:
                #         logger.error(f"任务处理失败 {task['uuid']}: {str(e)}")
                #         task["status"] = "failed"
                #         self.send_callback(
                #             task['callback_url'],
                #             task['uuid'],
                #             False,
                #             "任务处理失败"
                #         )
                #         self.remove_task(task['uuid'])

            time.sleep(2)  # 降低循环频率，减少资源占用

    def monitor_task_completion(self, task):
        """监控任务完成状态并从独立日志文件提取结果（修复路径重复问题）"""
        max_wait_time = 3600
        check_interval = 5
        start_time = time.time()

        # 获取项目根目录的绝对路径
        current_file_dir = os.path.dirname(os.path.abspath(__file__))  # /home/wzy/hadoop-cluster-docker/server
        project_root = os.path.dirname(current_file_dir)              # /home/wzy/hadoop-cluster-docker

        # 绝对路径用于实际文件操作
        LOGS_ABS_DIR = os.path.join(project_root, "logs")

        # 相对显示路径（从 hadoop-cluster-docker 开始）
        try:
            # 将绝对路径转换为以 PROJECT_NAME 开头的“伪相对路径”
            # 方法：从 project_root 中提取 PROJECT_NAME 及之后的部分
            project_base_name = os.path.basename(project_root)  # "hadoop-cluster-docker"
            display_logs_dir = os.path.join(project_base_name, "logs")  # "hadoop-cluster-docker/logs"
        except Exception:
            display_logs_dir = "logs"  # 回退

        logger.info(f"日志文件根目录: {display_logs_dir}")

        while time.time() - start_time < max_wait_time:
            if os.path.exists(SUBSCRIBE_QUEUE):
                try:
                    with open(SUBSCRIBE_QUEUE, 'r', encoding='utf-8') as f:
                        content = f.read()
                        pattern = f"{task['uuid']}:::(.*?)\n"
                        log_match = re.search(pattern, content, re.DOTALL)

                        if log_match:
                            log_file_rel_path = log_match.group(1).strip()
                            log_file_rel_path = re.sub(r'^logs[/\\]', '', log_file_rel_path)

                            # 实际读取用绝对路径
                            log_file_abs_path = os.path.join(LOGS_ABS_DIR, log_file_rel_path)
                            # 显示用相对路径
                            log_file_display_path = os.path.join(display_logs_dir, log_file_rel_path)

                            logger.info(f"尝试读取日志文件: {log_file_display_path}")

                            if os.path.exists(log_file_abs_path):
                                if os.path.getsize(log_file_abs_path) > 0:
                                    with open(log_file_abs_path, 'r', encoding='utf-8') as log_f:
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
                                    logger.info(f"日志文件存在但为空: {log_file_display_path}，等待重试...")
                            else:
                                logger.info(f"日志文件尚未生成: {log_file_display_path}，等待重试...")
                except Exception as e:
                    logger.error(f"处理订阅文件失败: {str(e)}")
                    time.sleep(check_interval)
                    continue
            time.sleep(check_interval)

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
        # pattern = r"(I\d{4} \d{2}:\d{2}:\d{2}\.\d{6} +\d+ caffe\.cpp:495\] execution time: .*? us)"
        # match = re.search(pattern, combined, re.DOTALL | re.IGNORECASE)

        # if match:
        #     model_info = match.group(0).strip()
        #     logger.info("Extracted model info: %s" % model_info)
        #     return True, model_info
        # else:
        #     logger.warning("No execution time found, returning full output")
        #     return True, combined
        # 【核心修改：根据命令内容判断任务类型，针对性解析】
        parsed_result = ""
        if "yolov3_416" in shcmd:
            # -------------------------- yolov3 输出解析 --------------------------
            # 修复正则表达式，使其能正确匹配实际输出格式
            patterns_yolov3 = [
                # 匹配 yolov3_detection() 执行时间，支持科学计数法
                (r"yolov3_detection\(\) execution time: (.*? us)", "Execution Time"),
                # 匹配 Hardware fps: 后面的数字，包括浮点数
                (r"Hardware fps: ([\d.]+)", "Hardware FPS"),
                # 匹配 End2end throughput fps: 后面的数字
                (r"End2end throughput fps: ([\d.]+)", "End2end FPS"),
                # 匹配 Using MLU device 后面的数字
                (r"Using MLU device (\d+)", "MLU Device")
            ]
            parsed_result = "=== YOLOv3 Task Result ===\n"
            for pattern, label in patterns_yolov3:
                match = re.search(pattern, combined, re.DOTALL | re.IGNORECASE)
                if match:
                    parsed_result += f"{label}: {match.group(1).strip()}\n"
                else:
                    parsed_result += f"{label}: Not Found\n"

        elif "classification" in shcmd:
            # -------------------------- Classification 输出解析 --------------------------
            # 修复正则表达式，使其能正确匹配实际输出格式
            patterns_cls = [
                # 匹配 accuracy1: 后面的数字，包括括号内的内容
                (r"accuracy1: ([\d.]+)", "Accuracy@1"),
                # 匹配 accuracy5: 后面的数字
                (r"accuracy5: ([\d.]+)", "Accuracy@5"),
                # 匹配 Total execution time: 后面的时间
                (r"Total execution time: (.*? us)", "Total Execution Time"),
                # 匹配 Hardware fps: 后面的数字
                (r"Hardware fps: ([\d.]+)", "Hardware FPS"),
                # 匹配 End2end throughput fps: 后面的数字
                (r"End2end throughput fps: ([\d.]+)", "End2end FPS"),
                # 匹配 Using MLU device 后面的数字
                (r"Using MLU device (\d+)", "MLU Device")
            ]
            parsed_result = "=== Classification Task Result ===\n"
            for pattern, label in patterns_cls:
                match = re.search(pattern, combined, re.DOTALL | re.IGNORECASE)
                if match:
                    parsed_result += f"{label}: {match.group(1).strip()}\n"
                else:
                    parsed_result += f"{label}: Not Found\n"

        # 若未匹配到任何任务类型，返回原始输出
        if not parsed_result:
            parsed_result = f"Command executed successfully. Raw output:\n{combined_output}"

        logger.info(f"Parsed result:\n{parsed_result}")
        return True, parsed_result

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


def async_process_task(input_task, output_path, uuid_str, callback_url):
    """Process task asynchronously"""
    try:
        logger.info("[Async Task] Starting processing UUID: %s, task_type: %s" % (uuid_str, input_task))
        # logger.info("[Async Task] Input path: %s, Output path: %s" % (input_path, output_path))

        # Execute inference command
        # 【核心修改1：根据 task_type 动态生成 Docker 命令】
        if input_task == "yolov3":
            # yolov3 任务命令
            docker_cmd = "docker exec camb_test bash -c 'cd  /cambricon/v8.2_arm/ && source env.sh && cd /cambricon/v8.2_arm/arm64/yolov3_416 && bash run_fp16.sh'"
        elif input_task == "classification":
            # classification 任务命令
            docker_cmd = "docker exec camb_test bash -c 'cd  /cambricon/v8.2_arm/ && source env.sh && cd /cambricon/v8.2_arm/arm64/classification && bash run_fp16.sh'"
        else:
            raise ValueError(f"Unsupported task_type: {input_task}")
        
        # inference_cmd = "cd /opt/cambricon/caffe/src/caffe && bash gen_offline_model.sh"
        success, result_output = parse_shell(docker_cmd)
        
        # Build task result (保留原结构，新增 task_type 字段)
        # 3. 【核心修改：复用cluster_manager.send_callback()，与hadoop回调格式统一】
        # 构造与hadoop一致的message内容（包含任务类型、命令、解析结果）
        message = f"Task Type: {input_task}\n" \
                  f"Executed Command: {docker_cmd}\n" \
                  f"Execution Time: {time.strftime('%H:%M:%S')}\n" \
                  f"Parsed Result:\n{result_output}"
        
        # 调用hadoop路由的回调方法，确保数据结构一致
        cluster_manager.send_callback(
            url=callback_url,
            uuid=uuid_str,
            success=success,
            message=message  # 解析结果放入message字段
        )

    except Exception as e:
        error_msg = f"Task processing error: {str(e)}\nTraceback: {traceback.format_exc()}"
        logger.error(error_msg)
        # 异常时也通过send_callback发送错误信息
        if callback_url:
            cluster_manager.send_callback(
                url=callback_url,
                uuid=uuid_str,
                success=False,
                message=error_msg
            )
    finally:
        logger.info("[Async Task] Processing finished UUID: %s" % uuid_str)


# 初始化集群管理器并启动后台线程
cluster_manager = ClusterManager()

# 新增：启动每小时统计线程
hourly_stats_thread = threading.Thread(target=cluster_manager.print_hourly_stats, daemon=True)
hourly_stats_thread.start()

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
        client_ip = request.remote_addr  # 获取客户端IP
        
        # 新增：请求计数加1
        # cluster_manager.increment_request_count()
        cluster_manager.increment_ip_request_count()

        # Validate required parameters
        required_params = ["input", "callback_url"]
        for param in required_params:
            if param not in data:
                error_msg = "Missing parameter: %s" % param
                logger.error(error_msg)
                return error_msg, 400

        input_task = data["input"]
        output_path = data.get("output", "")
        callback_url = data["callback_url"]
        # task_type = data["task_type"]  # 取值：yolov3 或 classification
        
        # 【核心修改2：校验 input_task 合法性】
        if input_task not in ["yolov3", "classification"]:
            error_msg = f"Invalid task_type: {input_task}. Must be 'yolov3' or 'classification'"
            logger.error(error_msg)
            return error_msg, 400

        # Generate UUID
        uuid_str = str(uuid.uuid1())
        logger.info("Generated UUID: %s" % uuid_str)

        # Submit async task
        executor.submit(
            async_process_task,
            input_task,
            output_path,
            uuid_str,
            callback_url,
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
        client_ip = request.remote_addr  # 获取客户端IP

        required = ["input", "output", "callback_url"]
        for param in required:
            if param not in data:
                return f"缺少参数: {param}", 400
            
        # 新增：请求计数加1
        # cluster_manager.increment_request_count()
        cluster_manager.increment_ip_request_count(client_ip)  # IP请求数+1

        uuid_str = str(uuid.uuid1())
        selected_master = None
        retry_count = 0
        max_retry = 5  # 增加重试次数
        retry_interval = 5
        
        #根据input参数映射对应脚本
        input_param = data["input"].strip().lower()  # 统一转为小写，避免大小写问题
        # 应用类型-脚本映射字典
        app_script_map = {
            "grep": "run-grep.sh",
            "pi": "run-pi.sh",
            "randomwriter": "run-teragen.sh",
            "sort": "run-sort3.sh",
            "wordmean": "run-wordmean.sh",
            "wordmedian": "run-wordmedian.sh"
        }
        
        input_map = {
            "grep":"input/input-grep1",
            "pi":"input/input-pi1",
            "randomwriter":"input/input-teragen1",
            "sort":"local-text-data input/input-sort2",
            "wordmean":"input/input2",
            "wordmedian":"input/input3",
            "wordcount":"input/input1",
        }
        
        # 匹配脚本：优先映射，未匹配或为wordcount则用默认脚本
        if input_param in app_script_map:
            script_name = app_script_map[input_param]
        else:
            script_name = "run-wordcount2.sh"  # 包含wordcount和其他未匹配情况
            
        if input_param in input_map:
            input_name = input_map[input_param]
        else:
            input_name = "input/input2"            

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
            "command": f"bash /root/{script_name} {input_name} {data['output']} {uuid_str}",
            "container": selected_master,  # 绑定到新选择的容器
            "callback_url": data["callback_url"],
            "timestamp": time.time()
        })

        return jsonify({"uuid": uuid_str})
    except Exception as e:
        logger.error(f"/hadoop 错误: {str(e)}")
        return str(e), 500

if __name__ == "__main__":
    logger.info("Starting proxy server...")
    # logger.info("Starting MLU inference server...")
    app.run(
        debug=False,
        threaded=True,
        host="0.0.0.0",
        port=8800
    )



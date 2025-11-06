#coding:utf-8
import subprocess
import os
import requests
import threading
import logging
import sys
import codecs
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, g
import uuid
import time
import re
import traceback

# 修复中文编码问题
try:
    sys.stdout.buffer.write('\ufffd'.encode('utf-8'))
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
except Exception as e:
    logging.warning(f"编码配置失败: {str(e)}")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler("server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化Flask应用
app = Flask(__name__)

# 适配Werkzeug 1.0.1，自定义访问日志格式
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.WARNING)

@app.before_request
def record_start_time():
    g.start_time = time.time()

@app.after_request
def custom_access_log(response):
    if request.path == '/favicon.ico':
        return response
    elapsed_time = (time.time() - g.start_time) * 1000
    current_time = time.strftime('%H:%M:%S')
    remote_addr = request.remote_addr
    request_line = f"{request.method} {request.path} {request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1')}"
    status_code = response.status_code
    content_length = response.headers.get('Content-Length', '-')
    log_msg = f"{current_time} - INFO - [访问日志] {remote_addr} - \"{request_line}\" {status_code} {content_length} - {elapsed_time:.2f}ms"
    logger.info(log_msg)
    return response

# 配置参数 - 动态路径
USER_HOME = os.path.expanduser('~')
HADOOP_BASE_DIR = os.path.join(USER_HOME, 'hadoop-cluster-docker')

# 路径定义
PUBLISH_QUEUE = os.path.join(HADOOP_BASE_DIR, 'publish', 'publish.txt')
SUBSCRIBE_QUEUE = os.path.join(HADOOP_BASE_DIR, 'subscribe', 'subscribe.txt')
EXTEND_SCRIPT = os.path.join(HADOOP_BASE_DIR, 'extend-container2.sh')
REDUCE_SCRIPT = os.path.join(HADOOP_BASE_DIR, 'reduce-container.sh')

MAX_HADOOP_GROUPS = 8
CHECK_INTERVAL = 10
executor = ThreadPoolExecutor(max_workers=10)


class ClusterManager:
    """Hadoop集群动态扩缩容管理器"""
    def __init__(self):
        self.task_queue = []
        # 细粒度锁
        self.task_lock = threading.Lock()
        self.container_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        
        self.request_count = 0
        self.start_time = time.time()
        self.ip_request_count = {}
        self.available_containers = ["hadoop-master-0"]
        self.shrinking_containers = set()
        self.shrink_lock = threading.Lock()

    def get_task_count(self):
        try:
            if self.task_lock.acquire(timeout=2):
                try:
                    return len(self.task_queue)
                finally:
                    self.task_lock.release()
            else:
                logger.error("获取任务队列锁超时，返回任务数0")
                return 0
        except Exception as e:
            logger.error(f"获取任务数失败: {str(e)}")
            return 0
            
    def increment_ip_request_count(self, client_ip):
        try:
            if self.stats_lock.acquire(timeout=2):
                try:
                    self.request_count += 1
                    self.ip_request_count[client_ip] = self.ip_request_count.get(client_ip, 0) + 1
                finally:
                    self.stats_lock.release()
            else:
                logger.error(f"更新IP请求计数锁超时，客户端IP: {client_ip}")
        except Exception as e:
            logger.error(f"更新IP请求计数失败: {str(e)}")

    def print_hourly_stats(self):
        while True:
            time.sleep(1800)
            current_time = time.time()
            elapsed_hours = (current_time - self.start_time) / 3600
            try:
                if self.stats_lock.acquire(timeout=5):
                    try:
                        logger.info(f"=== 运行统计 ===")
                        logger.info(f"当前时间: {time.strftime('%H:%M:%S')}")
                        logger.info(f"已运行时长: {elapsed_hours:.1f} 小时")
                        logger.info(f"累积处理请求数: {self.request_count}")  
                        logger.info(f"各客户端IP请求明细:")
                        for ip, count in self.ip_request_count.items():
                            logger.info(f"  {ip}: {count} 次")
                    finally:
                        self.stats_lock.release()
                else:
                    logger.error("获取统计锁超时，跳过本次统计")
            except Exception as e:
                logger.error(f"打印小时统计异常: {str(e)}")

    def get_hadoop_count(self):
        try:
            output = subprocess.check_output(
                "docker ps | grep hadoop-master | wc -l",
                shell=True,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=10
            )
            count = int(output.strip())
            logger.info(f"获取到Hadoop master容器数量: {count}")
            return count
        except subprocess.TimeoutExpired:
            logger.error(f"获取Hadoop容器数量超时（10秒）")
            return 1
        except Exception as e:
            logger.error(f"获取Hadoop容器数量失败: {str(e)}")
            return 1

    def is_container_available(self, container_name):
        logger.info(f"检查容器可用性: {container_name}")
        try:
            # 检查容器是否运行
            result = subprocess.run(
                f"docker inspect --format '{{{{.State.Running}}}}' {container_name}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                timeout=3
            )
            if result.returncode != 0:
                logger.warning(f"容器状态检查失败: {result.stderr}")
                return False
            
            if result.stdout.strip() != "true":
                logger.info(f"容器 {container_name} 未运行")
                return False

            # 检查Hadoop服务
            hadoop_running = False
            for _ in range(2):
                try:
                    result = subprocess.run(
                        f"docker exec {container_name} jps | grep NameNode",
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        encoding='utf-8',
                        timeout=2
                    )
                    if result.returncode == 0:
                        hadoop_running = True
                        break
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"Hadoop状态检查异常: {str(e)}")
                    continue

            if not hadoop_running:
                logger.info(f"容器 {container_name} 内Hadoop未启动")
                return False

            logger.info(f"容器 {container_name} 可用")
            return True
        except Exception as e:
            logger.warning(f"容器可用性检查失败: {str(e)}")
            return False
        
    def update_available_containers(self):
        logger.info("更新可用容器列表")
        try:
            if self.container_lock.acquire(timeout=5):
                try:
                    all_masters = []
                    try:
                        result = subprocess.check_output(
                            "docker ps --filter 'name=hadoop-master-' --format '{{.Names}}' | sort",
                            shell=True,
                            encoding='utf-8',
                            timeout=5
                        )
                        all_masters = result.splitlines()
                    except Exception as e:
                        logger.error(f"获取容器列表失败: {str(e)}，使用兜底列表")
                        all_masters = ["hadoop-master-0"]

                    # 过滤可用容器
                    available = []
                    for master in all_masters:
                        if master not in self.shrinking_containers and self.is_container_available(master):
                            available.append(master)
                    
                    self.available_containers = available
                    logger.info(f"可用容器列表: {self.available_containers}（缩容黑名单：{self.shrinking_containers}）")
                finally:
                    self.container_lock.release()
            else:
                logger.error("获取容器锁超时，无法更新可用容器")
        except Exception as e:
            logger.error(f"更新可用容器异常: {str(e)}")
            with self.container_lock:
                self.available_containers = ["hadoop-master-0"]

    def reassign_pending_tasks(self):
        logger.info("重分配待处理任务")
        try:
            if self.container_lock.acquire(timeout=5):
                try:
                    self.update_available_containers()
                    if len(self.available_containers) <= 1:
                        logger.info("可用容器数<=1，无需重分配")
                        return

                    if self.task_lock.acquire(timeout=5):
                        try:
                            reassigned = 0
                            for idx, task in enumerate(self.task_queue):
                                if task.get("container") == "hadoop-master-0" and task.get("status") != "running":
                                    new_container = self.available_containers[idx % len(self.available_containers)]
                                    logger.info(f"任务 {task['uuid']} 从 hadoop-master-0 重分配到 {new_container}")
                                    self.task_queue[idx]["container"] = new_container
                                    reassigned += 1
                            logger.info(f"完成重分配，共 {reassigned} 个任务")
                        finally:
                            self.task_lock.release()
                    else:
                        logger.error("获取任务锁超时，无法重分配")
                finally:
                    self.container_lock.release()
            else:
                logger.error("获取容器锁超时，无法重分配")
        except Exception as e:
            logger.error(f"任务重分配异常: {str(e)}")

    def reassign_task(self, task):
        logger.info(f"重分配任务: {task['uuid']}（当前容器：{task['container']}）")
        try:
            if self.container_lock.acquire(timeout=5):
                try:
                    task["status"] = "pending"
                    self.update_available_containers()
                    available_masters = self.available_containers.copy()
                finally:
                    self.container_lock.release()
            else:
                logger.error(f"获取容器锁超时，任务 {task['uuid']} 重分配失败")
                return

            if not available_masters:
                logger.error(f"无可用容器，任务 {task['uuid']} 分配失败")
                self.send_callback(
                    task['callback_url'],
                    task['uuid'],
                    False,
                    "无可用容器"
                )
                self.remove_task(task['uuid'])
                return

            task_count = self.get_task_count()
            new_container = available_masters[task_count % len(available_masters)]
            logger.info(f"任务 {task['uuid']} 重分配到 {new_container}")

            if self.task_lock.acquire(timeout=5):
                try:
                    task["container"] = new_container
                    task["status"] = "pending"
                finally:
                    self.task_lock.release()
            else:
                logger.error(f"获取任务锁超时，任务 {task['uuid']} 重分配失败")
        except Exception as e:
            logger.error(f"任务重分配异常: {str(e)}")

    def extend_cluster(self, target_num):
        logger.info(f"扩容逻辑启动，目标: {target_num}")
        try:
            if target_num > MAX_HADOOP_GROUPS:
                target_num = MAX_HADOOP_GROUPS
                logger.info(f"目标超过最大值{MAX_HADOOP_GROUPS}，调整为{target_num}")
            
            current_num = self.get_hadoop_count()
            if target_num <= current_num:
                logger.info(f"目标{target_num}≤当前{current_num}，无需扩容")
                return

            logger.info(f"扩容集群: {current_num} -> {target_num}")
            result = subprocess.run(
                f"bash {EXTEND_SCRIPT} {target_num}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.error(f"扩容脚本失败，退出码: {result.returncode}, 输出: {result.stdout}")
            else:
                logger.info(f"扩容脚本成功，输出: {result.stdout}")
                time.sleep(10)
                new_masters = [f"hadoop-master-{i}" for i in range(current_num, target_num)]
                logger.info(f"新增容器: {new_masters}")
                
                # 检查新容器可用性
                for master in new_masters:
                    try:
                        if self.is_container_available(master):
                            logger.info(f"新容器 {master} 就绪")
                        else:
                            logger.warning(f"新容器 {master} 未就绪")
                    except Exception as e:
                        logger.error(f"检查新容器 {master} 异常: {str(e)}")
                
                # 更新容器列表并重分配任务
                self.update_available_containers()
                logger.info(f"扩容后可用容器: {self.available_containers}")
                self.reassign_pending_tasks()
        except subprocess.TimeoutExpired:
            logger.error("扩容脚本超时（5分钟）")
        except Exception as e:
            logger.error(f"扩容逻辑异常: {str(e)}")

    def get_tasks_running_containers(self):
        try:
            if self.task_lock.acquire(timeout=5):
                try:
                    return {task["container"] for task in self.task_queue if task.get("status") == "running"}
                finally:
                    self.task_lock.release()
            else:
                logger.error("获取任务锁超时，返回空运行容器集")
                return set()
        except Exception as e:
            logger.error(f"获取运行中容器异常: {str(e)}")
            return set()

    def reduce_cluster(self, target_num):
        with self.task_lock:
            if len(self.task_queue) > 0:
                logger.info(f"任务列表非空（{len(self.task_queue)}个），不缩容")
                return

        if target_num < 1:
            target_num = 1
        current_num = self.get_hadoop_count()
        if target_num >= current_num:
            logger.info(f"目标{target_num}≥当前{current_num}，不缩容")
            return

        if not self.shrink_lock.acquire(blocking=False):
            logger.info("已有缩容操作，跳过本次")
            return

        try:
            logger.info(f"缩容集群: {current_num} -> {target_num}")
            containers_to_delete = [f"hadoop-master-{i}" for i in range(target_num, current_num)]
            
            with self.container_lock:
                self.shrinking_containers.update(containers_to_delete)
            logger.info(f"缩容黑名单新增: {containers_to_delete}")

            result = subprocess.run(
                f"bash {REDUCE_SCRIPT} {target_num}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.error(f"缩容脚本失败，退出码: {result.returncode}, 输出: {result.stdout}")
            else:
                logger.info(f"缩容脚本成功，输出: {result.stdout}")
            time.sleep(5)
            self.update_available_containers()
            logger.info(f"缩容后可用容器: {self.available_containers}")
        except subprocess.TimeoutExpired:
            logger.error("缩容脚本超时（5分钟）")
        except Exception as e:
            logger.error(f"缩容逻辑异常: {str(e)}")
        finally:
            with self.container_lock:
                self.shrinking_containers.difference_update(containers_to_delete)
            self.shrink_lock.release()
            logger.info(f"缩容结束，黑名单移除: {containers_to_delete}")

    def add_task(self, task):
        try:
            if self.task_lock.acquire(timeout=5):
                try:
                    self.task_queue.append(task)
                    logger.info(f"任务 {task['uuid']} 加入队列，当前队列长度: {len(self.task_queue)}")
                finally:
                    self.task_lock.release()
            else:
                logger.error(f"获取任务锁超时，任务 {task['uuid']} 加入失败")
        except Exception as e:
            logger.error(f"添加任务异常: {str(e)}")

    def remove_task(self, uuid):
        try:
            if self.task_lock.acquire(timeout=5):
                try:
                    original_length = len(self.task_queue)
                    self.task_queue = [t for t in self.task_queue if t['uuid'] != uuid]
                    logger.info(f"任务 {uuid} 从队列移除，队列长度变化: {original_length} -> {len(self.task_queue)}")
                finally:
                    self.task_lock.release()
            else:
                logger.error(f"获取任务锁超时，任务 {uuid} 移除失败")
        except Exception as e:
            logger.error(f"移除任务异常: {str(e)}")

    def monitor_and_adjust(self):
        """核心监控线程，确保心跳日志持续输出"""
        logger.info("monitor_and_adjust线程启动")
        while True:
            try:
                # 强制输出心跳日志（每CHECK_INTERVAL秒一次）
                task_count = self.get_task_count()
                current_groups = self.get_hadoop_count()
                logger.info(f"[monitor心跳] 当前任务数: {task_count}, 当前容器组数: {current_groups}")

                # 扩缩容逻辑
                if task_count > current_groups:
                    self.extend_cluster(task_count)
                elif task_count == 0 and current_groups > 1:
                    self.reduce_cluster(1)

            except Exception as e:
                # 捕获所有异常，确保线程不终止
                logger.error(f"monitor_and_adjust线程异常: {str(e)}", exc_info=True)
                traceback.print_exc()

            finally:
                # 无论是否异常，都按固定间隔休眠
                time.sleep(CHECK_INTERVAL)

    def process_tasks(self):
        logger.info("process_tasks线程启动")
        while True:
            pending_tasks = []
            # 短时间持有锁，获取待处理任务
            if self.task_lock.acquire(timeout=5):
                try:
                    pending_tasks = [t for t in self.task_queue if t.get("status") != "running"]
                    for task in pending_tasks:
                        task["status"] = "running"
                finally:
                    self.task_lock.release()
            else:
                logger.error("获取任务锁超时，跳过本轮任务处理")
                time.sleep(2)
                continue

            # 处理任务（释放锁后执行）
            for task in pending_tasks:
                try:
                    container = task["container"]
                    in_shrinking = False
                    with self.container_lock:
                        in_shrinking = container in self.shrinking_containers
                    
                    if in_shrinking or not self.is_container_available(container):
                        logger.warning(f"容器 {container} 不可用，任务 {task['uuid']} 重分配")
                        self.reassign_task(task)
                        continue

                    # 执行任务
                    cmd = f"docker exec -d {container} bash -c '{task['command']}'"
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
                        logger.error(f"任务 {task['uuid']} 启动失败: {result.stdout}")
                        self.send_callback(
                            task['callback_url'],
                            task['uuid'],
                            False,
                            "任务启动失败"
                        )
                        self.remove_task(task['uuid'])
                        continue

                    executor.submit(self.monitor_task_completion, task)

                except Exception as e:
                    logger.error(f"任务 {task['uuid']} 处理异常: {str(e)}")
                    self.send_callback(
                        task['callback_url'],
                        task['uuid'],
                        False,
                        f"任务处理异常: {str(e)}"
                    )
                    self.remove_task(task['uuid'])

            time.sleep(2)

    def monitor_task_completion(self, task):
        max_wait_time = 3600
        check_interval = 5
        start_time = time.time()

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_file_dir)
        LOGS_ABS_DIR = os.path.join(project_root, "logs")

        try:
            project_base_name = os.path.basename(project_root)
            display_logs_dir = os.path.join(project_base_name, "logs")
        except Exception:
            display_logs_dir = "logs"

        logger.info(f"监控任务 {task['uuid']} 完成状态，日志目录: {display_logs_dir}")

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
                            log_file_abs_path = os.path.join(LOGS_ABS_DIR, log_file_rel_path)
                            log_file_display_path = os.path.join(display_logs_dir, log_file_rel_path)

                            if os.path.exists(log_file_abs_path) and os.path.getsize(log_file_abs_path) > 0:
                                with open(log_file_abs_path, 'r', encoding='utf-8') as log_f:
                                    result_msg = log_f.read().strip()
                                logger.info(f"任务 {task['uuid']} 完成，提取结果成功")
                                self.send_callback(
                                    task['callback_url'],
                                    task['uuid'],
                                    True,
                                    result_msg
                                )
                                self.remove_task(task['uuid'])
                                return
                            elif os.path.exists(log_file_abs_path):
                                logger.info(f"日志文件存在但为空: {log_file_display_path}，等待重试")
                            else:
                                logger.info(f"日志文件未生成: {log_file_display_path}，等待重试")
                except Exception as e:
                    logger.error(f"处理订阅文件异常: {str(e)}")
            time.sleep(check_interval)

        logger.error(f"任务 {task['uuid']} 超时（1小时）")
        self.send_callback(
            task['callback_url'],
            task['uuid'],
            False,
            "任务执行超时（超过1小时）"
        )
        self.remove_task(task['uuid'])

    def send_callback(self, url, uuid, success, message, max_retries=3, retry_interval=5):
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
                    timeout=10
                )
                response.raise_for_status()
                logger.info(f"回调成功（第{attempt+1}次） {uuid}: {response.status_code}")
                return
            except Exception as e:
                logger.warning(f"回调失败（第{attempt+1}次） {uuid}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
        logger.error(f"回调失败（{max_retries}次重试） {uuid}")


def parse_shell(shcmd):
    try:
        logger.info(f"执行命令: {shcmd}")
        p = subprocess.Popen(
            shcmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8'
        )
        stdout, stderr = p.communicate(timeout=300)
        combined = stdout + "\n" + stderr

        if p.returncode != 0:
            logger.error(f"命令失败（返回码: {p.returncode}）: {combined}")
            return False, combined

        parsed_result = ""
        if "yolov3_416" in shcmd:
            patterns = [
                (r"yolov3_detection\(\) execution time: (.*? us)", "Execution Time"),
                (r"Hardware fps: ([\d.]+)", "Hardware FPS"),
                (r"End2end throughput fps: ([\d.]+)", "End2end FPS"),
                (r"Using MLU device (\d+)", "MLU Device")
            ]
            parsed_result = "=== YOLOv3 结果 ===\n"
        elif "classification" in shcmd:
            patterns = [
                (r"accuracy1: ([\d.]+)", "Accuracy@1"),
                (r"accuracy5: ([\d.]+)", "Accuracy@5"),
                (r"Total execution time: (.*? us)", "Total Execution Time"),
                (r"Hardware fps: ([\d.]+)", "Hardware FPS"),
                (r"End2end throughput fps: ([\d.]+)", "End2end FPS"),
                (r"Using MLU device (\d+)", "MLU Device")
            ]
            parsed_result = "=== 分类任务结果 ===\n"

        if 'patterns' in locals():
            for pattern, label in patterns:
                match = re.search(pattern, combined, re.DOTALL | re.IGNORECASE)
                parsed_result += f"{label}: {match.group(1).strip() if match else 'Not Found'}\n"
        else:
            parsed_result = f"命令执行成功:\n{combined}"

        logger.info(f"解析结果:\n{parsed_result}")
        return True, parsed_result

    except subprocess.TimeoutExpired:
        p.kill()
        stdout, stderr = p.communicate()
        error_msg = f"命令超时（5分钟）: {stdout}\n{stderr}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"命令执行异常: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def async_process_task(input_task, output_path, uuid_str, callback_url):
    try:
        logger.info(f"[异步任务] 开始处理 UUID: {uuid_str}, 类型: {input_task}")

        if input_task == "yolov3":
            docker_cmd = "docker exec camb_test bash -c 'cd /cambricon/v8.2_arm/ && source env.sh && cd arm64/yolov3_416 && bash run_fp16.sh'"
        elif input_task == "classification":
            docker_cmd = "docker exec camb_test bash -c 'cd /cambricon/v8.2_arm/ && source env.sh && cd arm64/classification && bash run_fp16.sh'"
        else:
            raise ValueError(f"不支持的任务类型: {input_task}")
        
        success, result_output = parse_shell(docker_cmd)
        
        message = f"任务类型: {input_task}\n命令: {docker_cmd}\n时间: {time.strftime('%H:%M:%S')}\n结果:\n{result_output}"
        cluster_manager.send_callback(callback_url, uuid_str, success, message)

    except Exception as e:
        error_msg = f"任务处理异常: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        if callback_url:
            cluster_manager.send_callback(callback_url, uuid_str, False, error_msg)
    finally:
        logger.info(f"[异步任务] 完成处理 UUID: {uuid_str}")


# 初始化集群管理器并启动线程
cluster_manager = ClusterManager()

# 启动后台线程
hourly_stats_thread = threading.Thread(target=cluster_manager.print_hourly_stats, daemon=True)
hourly_stats_thread.start()

monitor_thread = threading.Thread(target=cluster_manager.monitor_and_adjust, daemon=True)
monitor_thread.start()

task_thread = threading.Thread(target=cluster_manager.process_tasks, daemon=True)
task_thread.start()


@app.route('/micro', methods=['POST'])
def handle_micro():
    try:
        data = request.get_json() or request.form
        client_ip = request.remote_addr
        logger.info(f"Received /micro 请求: {data}")
        
        cluster_manager.increment_ip_request_count(client_ip)

        required = ["input", "callback_url"]
        if not all(p in data for p in required):
            missing = [p for p in required if p not in data]
            return f"缺少参数: {missing}", 400

        input_task = data["input"]
        if input_task not in ["yolov3", "classification"]:
            return f"无效任务类型: {input_task}，支持 'yolov3' 或 'classification'", 400

        uuid_str = str(uuid.uuid1())
        logger.info(f"生成UUID: {uuid_str}")

        executor.submit(
            async_process_task,
            input_task,
            data.get("output", ""),
            uuid_str,
            data["callback_url"]
        )

        return uuid_str

    except Exception as e:
        logger.error(f"/micro 异常: {str(e)}", exc_info=True)
        return f"服务器错误: {str(e)}", 500


@app.route('/hadoop', methods=['POST'])
def handler_hadoop():
    try:
        data = request.get_json()
        logger.info(f"Received /hadoop 请求: {data}")
        client_ip = request.remote_addr

        required = ["input", "output", "callback_url"]
        if not all(p in data for p in required):
            missing = [p for p in required if p not in data]
            return f"缺少参数: {missing}", 400
        
        cluster_manager.increment_ip_request_count(client_ip)

        uuid_str = str(uuid.uuid1())
        selected_master = None
        retry_count = 0
        max_retry = 5
        retry_interval = 5
        
        input_param = data["input"].strip().lower()
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
        
        script_name = app_script_map.get(input_param, "run-wordcount2.sh")
        input_name = input_map.get(input_param, "input/input2")

        # 重试获取可用容器
        while retry_count < max_retry and not selected_master:
            try:
                cluster_manager.update_available_containers()
                with cluster_manager.container_lock:
                    available_masters = cluster_manager.available_containers.copy()
                
                if not available_masters:
                    logger.warning(f"第{retry_count+1}次尝试: 无可用容器")
                    retry_count += 1
                    time.sleep(retry_interval)
                    continue

                non_default = [m for m in available_masters if m != "hadoop-master-0"]
                if non_default:
                    task_count = cluster_manager.get_task_count()
                    selected_master = non_default[task_count % len(non_default)]
                else:
                    selected_master = available_masters[0]

                logger.info(f"任务 {uuid_str} 分配到容器: {selected_master}（可用: {available_masters}）")

            except Exception as e:
                logger.warning(f"第{retry_count+1}次尝试失败: {str(e)}")
                retry_count += 1
                time.sleep(retry_interval)

        if not selected_master:
            selected_master = "hadoop-master-0"
            logger.warning(f"所有重试失败，任务 {uuid_str} 分配到默认容器")

        cluster_manager.add_task({
            "uuid": uuid_str,
            "command": f"bash /root/{script_name} {input_name} {data['output']} {uuid_str}",
            "container": selected_master,
            "callback_url": data["callback_url"],
            "timestamp": time.time(),
            "status": "pending"
        })

        return jsonify({"uuid": uuid_str})
    except Exception as e:
        logger.error(f"/hadoop 异常: {str(e)}", exc_info=True)
        return str(e), 500

if __name__ == "__main__":
    logger.info("启动代理服务器...")
    app.run(
        debug=False,
        threaded=True,
        host="0.0.0.0",
        port=8800
    )
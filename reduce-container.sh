#!/bin/bash
# 强制使用 bash 执行，避免 dash 语法兼容问题
if [ -z "$BASH_VERSION" ]; then
    echo "Please using bash execute this script（bash reduce-container.sh）"
    exit 1
fi

# 配置参数：默认保留 N=1 个容器组，从节点数量 num=3
N=${1:-1}
num=3

# 修复中文乱码（设置终端编码）
# export LC_ALL=en_US.UTF-8

###########################################################################
# 修复1：时间格式优化 - 仅保留「时分秒.毫秒」，去除年月日和时间戳
###########################################################################
# 获取当前时间（格式：HH:MM:SS.sss，sss为毫秒）
get_current_time() {
    # date +%T 输出 HH:MM:SS，+%3N 输出毫秒（000-999），拼接后用 sed 替换冒号为点（或直接保留冒号）
    date +"%T.%3N"
}

# 记录开始时间（仅时分秒.毫秒）
before_start_time=$(get_current_time)
echo "Begining time : $before_start_time"

###########################################################################
# 修复2：准确获取当前运行的容器组数量（仅统计运行中，排除已停止）
###########################################################################
current_num=$(docker ps --filter "name=hadoop-master-" --format "{{.Names}}" | wc -l)
echo "current num :  $current_num"

# 校验参数：避免保留数量 ≥ 当前数量（无效操作）
if [ "$N" -ge "$current_num" ]; then
    echo "Error : current num $N）can not >= $current_num）"
    exit 1
fi

###########################################################################
# 修复3：容器组删除逻辑（先删容器→等端点释放→再删网络，避免活跃端点错误）
###########################################################################
j=$((current_num - 1))  # 从最后一个容器组开始删除（倒序删除，避免序号混乱）
while [ "$j" -ge "$N" ]; do
    echo -e "\n=== begining delete container group $j ==="

    # 1. 删除 master 容器（先检查是否存在，避免无效删除）
    master_name="hadoop-master-$j"
    if docker ps --filter "name=$master_name" --format "{{.Names}}" &> /dev/null; then
        echo "delete $master_name docker..."
        docker rm -f "$master_name"
        sleep 2  # 等待容器完全释放网络端点（关键：避免网络删除时残留）
    else
        echo "$master_name container not exists, skip delete "
    fi

    # 2. 删除 slave 容器（逐个删除，每个间隔1秒，减少资源竞争）
    i=1
    while [ "$i" -lt "$num" ]; do
        slave_name="hadoop-slave-$j-$i"
        if docker ps --filter "name=$slave_name" --format "{{.Names}}" &> /dev/null; then
            echo "delete $slave_name container..."
            docker rm -f "$slave_name"
            sleep 1
        else
            echo "$slave_name container not exists, skip delete"
        fi
        i=$((i + 1))
    done

    # 3. 删除网络（先检查网络是否存在+是否有残留端点）
    network_name="hadoop-$j"
    if docker network inspect "$network_name" &> /dev/null; then
        # 检查网络下是否仍有活跃端点（避免删除报错）
        active_endpoints=$(docker network inspect -f '{{range $k, $v := .Containers}}{{$k}} {{end}}' "$network_name")
        if [ -n "$active_endpoints" ]; then
            echo "Warning : Network $network_name still has active containers, waiting 5 seconds before retry..."
            sleep 5
            # 再次尝试删除网络（显式输出结果）
            if docker network rm "$network_name"; then
                echo "Network $network_name removed successfully"
            else
                echo "Error: Failed to remove network $network_name. Please run 'docker network rm $network_name' manually"
            fi
        else
            echo "Removing network $network_name ..."
            docker network rm "$network_name"
            echo "Network $network_name removed successfully"
        fi
    else
        echo "Network $network_name does not exist, skipping..."
    fi

    # 4. 标记当前容器组删除完成
    echo "Container group hadoop-$j deletion completed"
    j=$((j - 1))
    echo -e "***********************************\n"
done

###########################################################################
# 修复4：结束时间格式统一（仅时分秒.毫秒）
###########################################################################
end_start_time=$(get_current_time)
echo "Ending time : $end_start_time"

# 生成结束标记文件（保持原功能）
echo "end" > symbol

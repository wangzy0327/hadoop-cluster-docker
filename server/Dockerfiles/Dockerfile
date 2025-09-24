FROM ubuntu:18.04

# 拷贝国内源（确保 sources.list 存在）
COPY sources.list /etc/apt/sources.list

# 更新包列表并安装 Python 3 相关工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        curl && \
    # 升级 pip 到最新支持版本（可选）
    python3 -m pip install --upgrade "pip >= 20.3,< 22.0" && \
    # 安装 flask
    pip3 install --default-timeout=100 "flask<2" requests==2.25.1 && \
    # 清理缓存以减小镜像体积
    rm -rf /var/lib/apt/lists/*

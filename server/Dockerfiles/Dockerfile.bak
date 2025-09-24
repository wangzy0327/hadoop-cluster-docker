FROM ubuntu:16.04
COPY sources.list sources.list
RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak \
    && mv sources.list /etc/apt/
RUN apt-get update && apt-get install -y --no-install-recommends \
    python2.7 \ 
    python-pip \ 
    curl && \
    pip install flask && \
rm -rf /var/lib/apt/lists/*

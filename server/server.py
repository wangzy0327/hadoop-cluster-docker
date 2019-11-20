#coding:utf-8
import commands 
from flask import Flask
from flask import request,jsonify
import time
import threading
import random
import uuid

app=Flask(__name__)

@app.route('/pipeline', methods=['POST'])
def post_route():
     #execute a cmd
     def exec_cmd(cmd):
        status_cmd,output_cmd = commands.getstatusoutput(cmd)
        print('status of cmd: '+str(status_cmd))
        print('result of cmd: '+output_cmd)
        return output_cmd

     if request.method == 'POST':
        headers = request.headers
        
    #parse json request, get ipy_path 
        data = request.get_json()
        print'headers:',headers
        print('Data Received: "{data}"'.format(data=data))
        ipy_path = data["ipy_path"]
        print('ipy_path: '+ipy_path)
        pipeline_name = data["pipeline"]
        print('pipeline: '+pipeline_name)

    #au prepare shell to start container
        root_path = "/home/pipeline_server/shells/"
        name_shell_exec = 'start.sh'
        cmd_shell_exec = root_path + name_shell_exec+' '+ ipy_path
        output = exec_cmd(cmd_shell_exec)
        print('response output: '+output)
        return output
	#results = exec_cmd(cmd_list_output)
        
        return "cannot find the ipy path"

@app.route('/hadoop', methods=['POST'])
def handler_hadoop():
   #execute a cmd
     def exec_cmd(cmd):
        status_cmd,output_cmd = commands.getstatusoutput(cmd)
        print('status of cmd: '+str(status_cmd))
        print('result of cmd: '+output_cmd)
        return output_cmd
    
     if request.method == 'POST':
        headers = request.headers

    #parse json request, get ipy_path 
        data = request.get_json()
        print'headers:',headers
        print('Data Received: "{data}"'.format(data=data))
        input_path = data["input"]
        print('input path: '+input_path)
        output_path = data["output"]
        print('output path: '+output_path)

    #au prepare read request to queue
        base_path = "/home/wzy/hadoop-cluster-docker/"
        root_path = "/root/"
        exec_file = "run-wordcount2.sh"
        publish_path = "publish/publish.txt"
        uuid_str=str(uuid.uuid1())
        print("uuid : "+uuid_str)
        cmd_shell_exec = 'echo "sh '+root_path + exec_file +' '+ input_path +' '+ output_path +' '+ uuid_str +'" >>  ' + base_path + publish_path
        output = exec_cmd(cmd_shell_exec)
        print('response output: '+output)
        return uuid_str
        #results = exec_cmd(cmd_list_output)

        return "cannot find the input output path"
     

if __name__=="__main__":
        app.run(debug=True,threaded=True,host="0.0.0.0",port=8800)


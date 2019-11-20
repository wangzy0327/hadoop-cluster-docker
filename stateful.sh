#!/bin/bash
count=1
publish_output=publish/publish.txt
subscribe_output=subscribe/subscribe.txt
while :
do 
   shcmd=`head -n ${count} ${publish_output}`
   uuid=(`head -n ${count} ${publish_output} | awk '{print $NF}'`)
   echo "uuid : "${uuid}
   echo "shcmd : "${shcmd}
   sleep 3
   echo "uuid num : "${#uuid[@]}
   if [ ${#uuid[@]} -gt 0 ]
   then
       docker exec hadoop-master bash -c "${shcmd}"       
       while :
       do
           com_uuid=(`tail -n ${count} ${subscribe_output} | awk '{print $NF}'`)
           echo "com_uuid : "$com_uuid
           if [ "${uuid}" == "${com_uuid}" ];then
             break
           fi
       done
   fi
done

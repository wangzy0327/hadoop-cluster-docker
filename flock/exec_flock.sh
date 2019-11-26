i=1
N=10
while [ $i -le $N ]
do
   sh flock$i.sh
   i=$(( $i + 1 )) 
done


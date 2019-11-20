i=$1
input=$2
output=$3
uuid=$4
echo "i:"$i
echo "input:"$input
echo "output:"$output
echo "uuid:"$uuid
docker exec -d hadoop-master-$i bash -c 'sh run-wordcount2.sh $input $output $uuid'


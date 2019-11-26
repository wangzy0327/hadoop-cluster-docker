#!/bin/bash
{
    flock -x 3
    #[ $? -eq 1 ] && { echo fail; exit; }
    echo "hello6" >> mylockfile
    #echo $$
} 3<>mylockfile

echo "hello6"

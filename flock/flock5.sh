#!/bin/bash
{
    flock -x 3
    #[ $? -eq 1 ] && { echo fail; exit; }
    echo "hello5" >> mylockfile
    #echo $$
} 3<>mylockfile

echo "hello5"

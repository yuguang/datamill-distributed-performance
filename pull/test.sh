#!/bin/bash
for i in `seq 1 50`;
do
        timeout 60 python2 client.py $i
done
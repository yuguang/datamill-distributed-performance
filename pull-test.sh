#!/bin/bash
for i in `seq 11 50`;
do
        python2 client.py $i 5
done
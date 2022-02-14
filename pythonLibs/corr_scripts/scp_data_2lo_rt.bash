#!/bin/bash

base=$1
sshid="-i ~/.ssh/id_rsa"

if [ ! -d "/home/sonata/corr_data/$1/node1" ]; then
    mkdir -p /home/sonata/corr_data/$1/node1
    mkdir -p /home/sonata/corr_data/$1/node2
    mkdir -p /home/sonata/corr_data/$1/node3
    mkdir -p /home/sonata/corr_data/$1/node4
    mkdir -p /home/sonata/corr_data/$1/node5
    mkdir -p /home/sonata/corr_data/$1/node6
    mkdir -p /home/sonata/corr_data/$1/node7
    mkdir -p /home/sonata/corr_data/$1/node8
fi

scp ${sshid} sonata@seti-node1:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node1/$1_0.uvh5 &
scp ${sshid} sonata@seti-node2:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node2/$1_0.uvh5 &
scp ${sshid} sonata@seti-node2:/mnt/buf1/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node2/$1_1.uvh5 &
scp ${sshid} sonata@seti-node3:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node3/$1_0.uvh5 &
scp ${sshid} sonata@seti-node3:/mnt/buf1/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node3/$1_1.uvh5 &
scp ${sshid} sonata@seti-node4:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node4/$1_0.uvh5 &
scp ${sshid} sonata@seti-node4:/mnt/buf1/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node4/$1_1.uvh5 &
scp ${sshid} sonata@seti-node5:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node5/$1_0.uvh5 &
scp ${sshid} sonata@seti-node5:/mnt/buf1/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node5/$1_1.uvh5 &
scp ${sshid} sonata@seti-node6:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node6/$1_0.uvh5 &
scp ${sshid} sonata@seti-node6:/mnt/buf1/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node6/$1_1.uvh5 &
scp ${sshid} sonata@seti-node7:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node7/$1_0.uvh5 &
scp ${sshid} sonata@seti-node7:/mnt/buf1/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node7/$1_1.uvh5 &
scp ${sshid} sonata@seti-node8:/mnt/buf0/xGPU/UVH5/$1.uvh5 /home/sonata/corr_data/$1/node8/$1_0.uvh5 &

wait

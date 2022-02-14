#!/bin/bash

base=$1
sshid="-i ~/.ssh/id_rsa"

if [ ! -d "/home/sonata/corr_data/$1/node5" ]; then
    mkdir -p /home/sonata/corr_data/$1/node5
    mkdir -p /home/sonata/corr_data/$1/node6
    mkdir -p /home/sonata/corr_data/$1/node7
    mkdir -p /home/sonata/corr_data/$1/node8
fi

scp ${sshid} sonata@seti-node5:/mnt/buf0/$1_0.uvh5 /home/sonata/corr_data/$1/node5
scp ${sshid} sonata@seti-node5:/mnt/buf1/$1_1.uvh5 /home/sonata/corr_data/$1/node5
scp ${sshid} sonata@seti-node6:/mnt/buf0/$1_0.uvh5 /home/sonata/corr_data/$1/node6
scp ${sshid} sonata@seti-node6:/mnt/buf1/$1_1.uvh5 /home/sonata/corr_data/$1/node6
scp ${sshid} sonata@seti-node7:/mnt/buf0/$1_0.uvh5 /home/sonata/corr_data/$1/node7
scp ${sshid} sonata@seti-node7:/mnt/buf1/$1_1.uvh5 /home/sonata/corr_data/$1/node7
scp ${sshid} sonata@seti-node8:/mnt/buf0/$1_0.uvh5 /home/sonata/corr_data/$1/node8

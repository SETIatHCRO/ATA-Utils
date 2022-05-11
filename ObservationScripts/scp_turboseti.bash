#!/bin/bash

base=$1
sshid="-i ~/.ssh/id_rsa"
baseout="/mnt/dataz-netStorage-40G/turboseti"

if [ ! -d "${baseout}/$1/seti-node1.0" ]; then
    mkdir -p ${baseout}/$1/seti-node1.0
    mkdir -p ${baseout}/$1/seti-node2.0
    mkdir -p ${baseout}/$1/seti-node2.1
    mkdir -p ${baseout}/$1/seti-node3.0
    mkdir -p ${baseout}/$1/seti-node3.1
    mkdir -p ${baseout}/$1/seti-node4.0
    mkdir -p ${baseout}/$1/seti-node4.1
    mkdir -p ${baseout}/$1/seti-node5.0
    mkdir -p ${baseout}/$1/seti-node5.1
    mkdir -p ${baseout}/$1/seti-node6.0
    mkdir -p ${baseout}/$1/seti-node6.1
    mkdir -p ${baseout}/$1/seti-node7.0
    mkdir -p ${baseout}/$1/seti-node7.1
    mkdir -p ${baseout}/$1/seti-node8.0
fi

scp ${sshid} sonata@seti-node1:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node1.0/ &
scp ${sshid} sonata@seti-node2:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node2.0/ &
scp ${sshid} sonata@seti-node2:/mnt/buf1/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node2.1/ &
scp ${sshid} sonata@seti-node3:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node3.0/ &
scp ${sshid} sonata@seti-node3:/mnt/buf1/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node3.1/ &
scp ${sshid} sonata@seti-node4:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node4.0/ &
scp ${sshid} sonata@seti-node4:/mnt/buf1/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node4.1/ &
scp ${sshid} sonata@seti-node5:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node5.0/ &
scp ${sshid} sonata@seti-node5:/mnt/buf1/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node5.1/ &
scp ${sshid} sonata@seti-node6:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node6.0/ &
scp ${sshid} sonata@seti-node6:/mnt/buf1/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node6.1/ &
scp ${sshid} sonata@seti-node7:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node7.0/ &
scp ${sshid} sonata@seti-node7:/mnt/buf1/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node7.1/ &
scp ${sshid} sonata@seti-node8:/mnt/buf0/turboseti/$1/$1.rawspec.0000.dat ${baseout}/$1/seti-node8.0/ &

wait

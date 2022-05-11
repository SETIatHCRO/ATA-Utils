#!/bin/bash
export HDF5_USE_FILE_LOCKING=FALSE
basein="/mnt/dataz-netStorage-40G/blade"
baseout="/mnt/dataz-netStorage-40G/turboseti"

plotSETI ${basein}/$1/seti-node1.0 -d ${baseout}/$1/seti-node1.0 -o ${baseout}/$1/seti-node1.0 -m 0.3 -z 
plotSETI ${basein}/$1/seti-node2.0 -d ${baseout}/$1/seti-node2.0 -o ${baseout}/$1/seti-node2.0 -m 0.3 -z
plotSETI ${basein}/$1/seti-node2.1 -d ${baseout}/$1/seti-node2.1 -o ${baseout}/$1/seti-node2.1 -m 0.3 -z
plotSETI ${basein}/$1/seti-node3.0 -d ${baseout}/$1/seti-node3.0 -o ${baseout}/$1/seti-node3.0 -m 0.3 -z
plotSETI ${basein}/$1/seti-node3.1 -d ${baseout}/$1/seti-node3.1 -o ${baseout}/$1/seti-node3.1 -m 0.3 -z
plotSETI ${basein}/$1/seti-node4.0 -d ${baseout}/$1/seti-node4.0 -o ${baseout}/$1/seti-node4.0 -m 0.3 -z
plotSETI ${basein}/$1/seti-node4.1 -d ${baseout}/$1/seti-node4.1 -o ${baseout}/$1/seti-node4.1 -m 0.3 -z
plotSETI ${basein}/$1/seti-node5.0 -d ${baseout}/$1/seti-node5.0 -o ${baseout}/$1/seti-node5.0 -m 0.3 -z
plotSETI ${basein}/$1/seti-node5.1 -d ${baseout}/$1/seti-node5.1 -o ${baseout}/$1/seti-node5.1 -m 0.3 -z
plotSETI ${basein}/$1/seti-node6.0 -d ${baseout}/$1/seti-node6.0 -o ${baseout}/$1/seti-node6.0 -m 0.3 -z
plotSETI ${basein}/$1/seti-node6.1 -d ${baseout}/$1/seti-node6.1 -o ${baseout}/$1/seti-node6.1 -m 0.3 -z
plotSETI ${basein}/$1/seti-node7.0 -d ${baseout}/$1/seti-node7.0 -o ${baseout}/$1/seti-node7.0 -m 0.3 -z
plotSETI ${basein}/$1/seti-node7.1 -d ${baseout}/$1/seti-node7.1 -o ${baseout}/$1/seti-node7.1 -m 0.3 -z
plotSETI ${basein}/$1/seti-node8.0 -d ${baseout}/$1/seti-node8.0 -o ${baseout}/$1/seti-node8.0 -m 0.3 -z

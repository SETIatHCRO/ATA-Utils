#!/bin/bash

/usr/bin/firefox pipeline-monitor.hcro.org:8081 &

sleep 1

URLS=(
	cam3cntl.hcro.org
	obs-node1:8081/1
	obs-node1:8081/2
)

for url in ${URLS[@]}
do
	/usr/bin/firefox -new-tab $url
done

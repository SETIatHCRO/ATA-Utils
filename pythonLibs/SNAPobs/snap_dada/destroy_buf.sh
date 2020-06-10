#!/bin/bash

for key in "$@"
do
    dada_db -k $key -d
done

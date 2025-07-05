#!/bin/bash
for i in {1..1000}
do
    python create_aux.py
    echo "Iteration $i completed"
done
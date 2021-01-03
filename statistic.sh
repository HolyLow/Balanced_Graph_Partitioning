#!/bin/bash

task="partition-hybrid"
dir="../snudda_to_pku/networks"
datafile="synapse-gapJunction1000-mat.csv"
#datasets=("tinySim" "1kSim" "1wSim")
datasets=("tinySim" "1000Sim")
#datasets=("1wSim")
points=(2 4 8)
epsilons=(0.9)
for dataset in ${datasets[@]}; do
    for point in ${points[@]}; do
        for epsilon in ${epsilons}; do
            fingerprint="${task}-${dataset}-${point}-${epsilon}"
            log="${dir}/${dataset}/${fingerprint}.log"
            echo "$log"
            cat $log | grep "partition cut_count"
        done
    done
done

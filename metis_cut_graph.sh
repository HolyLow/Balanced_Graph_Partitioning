#!/bin/bash

task="metis-cut-graph"
dir="../snudda_to_pku/networks"
datafile="synapse-undirected-metis.txt"
#datasets=("tinySim" "1kSim" "1wSim")
# datasets=("tinySim")
#datasets=("10000Sim" "20000Sim" "50000Sim" "100000Sim" "200000Sim")
datasets=("200000Sim")
#datasets=("1wSim")
points=(4 8 16)
# epsilons=(0.9)
for dataset in ${datasets[@]}; do
    for point in ${points[@]}; do
    #     for epsilon in ${epsilons}; do
            fingerprint="${task}-${dataset}-partition${point}"
            log="${dir}/${dataset}/${fingerprint}.log"
            cmd="gpmetis ${dir}/${dataset}/${datafile} $point"
            echo "$cmd"
            (time $cmd) 2>&1 | tee $log
    #     done
    done
done

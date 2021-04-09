#!/bin/bash

task="shmetis-cut-hybrid-graph"
dir="../snudda_to_pku/networks"
datafile="scale-80-hybrid-hyper-metis.txt"
#datasets=("tinySim" "1kSim" "1wSim")
# datasets=("tinySim")
datasets=("10000Sim" "20000Sim" "50000Sim" "100000Sim" "200000Sim")
#datasets=("100000Sim" "200000Sim")
#datasets=("1wSim")
points=(4 8 16)
#points=(16)
ubfactor=5
#nruns=2
#ctype=1
#otype=2
#vcycle=3
#vcycle=2
#dbglvl=24
# epsilons=(0.9)
for dataset in ${datasets[@]}; do
    for point in ${points[@]}; do
    #     for epsilon in ${epsilons}; do
            fingerprint="${task}-${dataset}-partition${point}-ctype${ctype}"
            log="${dir}/${dataset}/${fingerprint}.log"
            cmd="shmetis ${dir}/${dataset}/${datafile} $point $ubfactor"
            echo "$cmd"
            (time $cmd) 2>&1 | tee $log
            cp ${dir}/${dataset}/${datafile}.part.${point} ${dir}/${dataset}/${datafile}.part.${point}.shmetis
    #     done
    done
done

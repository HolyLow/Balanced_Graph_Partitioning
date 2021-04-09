#!/bin/bash

task="machine-analyze-cut"
dir="../snudda_to_pku/networks"
uddatafile="synapse-undirected-metis.txt"
hdatafile0="synapse-hyper-metis.txt"
hdatafile1="scale-80-hybrid-hyper-metis.txt"
#datasets=("tinySim" "1kSim" "1wSim")
# datasets=("tinySim")
datasets=("10000Sim" "20000Sim" "50000Sim" "100000Sim" "200000Sim")
#datasets=("10000Sim")
#points=(4 8 16)
points=(16)
# epsilons=(0.9)
machineNum=2
machineScale=10
for dataset in ${datasets[@]}; do
    for point in ${points[@]}; do
    #     for epsilon in ${epsilons}; do
            fingerprint="${task}-${dataset}-partition${point}-machineNum${machineNum}-machineScale${machineScale}"
            log="${dir}/${dataset}/${fingerprint}.log"
            cmd="python metis_graph_helper.py ${dir}/${dataset}/${uddatafile} $point --machineNum $machineNum --machineScale $machineScale --metisDistFile ${dir}/${dataset}/${uddatafile}.part.${point} --metisDistFile ${dir}/${dataset}/${hdatafile0}.part.${point} --metisDistFile ${dir}/${dataset}/${hdatafile1}.part.${point} --hyperMetisGraphFile ${dir}/${dataset}/${hdatafile0} --hyperMetisGraphFile ${dir}/${dataset}/${hdatafile1}"
            echo "$cmd"
            (time $cmd) 2>&1 | tee $log
    #     done
    done
done

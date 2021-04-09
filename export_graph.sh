#!/bin/bash

task="export-metis-graph"
dir="../snudda_to_pku/networks"
datafile="network-pruned-synapses.hdf5"
#datasets=("tinySim" "1kSim" "1wSim")
datasets=("10000Sim" "20000Sim" "50000Sim" "100000Sim" "200000Sim")
#datasets=("1wSim")
# points=(2 4 8)
# epsilons=(0.9)
gapJunctionScale=80
for dataset in ${datasets[@]}; do
    # for point in ${points[@]}; do
    #     for epsilon in ${epsilons}; do
            fingerprint="${task}-${dataset}"
            log="${dir}/${dataset}/${fingerprint}.log"
            cmd="python -m snudda.export_graph ${dir}/${dataset}/${datafile} ${dir}/${dataset}/metis.txt --gapJunctionScale $gapJunctionScale"
            echo "$cmd"
            (time $cmd) 2>&1 | tee $log
    #     done
    # done
done

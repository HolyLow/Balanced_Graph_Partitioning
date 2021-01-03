#!/bin/bash

bin="/home/jmxie/project/metis-5.1.0/build/Linux-x86_64/programs/gpmetis"
dir="../snudda_to_pku/networks"
task="metis-partition"
#datasets=("tinySim" "1kSim" "1wSim")
datafile="network-pruned-synapses.hdf5"
datasets=("tinySim" "1000Sim" "10000Sim" "100000Sim")
# datasets=("tinySim")
points=(4 8 16)
nmachines=(2)
report=""
for dataset in ${datasets[@]}; do
    for point in ${points[@]}; do
        for nmachine in ${nmachines[@]}; do
            fingerprint="${task}-${dataset}-${point}-${nmachine}-disableMulticut"
            log="${dir}/${dataset}/${fingerprint}.log"
            data="${dir}/${dataset}/${datafile}"
            cmd="python metis_cut.py $data $bin $point --nmachine $nmachine"
            (time $cmd) 2>&1 | tee $log

            fingerprint="${task}-${dataset}-${point}-${nmachine}-enableMulticut"
            log="${dir}/${dataset}/${fingerprint}.log"
            data="${dir}/${dataset}/${datafile}"
            cmd="python metis_cut.py $data $bin $point --nmachine $nmachine --multicut"
            (time $cmd) 2>&1 | tee $log

            # report=`echo -e "$report\n$log"`
            # line=`cat $log | grep "Edgecut"`
            # report=`echo -e "$report\n$line"`
            # line=`cat $log | grep "ratio:"`
            # report=`echo -e "$report\n$line"`
        done
    done
done

# echo "STATISTIC REPORT:"
# echo "$report"

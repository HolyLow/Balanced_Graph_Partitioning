#!/bin/bash

bin="/home/jmxie/project/metis-5.1.0/build/Linux-x86_64/programs/gpmetis"
dir="../snudda_to_pku/networks"
# task="metis-partition-hybrid"
# datafile="synapse-gapJunction1000-mat.csv"
task="metis-partition-synapse"
datafile="synapse-mat.csv"
# datasets=("tinySim" "1kSim" "1wSim")
datasets=("tinySim" "1000Sim" "10000Sim")
# datasets=("tinySim")
points=(2 4 8)
report=""
for dataset in ${datasets[@]}; do
    middle_infile="./${task}-${dataset}-graph.txt"
    python transform.py ${dir}/${dataset}/${datafile} $middle_infile numpyAdjacentMatrix2metisGraph
    for point in ${points[@]}; do
        fingerprint="${task}-${dataset}-${point}"
        log="${dir}/${dataset}/${fingerprint}.log"
        outfile="${dir}/${dataset}/${fingerprint}.csv"
        middle_outfile="${middle_infile}.part.${point}"
        cmd="$bin $middle_infile ${point}"
        (time $cmd) 2>&1 | tee $log
        mv $middle_outfile $outfile

        report=`echo -e "$report\n$log"`
        line=`cat $log | grep "Edgecut"`
        report=`echo -e "$report\n$line"`
        line=`cat $log | grep "ratio:"`
        report=`echo -e "$report\n$line"`
    done
    rm $middle_infile
done

echo "STATISTIC REPORT:"
echo "$report"

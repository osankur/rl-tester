MEMLIM=8G
TIMELIM=1800
ulimit -t ${TIMELIM}
N=100
MAXSTEPS=250
p=$1
FILE=examples/ring-protocol/logs/uniform${MAXSTEPS}_p${p}$
cd ../../
rm -f $FILE
python test_generator.py -r examples/ring-protocol/ring_req${p}.v -o examples/ring-protocol/
set -e
for i in $(seq 0 1 $N)
do
    echo "step: $i"
    echo "random_seed: $i " >> $FILE
    python3 tester.py -e uniform -i examples/ring-protocol/ring${p}.py -s examples/ring-protocol/teststrategy_ring_req${p}_objective.aag -r 10000 --max-steps $MAXSTEPS 2>&1 | tee -a $FILE
done
python scripts/parse_log.py $FILE

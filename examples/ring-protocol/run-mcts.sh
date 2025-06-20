set -x 
MEMLIM=8G
TIMELIM=1800
ulimit -t ${TIMELIM}
N=100
MAXSTEPS=250
p=$1
m=30
EPS=25
FILE=examples/ring-protocol/logs/mcts_p${p}_ms${MAXSTEPS}_m${m}_eps${EPS}
rm -f $FILE
touch $FILE
cd ../../
python test_generator.py -r examples/ring-protocol/ring_req${p}.v -o examples/ring-protocol/
set -e
for i in $(seq 0 1 $N)
do
    echo "step: $i"
    echo "random_seed: $i " >> $FILE
    python3 tester.py -e mcts -i examples/ring-protocol/ring${p}.py -s examples/ring-protocol/teststrategy_ring_req${p}_objective.aag -r 10000 -tpgb ${m} -rs greedy --epsilon ${EPS} --max-steps $MAXSTEPS --random_seed $RANDOM 2>&1 | tee -a $FILE
done
python scripts/parse_log.py $FILE

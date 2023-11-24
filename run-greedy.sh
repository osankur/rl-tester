set -x
MEMLIM=8G
TIMELIM=1800
ulimit -t ${TIMELIM}
N=50
MAXSTEPS=250
FILE=logs/greedy_ms${MAXSTEPS}_$1
rm -f $FILE
for i in $(seq 0 1 $N)
do
     echo "step: $i"
     echo "random_seed: $i " >> $FILE
    python3 tester.py -e greedy -i examples/passageway/passageway.py -s examples/passageway/teststrategy_passageway_req_objective.aag -r 10000 --max-steps $MAXSTEPS --epsilon $1 2>&1 | tee -a $FILE
done

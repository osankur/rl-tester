#!/bin/bash
set -x
MEMLIM=8G
TIMELIM=1800
ulimit -t ${TIMELIM}
N=50
MAXSTEPS=250
FILE=logs/log_ms${MAXSTEPS}_greedy$1_tpgb$2
rm -f $FILE
for i in $(seq 0 1 $N)
do
     echo "step: $i"
     echo "random_seed: $i " >> $FILE
     python3 tester.py -e mcts -i examples/passageway/passageway.py -s examples/passageway/teststrategy_passageway_req_objective.aag -r 10000  --max-steps $MAXSTEPS -tpgb $2 -rs greedy --epsilon $1 --random_seed $RANDOM 2>&1 | tee -a $FILE
done

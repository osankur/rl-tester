MEMLIM=8G
TIMELIM=1800
ulimit -t ${TIMELIM}
N=100
MAXSTEPS=250
EPS=12
rollout_policy=greedy # greedy | uniform
greedy_steps_in_tree_policy=0 # 0 or 30
alg=$1 # uniform greedy mcts
set -e
if [ -z "$alg" ]
  then
    echo "Please provide algorithm as first argument: uniform | greedy | mcts"
    exit -1
fi
p=$2
if [ -z "$p" ]
  then
    echo "Please provide number of processes: 4 | 8 | 16 | 32"
    exit -1
fi
# whether we are in faulty mode
f=""
if [ "$3" == "-f" ]
  then
    f="f"
fi

if [ $alg == "mcts" ]; then
  FILE=examples/ring-protocol/logs/${alg}_p${p}_maxsteps${MAXSTEPS}_eps${EPS}_r${rollout_policy}_tpgb${greedy_steps_in_tree_policy}_${f}
  mcts_params="-tpgb ${greedy_steps_in_tree_policy} -rs ${rollout_policy}"
else
  FILE=examples/ring-protocol/logs/${alg}_p${p}_maxsteps${MAXSTEPS}_eps${EPS}_${f}
  mcts_params=""
fi
cd ../../
rm -f $FILE
python test_generator.py -r examples/ring-protocol/ring_req${p}${f}.v -o examples/ring-protocol/
SECONDS=0
for i in $(seq 0 1 $N)
do
    echo "step: $i"
    echo "random_seed: $i " >> $FILE
    # python3 tester.py -e $alg -i examples/ring-protocol/ring${p}${f}.py -s examples/ring-protocol/teststrategy_ring_req${p}${f}_objective.aag -r 10000 --max-steps $MAXSTEPS --epsilon ${EPS} ${mcts_params} 2>&1 | tee -a $FILE
    echo "python3 tester.py -e $alg -i examples/ring-protocol/ring${p}${f}.py -s examples/ring-protocol/teststrategy_ring_req${p}${f}_objective.aag -r 10000 --max-steps $MAXSTEPS --epsilon ${EPS} ${mcts_params} 2>&1 >> $FILE"
    python3 tester.py -e $alg -i examples/ring-protocol/ring${p}${f}.py -s examples/ring-protocol/teststrategy_ring_req${p}${f}_objective.aag -r 10000 --max-steps $MAXSTEPS --epsilon ${EPS} ${mcts_params} >> $FILE 2> /dev/null
done
python scripts/parse_log.py $FILE
echo "Done in ${SECONDS}s"
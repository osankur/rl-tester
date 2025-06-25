MEMLIM=8G
TIMELIM=1800
ulimit -t ${TIMELIM}
N=100
MAXSTEPS=250
EPS=12
rollout_policy=greedy # greedy | uniform
greedy_steps_in_tree_policy=150 # 0 or 30
alg=$1 # uniform greedy mcts
mkdir -p logs
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

if [ $alg == "mcts" ]; then
  FILE=examples/passageway/logs/${alg}_p${p}_maxsteps${MAXSTEPS}_eps${EPS}_r${rollout_policy}_tpgb${greedy_steps_in_tree_policy}_passageway
  mcts_params="-tpgb ${greedy_steps_in_tree_policy} -rs ${rollout_policy}"
else
  FILE=examples/passageway/logs/${alg}_p${p}_maxsteps${MAXSTEPS}_eps${EPS}_passageway
  mcts_params=""
fi
cd ../../
rm -f $FILE
python test_generator.py -r examples/passageway/passageway_req${p}.v -o examples/passageway/
SECONDS=0
#set -x
for i in $(seq 0 1 $N)
do
    echo "step: $i"
    echo "random_seed: $i " >> $FILE
    echo "python3 tester.py -e $alg -i examples/passageway/passageway${p}.py -s examples/passageway/teststrategy_passageway_req${p}_objective.aag -r 10000 --max-steps $MAXSTEPS --epsilon ${EPS} ${mcts_params} 2>&1 >> $FILE"
    python3 tester.py -e $alg -i examples/passageway/passageway${p}.py -s examples/passageway/teststrategy_passageway_req${p}_objective.aag -r 10000 --max-steps $MAXSTEPS --epsilon ${EPS} ${mcts_params} >> $FILE 2> /dev/null
done
python scripts/parse_log.py $FILE
echo "Done in ${SECONDS}s"
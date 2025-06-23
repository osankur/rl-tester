# Ring Protocol Examples
Generate all requirements:

    make

## Uniform testing:
Non-faulty version:

    ./run.sh uniform 4
    ./run.sh uniform 8
    ./run.sh uniform 16
    ./run.sh uniform 32

The faulty version:

    ./run.sh uniform 4 -f
    ./run.sh uniform 8 -f
    ./run.sh uniform 16 -f
    ./run.sh uniform 32 -f

## Greedy algorithm

    ./run.sh greedy 4
    ./run.sh greedy 4 -f
    ...

## MCTS Algorithms
One can modify the following parameters inside the script:
  
    rollout_policy=greedy # greedy | uniform
    greedy_steps_in_tree_policy=0 # 0 or 30

The table below shows the algorithms obtained for each pair of parameters.

|  Parameters | Algorithm   |
|  ---------- | ----------- |
| uniform, 0  | Basic MCTS  |
| greedy, 0   | GRO         |
| greedy, 30  | GTRO        |

Then run the script as follows.

    ./run.sh mcts 4
    ./run.sh mcts 4 -f


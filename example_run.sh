# Maze example: Generate strategies for all requirements and run 100 uniform random tests, each of 500 steps (default is 1000)

python3 test_generator.py -r examples/maze/*.v -o examples/maze/
python3 tester.py -i examples/maze/maze.py -s examples/maze/teststrategy_maze_req_objective.aag -e uniform -r 100 --max-steps 500

# Long maze example: Generate strategies for all requirements and run uniform random tests, eps-greedy strategy with epsilon=.25,
# and MCTS as eps-greedy as tree policy for 10 steps at each node, and eps-greedy as rollout policy

python3 test_generator.py -r examples/long_maze/*.v -o examples/long_maze/
python3 tester.py -i examples/long_maze/long_maze.py -s examples/long_maze/teststrategy_long_maze_req_objective.aag -e uniform -r 100
python3 tester.py -i examples/long_maze/long_maze.py -s examples/long_maze/teststrategy_long_maze_req_objective.aag -e greedy -r 100 --epsilon 25
python3 tester.py -i examples/long_maze/long_maze.py -s examples/long_maze/teststrategy_long_maze_req_objective.aag -e mcts -r 100 -tpgb 10 --rollout-policy greedy --epsilon 25

# Passageway
python3 test_generator.py -r examples/passageway/passageway_req.v -o examples/passageway/
python3 tester.py -e mcts -i examples/passageway/passageway.py -s examples/passageway/teststrategy_passageway_req_objective.aag -r 10000 --max-steps 250 -tpgb 30 -rs greedy --epsilon 0

# Ring protocol
python test_generator.py -r examples/ring-protocol/ring_req.v -o examples/ring-protocol/
python3 tester.py -e greedy --epsilon 25 -i examples/ring-protocol/ring.py -s examples/ring-protocol/teststrategy_ring_req_objective.aag
python3 tester.py -e uniform --epsilon 25 --max-steps 250 -r 10000 -i examples/ring-protocol/ring.py -s examples/ring-protocol/teststrategy_ring_req_objective.aag
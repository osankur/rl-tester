#!/usr/bin/python
import passageway
import sys
maze = passageway.Corridor(3)
if len(sys.argv) >= 2 and sys.argv[1] == "-s":
    maze.run_socket()
else:
    maze.run()

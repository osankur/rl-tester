#!/usr/bin/python3
import sys
import ring
import time
ring = ring.Ring(4, faulty=True)
ring.run()
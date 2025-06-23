#!/usr/bin/python3
import sys
import ring
import time
ring = ring.Ring(16, faulty=True)
ring.run()
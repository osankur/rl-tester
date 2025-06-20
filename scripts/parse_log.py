import re
import fileinput

total = 0
count = 0
for line in fileinput.input():
    mSteps = re.search('.*after ([0-9]+) steps.*', line)
    if mSteps:
      count += 1
      total += int(mSteps.group(1))
print(f"Average nb of steps: {total/float(count)}")
    

# Copyright 2023, Battelle Energy Alliance, LLC
import sys, json

counts = {}
with open('./results.txt', 'r') as in_file:
	for line in in_file:
		count = line.split(' ')[2]
		count = count[:-2] #Remove new line and parenthesis character
#		print(count)
#		sys.exit()
		if count in counts:
			counts[count] += 1
		else:
			counts[count] = 1

jsoned = json.dumps(counts)
with open('./counts.txt', 'w') as outfile:
	json.dump(jsoned, outfile)

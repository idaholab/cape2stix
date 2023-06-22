# Copyright 2023, Battelle Energy Alliance, LLC
import json, sys
listThing = []
with open('./results.json', 'r')as in_file:
	# listThing = [eval(line) for line in in_file if int(line.split(',')[2].replace(')', '')) > 0] # this line is broken
	listThing = [line for line in in_file if int(line.split(',')[2].replace(')', '')) > 0] # this line is also broken
	listThing = sorted(listThing, key = lambda x: x[2])

#with open('sorted.txt', 'w')as outfile:
#	for thing in listThing:
#		outfile.write(f'{json.dump(thing)}\n')

for thing in listThing:
	with open('sorted.txt', 'a') as outfile:
		outfile.write(f'json.dump(thing)\n')

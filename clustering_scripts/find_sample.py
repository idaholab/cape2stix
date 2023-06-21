# Copyright 2023, Battelle Energy Alliance, LLC
import json, os, sys
search_id = 'malware--fde81448-ac55-4d27-87ee-1bc4501514e7'

with open(f'./just_rels.json') as input:
	something  = json.load(input)
#	print(something)
#	for thing in something:
#		print(thing)
	if search_id in something:
		print("We found it!!!")
	else:
		print("Very sad, nonexistant")

# Copyright 2023, Battelle Energy Alliance, LLC
import json 

path = './updated_json/just_rels.json'

sample1 = 'malware--ed580f76-b7b4-4328-bf1d-5590eb196e10'
sample2 = 'malware--f7bc49e3-ed0c-4b6f-8591-3699b8b2dec0'

with open(path) as f:
	rels = json.load(f)

counter = 0
for obj in rels[sample1]:
	if obj in rels[sample2]:
		counter += 1
print(f"Total rels that are the same: {counter}")

'''
counter = 0
for obj in rels[sample2]:
	counter += 1

print(f"Total rels of df sample: {counter}")
'''

# Copyright 2023, Battelle Energy Alliance, LLC
import json
import logging
import os
#from tqdm import tqdm
path = './updated_json/just_rels.json'
try:
	if os.path.isfile('./results.json'):
		os.remove('./results.json')
except Exception as e:
	logging.exception(e)

with open(path, 'r') as file:
	data = json.load(file)

#counted_list = []
outfile = open('./results.json', 'a')

has_been = {}
for malware in data:
	for malware_comp in data:
		types = {}
		counter = 0
		if malware == malware_comp or f'{malware}-{malware_comp}' in has_been or f'{malware_comp}-{malware}' in has_been:
			continue #skipping self comparisons and already compared samples
		data_set = set(data[malware_comp])
		for rel in data[malware]:
			if rel in data_set:
				the_type = rel.split('--')[0]
			#	print(f'The type is {the_type}')
				if the_type in types:
					types[the_type] += 1
				else:
					types[the_type] = 1
			#	if rel == rel_comp:
				counter += 1
		temp = (malware, malware_comp, counter, types)
		#counted_list.append(temp) #Creating a list of tuples that have the malware samples that were compared and a number of shared relationships
		#with open('./results.txt', 'a') as outfile:
		#	outfile.write(f'{temp}\n')
		has_been[f'{malware}-{malware_comp}'] = None
		del(data_set)
		outfile.write(f'{json.dumps(temp)}\n')
		outfile.flush()
		del(temp)
		del(types)
print('For loop completed')
outfile.close()

#with open('./results.txt', 'w') as output_file:#
#	for tuple in counted_list:
#		entry = ' '.join(str(x) for x in tuple)
#		output_file.write(line + '\n')
#with open('./results.json', 'w') as outfile:
#	json.dump(has_been, outfile)

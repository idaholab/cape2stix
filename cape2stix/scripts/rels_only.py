# Copyright 2023, Battelle Energy Alliance, LLC
import json

input = "merged_fresh.json"

with open(input) as f:
    data = json.load(f)
    
    
malwares = {}
for i in data['objects']:
    _id = i['id']
    if 'relationship--' in _id and 'malware--' in i['source_ref']:
        src = i['source_ref']
        target = i['target_ref']
        if src not in malwares:
            malwares[src] = set([target])
        else:
            malwares[src].add(target)
            
print(len(malwares))
for k,v in malwares.items():
    malwares[k] = list(v)
with open('just_rels.json', 'w') as f:
    json.dump(malwares, f)
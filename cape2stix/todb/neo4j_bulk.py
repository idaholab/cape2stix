# Copyright 2023, Battelle Energy Alliance, LLC
"""
file: chatgpt-example1.py
auth: rafer cooley, michael cutshaw with assistance from chatgpt
date: 03/01/2023

In this script, we first set up a Neo4j driver and load the STIX 2 bundle from a JSON file. We then define a Cypher query that will create Neo4j nodes for STIX 2 objects. Finally, we define a function that will process the STIX 2 objects and create Neo4j nodes using the Cypher query.

We then start a Neo4j session and use the process_stix2_objects function to load the STIX 2 objects into Neo4j. The process_stix2_objects function loops over each STIX 2 object in the bundle, extracts its type and properties, and uses the Cypher query to create a corresponding Neo4j node.

Note that this script assumes that you have the neo4j module installed and the APOC library installed and configured on your Neo4j server, with the following specific settings (see docker-compose file environment vars):
    - NEO4J_dbms_security_procedures_unrestricted="apoc.*"
"""

import neo4j
import json
from pathlib import Path
from tqdm import tqdm
import argparse

delete_all_query = """
MATCH (n)-[r]-()

CALL { WITH r
DELETE r
} IN TRANSACTIONS OF 10000 ROWS

WITH distinct n
CALL { WITH n
DELETE n
} IN TRANSACTIONS OF 10000 ROWS;
"""

object_cypher_query = """
        UNWIND $objects AS object
        WITH object,
            object.type AS type,
            coalesce(object.properties, {}) AS properties
        WITH object,
            type,
            properties,
            CASE WHEN type IS NULL THEN 'Missing type property'
                WHEN properties IS NULL THEN 'Missing properties'
                ELSE NULL
            END AS error
        CALL apoc.create.node(type, properties) YIELD node
        RETURN node, error
        """
        
rel_cypher_query = """
UNWIND $objects AS object
MATCH (source:stixnode WHERE source.id = object.source_ref )
USING INDEX source:stixnode(id)
MATCH (target:stixnode where target.id = object.target_ref)
USING INDEX target:stixnode(id)

CALL apoc.create.relationship(source, object.rel_type, object.rel_properties, target) YIELD rel
RETURN rel
"""
dedup = set()
# Define function to process STIX 2 objects
def process_stix2_objects(tx, objects):
    new_obj_list = []
    new_rel_list = []

    for obj in objects:
        if obj["id"] in dedup:
            continue
        else:
            dedup.add(obj["id"])
        # Check if object is a relationship
        if obj["type"] == "relationship":
            # Extract relationship properties
            rel_type = obj.pop("relationship_type", "RELATED_TO")
            source_ref = obj.pop("source_ref")
            target_ref = obj.pop("target_ref")
            rel_properties = obj.copy()
            rel_properties.pop("type", None)
            for k, v in rel_properties.items():
                if isinstance(v, (list, dict)):
                    rel_properties[k] = json.dumps(v)
            new_rel_list.append(
                {
                    "source_ref": source_ref,
                    "target_ref": target_ref,
                    "rel_type": rel_type,
                    "rel_properties": rel_properties,
                }
            )

        else:
            # Extract STIX 2 object type and properties
            obj_properties = obj.copy()
            obj_properties.pop("type")
            for k, v in obj_properties.items():
                if isinstance(v, (list, dict)):
                    obj_properties[k] = json.dumps(v)

            # Create Neo4j node for STIX 2 object
            obj = {"type": ['stixnode', obj["type"]], "properties": obj_properties}
            new_obj_list.append(obj)

    # Create Neo4j nodes for non-relationship objects
    for obj_batch in batch(new_obj_list):
        session.run(
            object_cypher_query,
            objects=obj_batch
        )
    # Create Neo4j relationship for relationship object
    for obj_batch in batch(new_rel_list):
        session.run(
            rel_cypher_query,
            objects=obj_batch,
        )

def batch(iterable, n=1000):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]
        
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("user")
    parser.add_argument("password")
    parser.add_argument("--delete", action="store_true", help="delete everything first then load")

    return parser.parse_args()
        
if __name__ == "__main__":
    args = parse_args()
    input_dir = Path(args.input_dir)

    driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", auth=(args.user, args.password))
    
    if args.delete:
        with driver.session() as session:
            session.run(delete_all_query)

    # Create or delete database as needed
    # with driver.session() as session:
    #     results1 = session.run("SHOW DATABASES")
    #     print("after running show db")
    

    # Load STIX 2 bundle from JSON file
    with driver.session() as session:
        session.run('CREATE INDEX stixnode_id IF NOT EXISTS FOR (n:stixnode) ON n.id')
        for file_path in tqdm(input_dir.iterdir(), total=len(list(input_dir.iterdir()))):
            file_path = input_dir.joinpath(file_path)
            with open(file_path, "r") as f:
                try:
                    bundle = json.load(f)
                except Exception as e:
                    print(file_path, 'failed to load as json')
                    
            # Start Neo4j session and load STIX 2 objects
            process_stix2_objects(session, bundle["objects"])

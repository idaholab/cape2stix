"Measure the total connectivity of a directory of STIX bundles"
import sys
import os
import logging
import argparse
import json
import networkx as nx
from networkx.algorithms import approximation
import matplotlib.pyplot as plt
from collections import Counter
from pprint import pformat
from tqdm import tqdm

# pylint: disable=logging-not-lazy,broad-exception-caught,trailing-whitespace,logging-fstring-interpolation

class Aggregater:
    "Class to aggregate stix results"
#-------------------

    def __init__(self, target=None,verbose=False):
        self.target = target
        self.verbose = verbose
        self.edges = set()
        self.nodes = set()
        self.e_dups = []
        self.n_dups = []
        self.types = []

    def agg_load(self):
        "Runs aggregation on target"
        if os.path.isfile(self.target):
            logging.info("Aggregating target file.")
            self.agg_file(self.target)
        elif os.path.isdir(self.target):
            logging.info("Aggregating target directory. This may take awhile. . .")
            self.agg_dir()
 
#-------------------

    def agg_file(self, file):
        "Launches aggregation for a single file"
        if ".gitkeep" in file:
            return
        try:
            with open(file, encoding="UTF-8") as f:
                bundle = json.load(f)
        except Exception as file_err:
            logging.error("Exception in file " + file)
            logging.exception(file_err)

        temp_e = set()
        temp_n = set()
        for obj in bundle["objects"]:
            
            if obj["type"] == "relationship":
                self.edges.add((obj["source_ref"], obj["target_ref"]))
                temp_e.add(obj["id"])

            else:
                self.nodes.add((obj["id"], obj["type"]))
                temp_n.add(obj["id"])
    
        # removes any strange duplicates in single bundle
        self.e_dups.extend(list(temp_e))
        self.n_dups.extend(list(temp_n))

#-------------------

    def agg_dir(self):
        "Launches aggregation for a directory"
        for file in tqdm(os.listdir(self.target)):
            self.agg_file(os.path.join(self.target,file))

#-------------------

    def count_unique_objects(self):
        "gets number of unique types and logs stats"
        for _, typ in self.nodes:
            self.types.append(typ)
        
        stats = f'''
        Number of Total Edges: {len(self.e_dups)}
        Number of Deduplicated Edges: {len(self.edges)}
        Number of Total Nodes: {len(self.n_dups)}
        Number of Deduplicated Nodes: {len(self.nodes)}
        Types: {pformat(Counter(self.types))}'''
        
        logging.info(stats)
        if not self.verbose:
            print(stats) # makes sure to print the stats even if not run as verbose

#-------------------
    def analysis_connect(self):
        "Runs Connectivity analysis on class"
        #TODO: I want number of subgraphs, metrics, all that
        # nx.cluster.average_clustering(G) is like: if a->b,b->c, how often is a->c 
        self.nodes={n for (n, t) in self.nodes}
        G = nx.DiGraph()
        G.add_nodes_from(self.nodes)
        G.add_edges_from(self.edges)

        # make an undirected copy of the digraph

        # extract subgraphs
        sub_graphs = nx.weakly_connected_components(G)
        print(len(list(sub_graphs)))
        
        # print((nx.density(G)))
        # approximation.node_connectivity(G)
#================================================

def parse_args(args):
    "Helper function for parsing arguments from the command line for connectivity.py"
    parser = argparse.ArgumentParser(
        description="Measure the total connectivity of a directory of STIX bundles")
    parser.add_argument(
        "-t",
        "--target",
        type=str,
        dest="target",
        action="store",
        help="path to file or directory for analysis",
    )
    parser.add_argument(
        "--log_level",
        choices=["debug", "info", "warn", "default"],
        metavar="{debug, info, warn}",
        default="default",
        help="defines lowest level of log recorded",
    )
    parser.add_argument(
        "--verbose", help="print logs to console", action="store_true")
    return parser.parse_args(args)
#================================================

if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    if not args.verbose:
        log_level = {"debug": logging.DEBUG, "info": logging.INFO, "warn": logging.WARN, "default": logging.NOTSET}[
        args.log_level
        ]
        logging.basicConfig(filename='stats.log', encoding='utf-8', level=log_level)
    try:
        if args.target is None:
            args.target = "output"
        Analysis = Aggregater(args.target, args.verbose)
        Analysis.agg_load()
        # Analysis.count_unique_objects()
        Analysis.analysis_connect()

    except Exception as err:
        logging.exception(err)
        exit()

        
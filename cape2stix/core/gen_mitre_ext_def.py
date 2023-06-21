# Copyright 2023, Battelle Energy Alliance, LLC
import json
import stix2
import logging
from hashlib import sha256
from stix2 import Identity, ExtensionDefinition, MemoryStore
from stix2.serialization import STIXJSONEncoder
from genson import SchemaBuilder
import os
from uuid import uuid4
import argparse
from pprint import pprint
from collections.abc import KeysView


def get_custom_props(obj):
    if not obj.has_custom:
        return {}
    else:
        return {key: val for key, val in obj.items() if key not in obj._properties}


if __name__ == "__main__":
    input_file = "../sup_files/enterprise-attack.json"
    with open(input_file) as f:
        data = json.load(f)
    data = stix2.parse(data, allow_custom=True)
    groups = {}
    if isinstance(data, stix2.v21.bundle.Bundle):
        objects = data.objects
    elif isinstance(data, list):
        objects = data
    l = {}
    builder = SchemaBuilder()
    builder.add_schema({"type": "object", "properties": {}})
    for obj in objects:
        if isinstance(obj, dict):
            continue
        builder.add_object({k.lower(): v for k, v in get_custom_props(obj).items()})

    print({"schema": json.dumps(builder.to_schema())})

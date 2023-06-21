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


class ExtensionJSONEncoder(STIXJSONEncoder):
    def default(self, obj):
        if isinstance(obj, KeysView):
            return list(obj)
        else:
            return super().default(obj)


def gen_uuid(string):
    """
    Generates the ID field for a stix object, using UUIDv4.
    param string -- type of the object to prepend to the uuid.

    """
    return f"{string}--{uuid4()}"


def hash_list(list_data):
    m = sha256()
    m.update("".join(sorted(list(set(list_data)))).encode())
    return str(m.hexdigest())


class StixLoader:
    """Class to manage creation, adding to and writing out our stix data."""

    def __init__(self, file_path=None, allow_custom=True):
        logging.debug("init")
        self.allow_custom = allow_custom
        self.create_bundle(file_path=file_path)

    def create_bundle(self, file_path=None):
        logging.info("creating bundle")
        self.ms = MemoryStore(allow_custom=self.allow_custom)
        self.ms_source = self.ms.source
        self.ms_sink = self.ms.sink
        if file_path is not None:
            self.ms.load_from_file(file_path)

    def stix_out(self, name=None):
        if not self.stix_loader:
            return None
        if name is None:
            logging.error("No name for STIX output.")
        else:
            path_name = f"{name}.json"
        self.sl.write_out(os.path.join(self.dir, path_name))

    def merge(self, items):
        logging.debug("Merging:")
        for item in items:
            logging.debug(f"Adding: {item}")
            self.ms_sink.add(item)

    def add_item(self, items):
        self.ms_sink.add(items, version=2.1)

    def get_sink_data(self):
        return self.ms.sink._data

    def write_out(self, path_):
        # We are not using the built in .save_to_file as its slow for some reason
        logging.debug(f"attempting to write_out to path: {path_}")
        logging.info("Starting save to file")
        # self.ms.save_to_file(path)
        d = {
            "type": "bundle",
            "id": gen_uuid("bundle"),
            "objects": [item for item in self.ms_source.query()],
        }

        if d["objects"]:
            logging.debug(d)
            logging.debug(path_)
            with open(path_, "w") as f:
                json.dump(d, f, cls=STIXJSONEncoder)
            logging.info(
                f"Finished save to file, number of objects: {len(list(self.ms_source.query()))}"
            )


class ExtensionFixer:
    def __init__(
        self,
        input_data=None,
        input_file=None,
        gen_only=False,
        identity_name="AMA",
        extensions={},
    ):
        self.data = input_data
        self.input_file = input_file
        self.identity_name = identity_name
        self.extensions = extensions
        self.output_objects = []
        self.gen_only = gen_only
        # lookup val will be hashed sorted type key names.

    def run(self):
        if self.input_file is not None:
            with open(self.input_file) as f:
                data = json.load(f)
            data = self.pre_fix(data)
            self.data = stix2.parse(data, allow_custom=True)
        if self.data is not None:
            self.generate_groups()
            self.generate_extensions()
            if not self.gen_only:
                self.replace_w_extensions()
                return self.output_objects
            else:
                return self.extensions
        else:
            raise Exception("No input data, cannot proceed")

    def pre_fix(self, data):
        if "type" in data and data["type"] == "bundle":
            for obj in data["objects"]:
                if "extensions" in obj and isinstance(obj["extensions"], dict):
                    to_del = []
                    for k, v in obj["extensions"].items():
                        if not isinstance(v, dict):
                            to_del.append(k)
                    for item in to_del:
                        del obj["extensions"][item]
                    if len(obj["extensions"]) == 0:
                        del obj["extensions"]
        return data

    def upsert_group(self, key, props):
        if key not in self.groups:
            builder = SchemaBuilder()
            builder.add_schema({"type": "object", "properties": {}})
            builder.add_object({k.lower(): v for k, v in props.items()})
            self.groups[key] = {"schema": builder, "props": props.keys()}
        else:
            self.groups[key]["schema"].add_object(
                {k.lower(): v for k, v in props.items()}
            )

    def generate_groups(self):
        self.groups = {}
        if isinstance(self.data, stix2.v21.bundle.Bundle):
            self.objects = self.data.objects
        elif isinstance(self.data, list):
            self.objects = self.data
        else:
            logging.critical("Parse data is not a list of STIX 2.1 bundle")
        for obj in self.objects:
            props = self.get_custom_props(obj)
            if props == {}:
                continue
            else:
                self.upsert_group(hash_list(sorted(props.keys())), props)

    def generate_extensions(self):
        self.identity = Identity(name=self.identity_name)
        self.output_objects.append(self.identity)

        for group_key, group_val in self.groups.items():
            ext_def = ExtensionDefinition(
                created_by_ref=self.identity,
                name=f"{self.identity_name}_{group_key}",
                extension_types=["property-extension"],
                # extension_properties=[prop.lower() for prop in group_val["props"]],
                version="1.0",
                schema=group_val["schema"].to_schema(),
                description="Autogenerated extension definition",
            )
            self.output_objects.append(ext_def)
            self.extensions[group_key] = {
                "ext": ext_def,
                "org_props": group_val["props"],
            }

    def replace_w_extensions(self):
        for obj in self.objects:
            new_obj = self.replace_w_extensions_base(
                obj, self.get_extension_for_obj(obj)
            )
            self.output_objects.append(new_obj)

    def replace_w_extensions_base(self, obj, ext):
        if ext is None:
            return obj
        org_props = ext["org_props"]
        obj_dict = {k: v for k, v in obj.items()}
        extension_props = {}
        for prop in org_props:
            if prop in obj_dict:
                extension_props[prop.lower()] = obj_dict[prop]
                del obj_dict[prop]
        obj_dict["extensions"] = {
            ext["ext"].id: {"extension_type": ext.extension_types[0], **extension_props}
        }
        return stix2.parse(obj_dict)

    def get_extension_for_obj(self, obj):
        key = self.obj_props_to_key(obj)
        if key is None:
            return None
        return self.extensions[key]

    def replace_w_extensions_spec(self, obj, ext):
        return self.replace_w_extensions_base(obj, ext)

    def get_custom_props(self, obj):
        if not obj.has_custom:
            return {}
        else:
            return {key: val for key, val in obj.items() if key not in obj._properties}

    def obj_props_to_key(self, obj):
        props = self.get_custom_props(obj)
        print(sorted(props.keys()))
        if props == {} or props == []:
            return None
        return hash_list(sorted(props.keys()))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("in_file")
    parser.add_argument("in_outfile")
    parser.add_argument("--gen_only", action="store_true")

    args = parser.parse_args()
    es = ExtensionFixer(input_file=args.in_file, gen_only=args.gen_only)
    fixed_stix = es.run()
    if args.gen_only:
        for k, v in fixed_stix.items():
            fixed_stix[k]["ext"] = json.loads(json.dumps(v["ext"], cls=STIXJSONEncoder))
        pprint(fixed_stix)
    else:
        sl = StixLoader()
        sl.merge(fixed_stix)
        sl.write_out(args.in_outfile)

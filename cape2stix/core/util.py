# Copyright 2023, Battelle Energy Alliance, LLC
import asyncio
from stix2.canonicalization.Canonicalize import canonicalize
from functools import wraps
from time import time
import logging
from cape2stix.core.extension_data import (
    staticidentities,
    staticextensions,
    staticextensionidentitymapping,
)
from hashlib import sha256
from stix2 import Relationship
import uuid
from stix2.base import _make_json_serializable
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
import shutil
import asyncio
import datetime
import stix2

"Utility functions"

# This is an atomic write function, will only work for writing.
@contextmanager
def openaw(path, mode="w+b"):
    with NamedTemporaryFile(mode, delete=False) as f:
        try:
            yield f
        except Exception as e:
            shutil.remove(f.name)
            raise e
        shutil.move(f.name, path)


def create_object(cls, *args, custom_object=True, force_uuidv5=False, **kwargs):
    """
    Function to use to generate stix objects, allows us to manage logging/custom objects at a higher level.
    """
    if not custom_object:
        for key in list(kwargs.keys()):
            if key not in cls._properties:
                del kwargs[key]
    else:
        if "allow_custom" in kwargs:
            logging.error(
                f'"allow_custom" should not be specified in object creation! obj: {kwargs}'
            )
        else:
            kwargs["allow_custom"] = True
    obj = cls(*args, **kwargs)
    
    if force_uuidv5 and obj.id.split('--')[1][14] == '4':
        # NOTE: this is a lame hack ftm.
        id_ = generate_UUIDv5(obj)
        obj = cls(*args, id=id_, **kwargs)
    return obj


def keys_to_object(d: dict, cls, keys: list, **kwargs):
    keys_for_new_obj = {}
    for inkey, outkey in keys:
        if inkey in d and d[inkey] != "":
            keys_for_new_obj[outkey] = d[inkey]
    if keys_for_new_obj != {}:
        obj = create_object(cls, **keys_for_new_obj, **kwargs)
        return obj


def generate_UUIDv5(stixObj):
    """
    Generate a UUIDv5 for this object, using its "ID contributing
    properties".
    :return: The ID, or None if no ID contributing properties are set
    """
    SCO_DET_ID_NAMESPACE = uuid.UUID("00abedb4-aa42-466c-9c01-fed23315a9b7")

    id_ = None
    json_serializable_object = {}

    if hasattr(stixObj, "_id_contributing_properties"):
        contributing_props = stixObj._id_contributing_properties
    elif stixObj.type == "relationship":
        contributing_props = ["relationship_type", "source_ref", "target_ref"]
    elif stixObj.type == "location":
        contributing_props = ["name", "country"]

    for key in contributing_props:
        if key in stixObj:
            obj_value = stixObj[key]

            serializable_value = _make_json_serializable(obj_value)

            json_serializable_object[key] = serializable_value

    if json_serializable_object:

        data = canonicalize(json_serializable_object, utf8=False)
        uuid_ = uuid.uuid5(SCO_DET_ID_NAMESPACE, data)
        id_ = "{}--{}".format(stixObj._type, str(uuid_))

    return id_


def timing(func):
    """
    Timing decrorator function.
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def wrap(*args, **kwargs):
            start = time()
            
            result = await func(*args, **kwargs)
            end = time()
            logging.info(f"func:{func.__name__} took: {end - start:2.5f} sec")
            return result
    else:
        @wraps(func)
        def wrap(*args, **kwargs):
            start = time()
            result = func(*args, **kwargs)
            end = time()
            logging.info(f"func:{func.__name__} took: {end - start:2.5f} sec")
            return result

    return wrap


def gen_uuid(string):
    """
    Generates the ID field for a stix object, using UUIDv4.
    param string -- type of the object to prepend to the uuid.

    """
    return f"{string}--{uuid.uuid4()}"


# NOTE: might just want to get rid of this one. NEVER MIND, need to pay attention to return types.
def genRel(src, target, rel_type, custom_object=True, **kwargs):
    """
    Function to help building relationships for our memory store from source to destination.

    ex: genRel(product, cve, 'affected-by', sl)

    param src -- source of relationship
    param target -- target of relationship
    param rel_type -- type of relationship
    param sl -- stix_loader class
    """
    return create_object(
        Relationship,
        source_ref=src,
        relationship_type=rel_type,
        target_ref=target,
        custom_object=custom_object,
        **kwargs,
    )


def genRelMany(srcs, targets, rel_type, custom_object=True, **kwargs):
    """
    Function to help building relationships for our memory store from one more sources to one or more destinations.

    ex: genRel(product, cves, 'affected-by', sl)

    param srcs -- source(s) of relationship
    param targets -- target(s) of relationship
    param rel_type -- type of relationship

    returns: list of relationships
    """
    rel_list = []
    if not isinstance(srcs, list):
        srcs = [srcs]
    if not isinstance(targets, list):
        targets = [targets]
    for src in srcs:
        for target in targets:
            rel_list.append(
                create_object(
                    Relationship,
                    source_ref=src,
                    relationship_type=rel_type,
                    target_ref=target,
                    custom_object=custom_object,
                    **kwargs,
                )
            )

    return rel_list


def fixdate(starttime):
    """
    Helper function to fix timestamp strings from CAPE report to desired STIX format.

    param starttime -- the passed in timestamp

    return thistime -- returns the properly formatted timestamp to populate stix package objects
    """
    timestarted = datetime.datetime.strptime(str(starttime), "%Y-%m-%d %H:%M:%S")
    thistime = str(timestarted.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return str(thistime)


def hash_list(list_data):
    m = sha256()
    m.update("".join(sorted(list(set(list_data)))).encode())
    return str(m.hexdigest())


class ExtensionHelper:
    def __init__(self, identity_name="AMA", extensions={}): 
        self.extensions = staticextensions
        self.identities = staticidentities
        self.mapping = staticextensionidentitymapping
        self.used = []
        # lookup val will be hashed sorted type key names.

    def get_used_extensions(self):
        objs_list = []
        used_identities = []
        for name in self.used:
            objs_list.append(stix2.parse(self.extensions[name]["ext"]))
            if self.mapping[name] not in used_identities:
                objs_list.append(stix2.parse(self.identities[self.mapping[name]]))
                used_identities.append(self.mapping[name])
        return objs_list

    def get_extension(self, name):
        if name in self.extensions:
            if name not in self.used:
                self.used.append(name)
            dict_ext = self.extensions[name]
            dict_ext["ext"] = stix2.parse(dict_ext["ext"])
            return dict_ext
        else:
            logging.error(f"No extension for key {name}")
            return None

    def replace_w_extensions_base(self, obj, ext_name):
        ext = self.get_extension(ext_name)
        if ext is None:
            return obj
        org_props = ext["org_props"]
        ext = ext["ext"]
        obj_dict = {k: v for k, v in obj.items()}
        extension_props = {}
        for prop in org_props:
            if prop in obj_dict:
                extension_props[prop.lower()] = obj_dict[prop]
                del obj_dict[prop]
        obj_dict["extensions"] = {
            ext.id: {"extension_type": ext.extension_types[0], **extension_props}
        }
        return stix2.parse(obj_dict)

    def replace_w_extensions_spec(self, obj, ext_name):
        return self.replace_w_extensions_base(obj, ext_name)

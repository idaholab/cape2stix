# Using functions from medallion/backends/mongodb_backend.py to initialize mongodb database for use by taxii
from pymongo import  IndexModel, MongoClient, ASCENDING
import os, json, calendar, pytz
import datetime as dt

def find_manifest_entries_for_id(obj, manifest):
    for m in manifest:
        if m["id"] == obj["id"]:
            if "modified" in obj:
                if m["version"] == obj["modified"]:
                    return m
            else:
                # handle data markings
                if m["version"] == obj["created"]:
                    return m
def string_to_datetime(timestamp_string):
    """Convert string timestamp to datetime instance."""
    try:
        return dt.datetime.strptime(timestamp_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return dt.datetime.strptime(timestamp_string, "%Y-%m-%dT%H:%M:%SZ")
      
def datetime_to_float(dttm):
    """Given a datetime instance, return its representation as a float"""
    # Based on this solution: https://stackoverflow.com/questions/30020988/python3-datetime-timestamp-in-python2
    if dttm.tzinfo is None:
        return calendar.timegm(dttm.utctimetuple()) + dttm.microsecond / 1e6
    else:
        return (dttm - dt.datetime(1970, 1, 1, tzinfo=pytz.UTC)).total_seconds()
# def init_mongodb():
#     client = connect_to_client()
#     print(client)
#     build_new_mongo_databases_and_collection(client)
#     add_api_root(client)

def connect_to_db(url):
    return MongoClient(url)

def load_data_from_file(filename):
    # try:
    #     if isinstance(filename, string_types):
    #         with io.open(filename, "r", encoding="utf-8") as infile:
    #             json_data = json.load(infile)
    #     else:
    #         json_data = json.load(filename)
    # except Exception as e:
    #     print("Problem loading initialization data from {0}".format(filename), 408, e)
    print(filename)
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            json_data = json.load(f)    
    return json_data

def initialize_mongodb_with_data(filename, client):
    json_data = load_data_from_file(filename)
    if "/discovery" in json_data:
        db = client["discovery_database"]
        db["discovery_information"].insert_one(json_data["/discovery"])
    else:
        print("No discovery information provided when initializing the Mongo DB")
    api_root_info_db = db["api_root_info"]
    for api_root_name, api_root_data in json_data.items():
        if api_root_name == "/discovery":
            continue
        url = list(filter(lambda a: api_root_name in a, json_data["/discovery"]["api_roots"]))[0]
        api_root_data["information"]["_url"] = url
        api_root_data["information"]["_name"] = api_root_name
        api_root_info_db.insert_one(api_root_data["information"])
        client.drop_database(api_root_name)
        api_db = client[api_root_name]
        if api_root_data["status"]:
            api_db["status"].insert_many(api_root_data["status"])
        else:
            api_db.create_collection("status")
        api_db.create_collection("collections")
        api_db.create_collection("objects")
        for collection in api_root_data["collections"]:
            collection_id = collection["id"]
            objects = collection["objects"]
            manifest = collection["manifest"]
            # these are not in the collections mongodb collection (both TAXII and Mongo DB use the term collection)
            collection.pop("objects")
            collection.pop("manifest")
            api_db["collections"].insert_one(collection)
            for obj in objects:
                obj["_collection_id"] = collection_id
                obj["_manifest"] = find_manifest_entries_for_id(obj, manifest)
                obj["_manifest"]["date_added"] = datetime_to_float(string_to_datetime(obj["_manifest"]["date_added"]))
                obj["_manifest"]["version"] = datetime_to_float(string_to_datetime(obj["_manifest"]["version"]))
                obj["created"] = datetime_to_float(string_to_datetime(obj["created"]))
                if "modified" in obj:
                    # not for data markings
                    obj["modified"] = datetime_to_float(string_to_datetime(obj["modified"]))
                api_db["objects"].insert_one(obj)
            id_index = IndexModel([("id", ASCENDING)])
            type_index = IndexModel([("type", ASCENDING)])
            collection_index = IndexModel([("_collection_id", ASCENDING)])
            date_index = IndexModel([("_manifest.date_added", ASCENDING)])
            version_index = IndexModel([("_manifest.version", ASCENDING)])
            date_and_spec_index = IndexModel([("_manifest.media_type", ASCENDING), ("_manifest.date_added", ASCENDING)])
            version_and_spec_index = IndexModel([("_manifest.media_type", ASCENDING), ("_manifest.version", ASCENDING)])
            collection_and_date_index = IndexModel([("_collection_id", ASCENDING), ("_manifest.date_added", ASCENDING)])
            api_db["objects"].create_indexes(
                [id_index, type_index, date_index, version_index, collection_index, date_and_spec_index,
                    version_and_spec_index, collection_and_date_index]
            )

if __name__ == "__main__":
    url = "mongodb://root:example@inl604320:27017/"
    mongo_client = connect_to_db(url)
    initialize_mongodb_with_data('default_data.json', mongo_client)
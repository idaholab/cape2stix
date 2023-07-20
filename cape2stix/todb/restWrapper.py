# Copyright 2023, Battelle Energy Alliance, LLC
import requests
import logging
import json

from cape2stix.todb import schema

# Written orginally by Taylor McCampbell <taylor.mccampbell@inl.gov>, modified by Michael Cutshaw
class RestAPIWrapper:
    def __init__(  # nosec B107
        self,
        host="localhost",
        port="2480",
        user="root",
        password="toor",
        db="test",
        proto="http",
    ):
        self.db = db
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.api_url = f"{proto}://{self.host}:{self.port}"
        self.auth = (self.user, self.password)

    def connectToDB(self):
        url = f"{self.api_url}/connect/{self.db}"
        try:
            response = requests.get(url, auth=self.auth) #nosec
        except Exception as e:
            logging.error("Problem with http request")
            logging.exception(e)

        return response

    def query(self, queryString, limit=2147483647):
        url = f"{self.api_url}/query/{self.db}/sql/{queryString}/{limit}"
        try:
            response = requests.get(url, auth=self.auth) #nosec
        except Exception as e:
            logging.error("Problem with http request")
            logging.exception(e)

        return response.json()

    def batchQuery(self, queries, lang_type="sql", error_msg="Batch error"):

        batch_data = {"transaction": False, "operations": []}
        for query in queries:
            batch_data["operations"].append(
                {"type": "cmd", "language": lang_type, "command": query}
            )

        resp = self.makeRequest(
            f"batch/{self.db}/batch", json=batch_data, error_msg=error_msg
        )
        if resp is not None and "error" in resp.json():
            logging.exception(resp.json())

    def listDatabases(self):
        jsonResponse = self.makeRequest("listDatabases", method="GET").json()
        return jsonResponse["databases"]

    def checkDBExists(self):
        return self.db in self.listDatabases()

    def deleteDB(self):
        logging.info("Deleting database!")
        return self.makeRequest(
            f"database/{self.db}",
            method="DELETE",
            error_msg="There was a problem with database deletion",
        )

    def makeRequest(
        self, suburl, method="POST", error_msg="Problem making request", **kwargs
    ):
        url = f"{self.api_url}/{suburl}"
        try:
            return requests.request(method, url=url, auth=self.auth, **kwargs)
        except Exception as e:
            logging.error(error_msg)
            logging.exception(e)

    def createDB(self):
        logging.info("Creating database!")
        return self.makeRequest(
            f"database/{self.db}/plocal",
            error_msg="There was a problem with database creation",
        )

    def createSchema(self):
        # This function relies on a file being in the same directory called schema.py that contains all nodes and edges that could be entered in the database
        logging.info("Creating schema!")
        node_queries = [
            f"create class {node_class} extends V" for node_class in schema.nodes
        ]

        self.batchQuery(
            node_queries,
            error_msg="Problem with creating schema in nodes",
        )

        edge_queries = [
            f"create class {edge_class} extends E" for edge_class in schema.edges
        ]

        self.batchQuery(
            edge_queries,
            error_msg="Problem with creating schema in edges",
        )

        property_queries = []
        for prop in schema.properties:
            prop_class, prop_prop, prop_type = prop
            if prop_class == "all":
                property_queries.extend(
                    [
                        f"CREATE PROPERTY {node_class}.{prop_prop} {prop_type}"
                        for node_class in schema.nodes
                    ]
                )
                property_queries.extend(
                    [
                        f"CREATE PROPERTY {edge_class}.{prop_prop} {prop_type}"
                        for edge_class in schema.edges
                    ]
                )
            else:
                property_queries.append(
                    f"CREATE PROPERTY {prop_class}.{prop_prop} {prop_type}"
                )

        self.batchQuery(
            property_queries,
            error_msg="Problem with creating schema in properties",
        )

        index_queries = []
        for index in schema.indexes:
            index_class, index_prop, index_type = index
            if index_class == "all":
                property_queries.extend(
                    [
                        f"CREATE INDEX {node_class}.{index_prop} {index_type}"
                        for node_class in schema.nodes
                    ]
                )
                property_queries.extend(
                    [
                        f"CREATE INDEX {edge_class}.{index_prop} {index_type}"
                        for edge_class in schema.edges
                    ]
                )
            else:
                property_queries.append(
                    f"CREATE INDEX {index_class}.{index_prop} {index_type}"
                )

        self.batchQuery(
            index_queries,
            error_msg="Problem with creating schema in indexes",
        )

    def sendCommand(
        self, command, lang_type="sql", error_msg="Problem sending command"
    ):
        data = {"command": command}
        url = f"{self.api_url}/command/{self.db}/{lang_type}"
        try:
            return requests.post(url, json=data, auth=self.auth) #nosec
        except Exception as e:
            logging.error(error_msg)
            logging.exception(e)

    def createNodeSchema(self, className):
        return self.sendCommand(
            f"create class {className} extends V",
            error_msg="Problem creating new schema entry for node",
        )

    def createEdgeSchema(self, className):
        return self.sendCommand(
            f"create class {className} extends E",
            error_msg="Problem creating new schema entry for edge",
        )

    def insertNodeDocument(self, stix_obj, klass):
        stix_obj["@class"] = klass
        return self.makeRequest(f"document/{self.db}", json=stix_obj).json()

    def insertEdgeDocument(self, stixObj, edgeKlass, source, target):
        return self.sendCommand(
            f"create edge {edgeKlass} from {source} to {target} CONTENT {json.dumps(stixObj)}",
            error_msg="Error when inserting edge into database",
        ).json()


# Testing here
if __name__ == "__main__":
    rapi = RestAPIWrapper(db="testRest")
    rapi.createDB()
    rapi.connectToDB()
    rapi.createSchema()

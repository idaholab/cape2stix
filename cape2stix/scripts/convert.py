# Copyright 2023, Battelle Energy Alliance, LLC
"Script to convert CAPE JSON reports into STIX 2.1"
# from pycti import Malware
# pylint: disable=trailing-whitespace
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation
# pylint: disable=import-error #
import logging
import re
import json
import argparse
import datetime
import ipaddress
import sys
import os
import asyncio
import requests
from pathlib import PureWindowsPath
from aiofile import async_open
from stix2 import (
    Process,
    Software,
    Location,
    Report,
    Malware,
    MalwareAnalysis,
    File,
    Directory,
    Mutex,
    AttackPattern,
    DomainName,
    WindowsRegistryKey,
    IPv4Address,
    NetworkTraffic,
    parse
)
from cape2stix.core.util import (
    genRel,
    genRelMany,
    fixdate,
    timing,
    create_object,
    keys_to_object,
    ExtensionHelper,
)
from cape2stix.core.stix_loader import StixLoader
from cape2stix.core.mitreattack import AttackGen



class Cape2STIX:
    """
    Class to setup our json reader and handle the conversion.
    param: file - path to json file
    """

    def __init__(self, file=None, data=None, allow_custom=True, small=False):
        self.file = file
        self.allow_custom = allow_custom
        self.gen_viewable = small
        self.es = ExtensionHelper()
        self.firstTimeSetup()
        if data is not None:
            self.content = data
            logging.debug("Here")
        self.sl = StixLoader(allow_custom=self.allow_custom)
        self.objects = []
        self.fspec={}
        self.fhash={}
        self.whitelist=[]
        
    def firstTimeSetup(self):
        pass
        # sup_files = os.path.join(os.path.dirname(__file__), "sup_files")
        # if not os.path.exists(sup_files):
        #     os.mkdir(sup_files)
        # local_ttp_json = os.path.join(sup_files, "enterprise-attack.json")
        # if not os.path.exists(local_ttp_json):
        #     downloadGithub(dst_path=local_ttp_json)
        # self.ttp_path = local_ttp_json

    @timing
    async def setup(self):
        if self.file is not None:
            async with async_open(self.file, "r") as reader:
                self.content = json.loads(await reader.read())
                
    def create_object(self, cls, *args, **kwargs):
        """
        wraps util.create_object to ensure that the custom_object parameter is set consistently.
        """
        return create_object(cls, *args, **kwargs, custom_object=self.allow_custom)

    def create_rel(self, *args, **kwargs):
        """
        wraps util.create_rel to ensure that the custom_object parameter is set consistently.
        parameters:
        src
        target
        rel_type
        custom_object
        """
        return genRel(
            *args, **kwargs, custom_object=self.allow_custom, force_uuidv5=True
        )

    def create_rel_many(self, *args, **kwargs):
        """
        wraps util.create_rel to ensure that the custom_object parameter is set consistently.
        """
        return genRelMany(
            *args, **kwargs, custom_object=self.allow_custom, force_uuidv5=True
        )

    def keys_to_object(self, *args, **kwargs):
        return keys_to_object(*args, **kwargs, custom_object=self.allow_custom)

    @timing
    def add_objects(self, tup, rel_type="related-to", main_obj=None, reversed=False):
        """Adds objects to the bundle and generates relationships
        tup -- a tuple of lists of objects to be connected in the form (source_ref, target_ref)
        main_obj -- sets main_obj as the source_ref
        reversed -- changes the direction of the reference
        """

        objs_to_connect, objects = tup
        new_rels = []
        if main_obj is not None:
            for obj_to_connect in objs_to_connect:
                if reversed:
                    src = obj_to_connect
                    target = main_obj
                else:
                    src = main_obj
                    target = obj_to_connect
                new_rels.extend(self.create_rel_many(src, target, rel_type=rel_type))
        self.objects.extend(objects + new_rels)
        for item in objects + new_rels + objs_to_connect:
            self.sl.add_item(item)
        return objs_to_connect, objects

    @timing
    async def convert(self, outpath=None):
        "Primary logic of convert.py; calls the gen-functions to convert report data into stix objects"
        try:
            if self.content["target"]["category"] == "file": # NOTE: i don't have enough reports to test if this will ever not be true;this is for safety -wb 
                self.fspec = self.content["target"]["file"]
                h=self.fspec
                self.fhash = {
                    "md5": h["md5"], "sha1": h["sha1"], "sha256": h["sha256"],
                    "ssdeep": h["ssdeep"], "sha3_384": h["sha3_384"],
                    "tlsh": re.sub(r'^T1', '', h["tlsh"], count=1)
                }

            _, malware_objs = self.add_objects(self.genMalware())
            malware_obj = malware_objs[0]
            self.add_objects(self.genMalwareAnalysis(), rel_type="dynamic-analysis-of", main_obj=malware_obj)

            self.add_objects(
                self.genProcesses(), rel_type="creates", main_obj=malware_obj
            )
            

            if not self.gen_viewable:
                self.add_objects(
                    self.genMalwareFile(), rel_type="related-to", main_obj=malware_obj
                )
                self.add_objects(
                    self.genReadFiles(), rel_type="reads", main_obj=malware_obj
                )
                self.add_objects(
                    self.genModifiedFiles(), rel_type="modifies", main_obj=malware_obj
                )
                self.add_objects(
                    self.genDeletedFiles(), rel_type="deletes", main_obj=malware_obj
                )
                self.add_objects(
                    self.genDeletedRegistryKeys(),
                    rel_type="deletes",
                    main_obj=malware_obj,
                )
                self.add_objects(
                    self.genModifiedRegistryKeys(),
                    rel_type="modifies",
                    main_obj=malware_obj,
                )
                self.add_objects(
                    self.genReadRegistryKeys(), rel_type="reads", main_obj=malware_obj
                )
            self.add_objects(
                self.genMutexes(), rel_type="creates", main_obj=malware_obj
            )
            self.add_objects(
                await self.genTTPs(), rel_type="uses", main_obj=malware_obj
            )

            self.add_objects(
                self.genDomainNames(), rel_type="uses", main_obj=malware_obj
            )
            self.add_objects(([], self.es.get_used_extensions()))

            self.add_objects(
                self.genNetworkTraffic(), rel_type="uses", main_obj=malware_obj
            )

            if outpath is not None:
                logging.info(f"finished with {outpath}")
                await self.sl.write_out(outpath)
            else:
                await self.sl.write_out("Test_MalwareAnalysisCAPE.json")
        except Exception as e:
            logging.critical("File failed to convert: ")
            logging.exception(e)

    # ie function to create processes.. return process tree so arg here would be parent process.
    @timing
    def genProcesses(self):
        """
        Function to generate STIX Process SDOs for our memorystore.

        param proc_dict -- entire json dictionary of the 'processes' section of CAPE report.
        param sl -- the stix_loader class for memorystore access

        return Process List -- returns reference list to all process tree for the memory stored Report
        """
        proc_dict = self.content["behavior"]["processes"]
        proc_list = []
        for proc in proc_dict:
            logging.debug(proc["process_id"])
            logging.debug(proc["parent_id"])
            logging.debug(proc["environ"])
            # for key in proc['environ']:
            #     print(key+' ')

            process = self.create_object(
                Process,
                pid=proc["parent_id"],
                environment_variables=proc["environ"],
                command_line=proc["environ"]["CommandLine"]
                # created_time=fixdate(proc['first_seen'])
            )
            proc_list.append(process)
            # for calls in proc['calls']:
            #     print(calls['category'])
        return (proc_list, proc_list)

    # NOTE: This object should have the proper SRO's connected for traversals, and should form the "center-peice" \
    # of each analysis graph (although it will not have a proper SRO to the malware analysis/report).
    @timing
    def getTags(self):
        "retrieves the tags from malwarebazaar"
        data = {'query': 'get_info', 'hash': self.fhash["sha256"]}
        url = "https://mb-api.abuse.ch/api/v1/"
        try:
            res = requests.post(url, data=data, timeout=20).json() # where r is the response of the post request
        except Exception as e:
            logging.warning('Exception when grabbing from malware bazaar')
            logging.exception(e)
            return None
        if res["query_status"] != 'ok':
            logging.warning(f'Malware Bazaar Response: {res}')
            return None
        if "tags" not in res["data"][0]:
            logging.warning("tags not found")
            return None
        
        return (res['data'][0]["tags"])

    
    @timing
    def genMalware(self):
        "generates the primary malware object and retrieves tags"
        tags = self.getTags()
        logging.debug(tags)
        if "sha256" in self.content["info"]["parent_sample"]:
            malware_obj = self.create_object(
                Malware,
                name=self.content["info"]["parent_sample"]["sha256"],
                is_family=False,
                x_malware_bazaar_tags=tags
            )
        else:
            ended = self.content["info"]["ended"]
            malware_obj = self.create_object(Malware, name=ended, is_family=False, x_malware_bazaar_tags=tags)
        malware_obj = self.es.replace_w_extensions_spec(malware_obj, "malware_bazaar")
        return [malware_obj], [malware_obj]
   



    # NOTE: This object should store the metadata about the analysis \
    # done by CAPE/VM info (or let that described as a software object) - MC
    # function takes cape report as dict, return STIX objects as list, and the object it's supposed to attach to
    # ie function to create processes.. return process tree so arg here would be parent process.
    @timing
    def genMalwareAnalysis(self):
        """
        Function to generate STIX Malware Analysis SDOs for our memorystore.

        param stats_dict --
        param cape_dict --
        param info_dict -- entire json dictionary of the 'info' section of CAPE report.
        param sl -- the stix_loader class for memorystore access

        return ma -- returns reference to memory stored MalwareAnalysis SDOp
        """
        stats_dict, cape_dict, info_dict = (
            self.content["statistics"],
            self.content["CAPE"],
            self.content["info"],
        )
        logging.debug(stats_dict)
        logging.debug(cape_dict)
        logging.debug(info_dict)

        started = fixdate(info_dict["started"])
        analysis_started = fixdate(info_dict["machine"]["started_on"])
        analysis_ended = fixdate(info_dict["machine"]["shutdown_on"])

        os_software = self.create_object(Software, name=info_dict["machine"]["name"])

        host_vm_ref = self.create_object(
            Software,
            name=info_dict["machine"]["manager"],
        )
        malwareanalysis = self.create_object(
            MalwareAnalysis,
            # name='temp',
            product=info_dict["version"],
            version=info_dict["version"],
            host_vm_ref=host_vm_ref,
            operating_system_ref=os_software,
            # installed_software_refs= #TODO grab refs to any nonstandard software on the kvm system for analysis
            # configuration_version= #TODO property associated with confiruation for this run
            modules=info_dict["package"],
            submitted=started,
            result="malware",
            analysis_started=analysis_started,
            analysis_ended=analysis_ended
            # analysis_sco_refs= #TODO list of all refs for this run, meaning this would be one of the last objects built, pass a list in
        )
        ma_objects = []
        ma_objects.append(os_software)
        ma_objects.append(host_vm_ref)
        ma_objects.append(malwareanalysis)

        # for object in ma_objects:
        #     self.sl.add_item(object)
        logging.debug(malwareanalysis)

        ma_objects.append(self.create_rel(os_software, host_vm_ref, "related-to"))
        ma_objects.append(
            self.create_rel(malwareanalysis, os_software, "dynamic-analysis-of")
        )
        return [malwareanalysis], ma_objects

    @timing
    def genMalwareFile(self):
        "generates STIX for the executable file associated with the malware"

        if self.content["target"]["category"] == "file":
            
            malware_file = self.create_object(
                File,
                name=self.fspec["name"],
                size=self.fspec["size"],
                hashes=self.fhash
            ) # NOTE:  mime_type is represented in self.content[target][file][type] but is not in the proper IANA form

        return [malware_file], [malware_file]

    # NOTE: I think we should use report as a "metadata" -esk object to capture all other objects that are generated \
    # Throughout the analysis, we can use the embeddings relationships for now. Other objects can capture the CAPE \
    # Instance metadata and connect to everything. - MC

    # function takes cape report as dict, return STIX objects as list, and the object it's supposed to attach to
    # ie function to create processes.. return process tree so arg here would be parent process.
    @timing
    def genReport(self, all_objects):
        """
        Function to generate STIX Report SDOs for our memorystore.

        param rep_dict -- entire json dictionary of the 'info' section of CAPE report.
        param all_objects -- list of all objects produced in the analysis.

        return report -- returns reference to memory stored Report
        """

        if len(all_objects) == 0:
            logging.error("Received no objects, not generating report.")
            return [], []
        rep_dict = self.content["info"]

        # TODO: combine any list sent back and send to object_refs
        # TODO: need to fix timestamp.

        timestamp = 1528797322
        temptime = datetime.datetime.fromtimestamp(timestamp)

        report = self.create_object(
            Report,
            # TODO: might want to add at least a partial hash in here at some point.
            name=str(temptime) + "_MalwareAnalysisCAPE",
            # TODO: might need to verify that we should have the published attr or not, if required delete this comment
            published=temptime,
            object_refs=all_objects,
            report_types="malware",  # TODO:extend to include any applicable report-type-ov
        )
        # self.sl.add_item(report)

        return report

    @timing
    def genRegistryKeys(self, data):
        "generates STIX for the windows registry keys modified by the malware"
        l = []
        for key in data:
            l.append(self.create_object(WindowsRegistryKey, key=key, force_uuidv5=True))
        return (l, l)

    def genDeletedRegistryKeys(self):
        return self.genRegistryKeys(self.content["behavior"]["summary"]["delete_keys"])

    def genModifiedRegistryKeys(self):
        return self.genRegistryKeys(self.content["behavior"]["summary"]["write_keys"])

    def genReadRegistryKeys(self):
        return self.genRegistryKeys(self.content["behavior"]["summary"]["read_keys"])

    @timing
    async def genTTPs(self):
        ttp_list = []
        # NOTE: The C and E TTPs are from the malware behavior catalogs, for now not including them.
        # NOTE: There may be multiple signatures that could be "hit", it may be desirable to represent that
        unique = set()
        for ttp in self.content["ttps"]:
            if ttp["ttp"].startswith("T"):
                if ttp["ttp"] in unique:
                    continue
                else:
                    unique.add(ttp["ttp"])

                ttp_data = AttackGen.githubVersion(ttp["ttp"][1:])
                if ttp_data is None:
                    continue
                ap = self.create_object(
                    AttackPattern,
                    **ttp_data,
                )
                ap = self.es.replace_w_extensions_spec(ap, "mitre")
                ttp_list.append(ap)
        return (ttp_list, ttp_list)

    @timing
    def genMutexes(self):
        # behavior/summary/mutexes
        mutex_list = []
        for mutex_name in self.content["behavior"]["summary"]["mutexes"]:
            mutex_list.append(
                self.create_object(Mutex, name=mutex_name, force_uuidv5=True)
            )
        return (mutex_list, mutex_list)

    def genPayloads(self):
        # these could be files, malware, indicators or something else
        pass

    @timing
    def genFiles(self, data, link_all=True, tree=False):
        # main function to produce files from a given json sub-object.
        # It seems like there may be an edge case where a directory will be mis-identifed as a file if
        # it does not have any children (as we only have pathes for this).
        structure = {}

        top = {}
        for item in data:
            if "\\" in item:
                full_path = PureWindowsPath(item)
                parts = list(full_path.parts)
                parent = None
                for index, part in enumerate(parts):

                    if (index + 1) == len(parts) and len(parts) > 1:
                        file = self.create_object(
                            File,
                            name=part,
                            parent_directory_ref=parent.id
                            if parent is not None
                            else None,
                            force_uuidv5=True,
                        )

                    else:
                        file = self.create_object(
                            Directory,
                            path=PureWindowsPath().joinpath(*parts[:index]),
                            force_uuidv5=True,
                        )
                        parent = file
                    if index == 0:
                        top[file.id] = file
                    if file.id not in structure:
                        structure[file.id] = file

        if link_all:
            return (list(structure.values()), list(structure.values()))

        else:
            return (top.values(), structure.values())

    def genDeletedFiles(self, link_all=True, tree=False):
        # ['//behavior/summary/delete_files']
        return self.genFiles(
            self.content["behavior"]["summary"]["delete_files"],
            link_all=link_all,
            tree=tree,
        )

    def genModifiedFiles(self, link_all=True, tree=False):
        # //behavior/summary/write_files
        return self.genFiles(
            self.content["behavior"]["summary"]["write_files"],
            link_all=link_all,
            tree=tree,
        )

    def genReadFiles(self, link_all=True, tree=False):
        # ['//behavior/summary/read_files']
        return self.genFiles(
            self.content["behavior"]["summary"]["read_files"],
            link_all=link_all,
            tree=tree,
        )

    @timing
    def genDomainNames(self):
        # //network/domains
        l = []
        for domain in self.content["network"]["domains"]:
            l.append(self.create_object(DomainName, value=domain["domain"]))
        return l, l

    @timing
    def genhosts(self, hosts: list):
        objs_to_connect = []
        objects = []
        locations = {}
        ts = {}
        for host in hosts:
            if (host["country_name"], host["hostname"]) not in ts:
                ts[(host["country_name"], host["hostname"])] = [host["ip"]]
            else:
                ts[(host["country_name"], host["hostname"])].append(host["ip"])

        new_hosts = []
        for (country, hostname), hosts in ts.items():
            cidrs = ipaddress.collapse_addresses(
                [ipaddress.ip_network(ip_) for ip_ in hosts]
            )
            new_hosts.append((country, hostname, cidrs))
        for country, hostname, cidrs in new_hosts:
            for cidr in cidrs:
                # This will contain an ip, possible hostname and country_name
                if country != "":
                    if country not in locations:
                        loc = keys_to_object(
                            {'country_name': country},
                            Location,
                            [("country_name", "country"), ("country_name", "name")],
                            force_uuidv5=True,
                        )
                        if loc is not None:
                            locations[country] = loc
                            objs_to_connect.append(loc)
                    else:
                        loc = locations[country]

                    ipv4 = keys_to_object(
                        {'ip': cidr}, IPv4Address, [("ip", "value")], force_uuidv5=True
                    )
                    if ipv4 is not None:
                        objs_to_connect.append(ipv4)

                    if hostname != "":
                        domainname = keys_to_object(
                            {'hostname': hostname}, DomainName, [("hostname", "value")], force_uuidv5=True
                        )
                        if domainname is not None:
                            objs_to_connect.append(domainname)
                    else:
                        domainname = None

                    if ipv4 is not None and loc is not None:
                        objects.append(
                            self.create_rel(src=ipv4, target=loc, rel_type="located-at")
                        )

                    if domainname is not None and loc is not None:
                        objects.append(
                            self.create_rel(
                                src=domainname, target=loc, rel_type="located-at"
                            )
                        )

                    if domainname is not None and ipv4 is not None:
                        objects.append(
                            self.create_rel(
                                src=ipv4, target=domainname, rel_type="resolves-to"
                            )
                        )
        objects.extend(objs_to_connect)
        return objs_to_connect, objects

    @timing
    def gennettraffic(self, traffics: list, proto: str):
        l = []
        for traffic in traffics:
            # NOTE: Currently assuming everything is ipv4, this will need to be adjusted later
            # NOTE: always assuming that there will be a dst/src ip. If this is not true corrections wil be needed.
            # make src/dst ip first
            src_ip = self.keys_to_object(
                traffic, IPv4Address, [("src", "value")], force_uuidv5=True
            )
            dst_ip = self.keys_to_object(
                traffic, IPv4Address, [("dst", "value")], force_uuidv5=True
            )
            # make net traffic object
            nettraf = self.create_object(
                NetworkTraffic,
                src_ref=src_ip,
                dst_ref=dst_ip,
                src_port=traffic["sport"],
                dst_port=traffic["dport"],
                protocols=[proto],
                force_uuidv5=True,
            )
            # they already joined with the references
            l.extend([src_ip, dst_ip, nettraf])

        return l, []

    @timing
    def genNetworkTraffic(self):
        # l will contain all objects created here.
        objs_to_connect = []
        objects = []
        # //network/tcp
        objs, rels = self.gennettraffic(self.content["network"]["tcp"], "tcp")
        objs_to_connect.extend(objs)
        objects.extend(rels)

        # //network/udp
        objs, rels = self.gennettraffic(self.content["network"]["udp"], "udp")
        objs_to_connect.extend(objs)
        objects.extend(rels)

        # //network/hosts
        objs, rels = self.genhosts(self.content["network"]["hosts"])
        objs_to_connect.extend(objs)
        objects.extend(rels)
        # //network/dead_hosts
        # objs, rels = self.genhosts(self.content["network"]["dead_hosts"])
        # objs_to_connect.extend(objs)
        # objects.extend(rels)
        # # //network/http
        # # //signatures/6/name/http_request
        # objects.extend(objs_to_connect)
        return objs_to_connect, objects

    def genAPICalls(self):
        # This function will provide a single object to aggregate API calls. ex: NtSetInformationFile
        pass


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="CAPE json conversion to STIX. Using mainly the report.json output"
    )
    parser.add_argument(
        "--log_level", choices=["warn", "debug", "info"], default="warn"
    )
    parser.add_argument("--disallow_custom", action="store_true", default=False)
    parser.add_argument("--small", action="store_true", default=False)
    parser.add_argument(
        "--overwrite", action="store_true", help="overwrite existing files"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-u", action="store_true", help="run tests with base file")

    group.add_argument(
        "-f",
        "--file",
        type=str,
        dest="file",
        action="store",
        help="path to file ie: ./report.json",
    )

    return parser.parse_args(args)

@timing
async def convert_file(args, sem=None):
    if sem is not None:
        await sem.acquire()
    try:
        file_path, custom, small, outpath = args
        cs = Cape2STIX(file_path, allow_custom=custom, small=small)
        await cs.setup()
        await cs.convert(outpath=outpath)
    except Exception as e:
        logging.exception(e)
        logging.critical(f"{file_path} failed!")
    finally:
        if sem is not None:
            sem.release()

stix_uuid5 = '[a-z0-9-]+--[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-5[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}'

# TODO: figure out the best place to call this function
# TODO: look briefly at performance if we output a dict instead of a list with key=type and val=id
# def parse_benign(benign_file):
#     """parses a stix file and builds a list of UUIDv5s such 
#        that they can be removed from the converted file"""
#     if os.path.exists(benign_file):
#         with open(benign_file) as b:
#             benign = parse(b, allow_custom=True)
#             return [obj.id for obj in benign.objects if re.match(stix_uuid5, obj.id)]

# @timing
# async def parse_malign(malign_stix, benign_list):
#     for obj in malign_stix:
#         # if obj.id in benign_list[obj.type]: #TODO: I would like to test this over just iterating over a list, but I need to change parse_benign
#         if obj.id in benign_list:
#             print("todo:remove obj")


@timing
async def _main():
    args = parse_args(sys.argv[1:])
    log_level = {"warn": logging.WARN, "debug": logging.DEBUG, "info": logging.INFO}[
        args.log_level
    ]
    logging.basicConfig(level=log_level)

    if args.file:
        logging.debug(args.file)

        if os.path.exists(args.file):
            if os.path.isdir(args.file):
                promises = []
                sem = asyncio.Semaphore(5)
                for file_path in os.listdir(args.file):
                    if file_path.startswith("."):
                        logging.warning(f"skipping {file_path} as it starts with '.'")
                        continue
                    if not args.overwrite and os.path.exists(
                        os.path.join("output", file_path)
                    ):
                        logging.warning(f"skipping {file_path} as file already exists")
                        continue

                    promises.append(
                        convert_file(
                            (
                                os.path.join(args.file, file_path),
                                not args.disallow_custom,
                                args.small,
                                f"output/{file_path}",
                            ),
                            sem=sem,
                        )
                    )
                    # promises.append(parse_malign()) #TODO: implement parse_malign
                await asyncio.gather(*promises)
            else:
                file_path = args.file
                await convert_file(
                    (
                        file_path,
                        not args.disallow_custom,
                        args.small,
                        f"output/{os.path.basename(file_path)}",
                    )
                )
        else:
            logging.error(
                "Please add a valid path to a JSON file. example: /Users/frank/portable.json"
            )


if __name__ == "__main__":
    asyncio.run(_main())

# Copyright 2023, Battelle Energy Alliance, LLC
import requests
from enum import Enum
import logging
from urllib.parse import urljoin
from pprint import pprint
import math
import json
import os
import argparse
import logging
import sys
from itertools import cycle


class TaskStatus(Enum):
    failed_analysis = "failed_analysis"
    failed_processing = "failed_processing"
    banned = "banned"
    pending = "pending"
    running = "running"
    distributed = "distributed"
    completed = "completed"
    reported = "reported"
    recovered = "recovered"


class CAPEClient:
    def __init__(self, url):
        # if 'apiv2' not in url:
        #     self.url = urljoin(url, 'apiv2')
        # else:
        self.url = url
        self.auth()

    def auth(self):
        pass

    def search(self, sha256, **kwargs):
        """curl -d "option=[option]&argument=[argument]" http://example.tld/apiv2/tasks/extendedsearch/

        Searchable Options List:
        id : Task id
        name : Name of target file name
        type : Name of file type
        string : Match a string in the static analysis section
        ssdeep : Match an ssdeep hash
        crc32 : Match a CRC32 hash
        file : Match a file in the behavioral analysis summary
        command : Match an executed command
        resolvedapi : Match an API that a sample resolved
        key : Match a registry key in the behavioral analysis summary
        mutex : Match a mutex in the behavioral analysis summary
        domain : Match a resolved domain
        ip : Match a contacted IP Address
        signature : Match a CAPE signature description
        signame : Match a CAPE signature name
        detections: Match samples associated with malware family
        url : Match a URL target task (submitted URL task)
        imphash : Match an import hash
        iconhash: Match the exact hash of the icon associated with the PE
        iconfuzzy: Match a hash designed to match on similar-looking icons
        surialert : Match a suricata alert signature
        surihttp : Match suricata HTTP data
        suritls : Match suricata TLS data
        clamav : Match a Clam AV signature
        yaraname : Match a Yara signature name
        virustotal : Match a virustotal AV Signature
        comment : Match a comment posted to a specific task
        md5 : Targets with a specific MD5 hash
        sha1 : Targets with a specific SHA1 hash
        sha256 : Targets with a specific SHA256 hash
        sha512 : Targets with a specific SHA512 hash
        TTP: TTP number
        """

    def list_tasks(self, status=None, limit=50, offset=None, tags_tasks=None):
        """
        This is GET, needs to have a trailing /

        curl http://example.tld/apiv2/tasks/list/
        curl http://example.tld/apiv2/tasks/list/[limit]/ (specify a limit of tasks to return)
        curl http://example.tld/apiv2/tasks/list/[limit]/[offset]/ (specify a limit of tasks to return, offset by a specific amount)
        Acepts as params status to check for status and/or option to search by option LIKE
        """
        d = {}
        if status is not None:
            if not isinstance(status, TaskStatus):
                logging.error(
                    "Given status is not of type TaskStatus, please use the Enum!"
                )
            else:
                d["status"] = status.value

        if tags_tasks is not None:
            d["tags_tasks"] = tags_tasks

        # max limit is 50, so we need to deal with pagination.
        if limit > 50:
            response_data = []
            for i in range(math.ceil(limit / 50)):
                part_response_data = self.get(
                    ["tasks", "list", limit if limit <= 50 else 50, i * 50], **d
                )
                response_data.extend(part_response_data["data"])
                if len(part_response_data["data"]) < 50:
                    return response_data
                limit -= 50

        else:
            response_data = self.get(["tasks", "list", limit], **d)
            return response_data["data"]

    def delete_tasks(self, tasks):
        # currently expects the task json, might want to modify to also accept ids later.
        if isinstance(tasks, list) and len(tasks) == 0:
            logging.warning("Empty task list passed attempted to be deleted.")
            return None
        if not isinstance(tasks, list):
            tasks = [tasks]

        d = {}
        d["ids"] = ",".join(str(task["id"]) for task in tasks)

        response_data = self.post(["tasks", "delete_many"], **d)
        return response_data

    def submit(self, file_path, timeout=200):
        """
        curl -F file=@/path/to/file -F machine="VM-Name" -H "Authorization: Token YOU_TOKEN" http://example.tld/apiv2/tasks/create/file/
        Note: machine is optional. Header depends of the config if Token auth is enabled
        """
        pass

    def get_report(self, task_id):
        return self.get(["tasks", "get", "report", task_id])

    def save_to_file(self, j, path):
        with open(path, "w") as f:
            json.dump(j, f)

    def submit_file(
        self, file_path, tags="win10", tags_tasks=None, timeout=200, machines=None
    ):
        rel_url = ["tasks", "create", "file"]
        data = {"tags": tags, "timeout": str(timeout)}
        if machines is not None:
            data["machine"] = machines.split(",")[0]
        if tags_tasks is not None:
            data["tags_tasks"] = tags_tasks
        return requests.post(
            urljoin(self.url, f'apiv2/{"/".join([str(part) for part in rel_url])}/'),
            data=data,
            files=[("file", open(file_path, "rb"))],
        ).json()

    def submit_directory(
        self, dir_path, platform="windows", tags="win10", timeout=200, machines=None
    ):
        rel_url = ["tasks", "create", "file"]
        responses = []
        if machines is not None:
            machines = cycle(machines.split(","))
        return [
            requests.post(
                urljoin(
                    self.url, f'apiv2/{"/".join([str(part) for part in rel_url])}/'
                ),
                data={
                    "tags": tags,
                    "timeout": str(timeout),
                    "machine": next(machines) if machines is not None else None,
                },
                files=[("file", open(os.path.join(dir_path, path), "rb"))],
            ).json()
            for path in os.listdir(dir_path)
        ]

    def get(self, rel_url, **kwargs):
        return requests.get(
            urljoin(self.url, f'apiv2/{"/".join([str(part) for part in rel_url])}/'),
            params=kwargs,
        ).json()

    def post(self, rel_url, **kwargs):
        return requests.post(
            urljoin(self.url, f'apiv2/{"/".join([str(part) for part in rel_url])}/'),
            data=kwargs,
        ).json()


def parse_args(args):
    parser = argparse.ArgumentParser(description="CAPE API interface")
    parser.add_argument(
        "--log_level", choices=["warn", "debug", "info"], default="warn"
    )
    parser.add_argument("--submit", default=None)
    parser.add_argument("--delete", action="store_true", default=False)
    parser.add_argument("--delete_pending", action="store_true", default=False)
    parser.add_argument("--get_reports", action="store_true", default=False)
    parser.add_argument("--list", action="store_true", default=False)
    parser.add_argument("--machines", default=None)
    parser.add_argument("--host", default="http://127.0.0.1:8000")
    parser.add_argument("--limit", type=int, default=5000)
    return parser.parse_args(args)


if __name__ == "__main__":
    # setup object
    args = parse_args(sys.argv[1:])
    
    cc = CAPEClient(args.host)
    # print(cc.submit_file('/tmp/test'))
    if args.list:
        pprint(cc.list_tasks(limit=args.limit))

    if args.get_reports:
        reported_tasks = cc.list_tasks(status=TaskStatus.reported, limit=args.limit)
        for reported_task in reported_tasks:
            report = cc.get_report(reported_task["id"])
            cc.save_to_file(report, f'input/{reported_task["id"]}.json')
    if args.delete:
        pprint(cc.delete_tasks(cc.list_tasks(limit=args.limit)))

    if args.delete_pending:
        pprint(cc.delete_tasks(cc.list_tasks(status=TaskStatus.pending, limit=args.limit)))

    if args.submit:
        if os.path.exists(args.submit):
            if os.path.isdir(args.submit):
                cc.submit_directory(args.submit, machines=args.machines)
            else:
                cc.submit_file(args.submit, machines=args.machines)
    # get all remaining tasks json reports

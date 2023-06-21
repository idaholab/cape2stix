# Copyright 2023, Battelle Energy Alliance, LLC
from stix2 import TAXIICollectionSource
from taxii2client.v20 import Collection
from stix2 import Filter
import json
import logging
import requests
import os

MITREAttack = None


def download(url, outpath, verify=True):
    resp = requests.get(url, verify=verify)
    with open(outpath, "wb") as f:
        f.write(resp.content)


class MITREAttackGenerator:
    def __init__(self):
        self.mitreattack = None
        self_path = os.path.dirname(os.path.abspath(__file__))
        sup_files_path = os.path.join(self_path, "../sup_files")
        if not os.path.exists(sup_files_path):
            os.mkdir(sup_files_path)
        self.attack_path = os.path.join(sup_files_path, "enterprise-attack.json")
        if not os.path.exists(self.attack_path):
            self.downloadGithub(dst_path=self.attack_path)

    def taxiiVersion(self, TTP):

        # enterprise_attack = 95ecc380-afe9-11e4-9b6c-751b66dd541e"
        # mobile_attack = 2f669986-b40b-4423-b720-4396ca6a462b"
        # ics-attack = 02c3ef24-9cd4-48f3-a99f-b74ce24f1d34"

        collection = Collection(
            f"https://cti-taxii.mitre.org/stix/collections/95ecc380-afe9-11e4-9b6c-751b66dd541e/"
        )
        src = TAXIICollectionSource(collection)

        result = src.query(
            [
                Filter("external_references.external_id", "=", "T" + str(TTP).zfill(4)),
                Filter("type", "=", "attack-pattern"),
            ]
        )

        try:
            return result[0]
        except:
            return "Error: T" + TTP + " not found."

    def downloadGithub(self, dst_path=None):
        try:
            logging.info("Redownloading enterprise-attack.json...")
            download(
                "https://github.com/mitre-attack/attack-stix-data/raw/master/enterprise-attack/enterprise-attack.json",
                dst_path,
            )
        except:
            logging.warning(
                "Failed with normal download, trying with ignore ssl errors!"
            )
            try:
                logging.info("Redownloading enterprise-attack.json...")
                download(
                    "https://github.com/mitre-attack/attack-stix-data/raw/master/enterprise-attack/enterprise-attack.json",
                    dst_path,
                    verify=False,
                )
            except:
                logging.error("Download Error for enterprise-attack.json: Try Again")
        return 0

    def githubVersion(self, TTP, file_path=None):
        # Open json file if not already loaded
        if self.mitreattack is None:
            self.mitreattack = {}
            with open(
                self.attack_path if file_path is None else file_path,
                "r",
                encoding="utf-8",
                errors="replace",
            ) as f:
                attack_raw_data = json.load(f)
            for i in attack_raw_data["objects"]:
                if i["type"] == "attack-pattern":
                    self.mitreattack[
                        i["external_references"][0]["external_id"].lstrip("Tt")
                    ] = i

        # Search for TTP
        if TTP in self.mitreattack:
            return self.mitreattack[TTP]


AttackGen = MITREAttackGenerator()

# if __name__ == "__main__":
#     downloadGithub()
#     try:
#         TTP = sys.argv[1]
#         TTP = TTP.lstrip("Tt")
#     except:
#         print("TTP Argument Missing")
#         exit()


# print(githubVersion(TTP))
# print('###################################')
# print(taxiiVersion(TTP))

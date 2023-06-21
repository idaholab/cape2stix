# Copyright 2023, Battelle Energy Alliance, LLC
import unittest
import json
import os

import asyncio

from cape2stix.scripts.convert import Cape2STIX, convert_file

# from stix_enforcer.Fixers.UUID5Fixer import updateUUIDs       # modified stix_enforcer scripts to work as import
# from stix_enforcer.Fixers.TimeFixer import fixTime


# generate stix objects with convert.py
# assert relevant properties match valid values according to stix-enforcer

dir = os.path.dirname(__file__)
report_path = os.path.join(dir, "test_report.json")
converted_path = os.path.join(dir, "converted_report.json")


def find_obj(container, value, property="type", src_type=None, dst_type=None):
    """
    Search for first instance of desired object
    """

    for obj in container["objects"]:
        if obj[property] == value:
            if src_type is None:
                return obj
            else:
                if (
                    obj["source_ref"].split("--")[0] == src_type
                    and obj["target_ref"].split("--")[0] == dst_type
                ):
                    return obj
    return None  # no object of desired properties present


class TestConverter(unittest.TestCase):
    # expected result should be hardcoded
    # feed hardcoded properties
    # test individual methods
    # tests must not depend on each other
    # input should be simplest possible and representative (not exhaustive)

    @classmethod
    def setUpClass(cls):
        args = (report_path, True, False, converted_path)
        asyncio.run(convert_file(args))
        with open(converted_path, "r") as f:
            cls.content = json.load(f)
        f.close()

    def test_spec_vers(self):
        """
        Enforced by SpecVersionFixer.py
        -- enforce inclusion of common spec_version property (in all objects)
        """
        mal = find_obj(self.content, "malware")

        self.assertIn("spec_version", mal)
        self.assertEqual(mal["spec_version"], "2.1")

    # uuid5s should be checked by validator (code 103)
    def test_ipv4_addr_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        ipv4 = find_obj(self.content, "ipv4-addr")
        uuid5 = "ipv4-addr--7e5fa90c-c43c-5baf-93b2-00684c5276b5"

        self.assertEqual(ipv4["id"], uuid5)

    # def test_ipv6_addr_uuid5(self):

    def test_dir_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        dir = find_obj(self.content, "directory")
        # enforced_dir = updateUUIDs(dir)
        uuid5 = "directory--2d660588-dd2e-578d-8de0-68517564761d"

        # self.assertEqual(dir['id'], enforced_dir['id'])
        self.assertEqual(dir["id"], uuid5)

    def test_domain_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        dom = find_obj(self.content, "domain-name")
        uuid5 = "domain-name--9887785a-3f35-5686-8b1b-00491d686409"

        self.assertEqual(dom["id"], uuid5)

    def test_file_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        file = find_obj(self.content, "file")
        uuid5 = "file--0adfec20-c51c-5fbc-94b0-81fd40330859"

        self.assertEqual(file["id"], uuid5)

    def test_mutex_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        mutex = find_obj(self.content, "mutex")
        uuid5 = "mutex--28cafab6-4b0c-552e-b4fd-82bc5f1ac110"

        self.assertEqual(mutex["id"], uuid5)

    def test_net_traffic_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        net_traffic = find_obj(self.content, "network-traffic")
        uuid5 = "network-traffic--f5bacbcf-6eca-58e2-bf43-57d20d03e84f"

        self.assertEqual(net_traffic["id"], uuid5)

    def test_reg_key_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        reg_key = find_obj(self.content, "windows-registry-key")
        uuid5 = "windows-registry-key--9ba5bd01-6314-5eb8-be1a-ec9b4dfd60e9"

        self.assertEqual(reg_key["id"], uuid5)

    def test_software_uuid5(self):
        """
        Enforced by UUIDFixer.py
        -- enforce use of valid uuid5s for SCOs
        """
        soft = find_obj(self.content, "software")
        uuid5 = "software--2cdb2ada-a3ac-50b5-b45f-ce272456ba41"

        self.assertEqual(soft["id"], uuid5)

    def test_report_timestamp(self):
        """
        Covers TimeFixer.py
        -- enforce timestamp formatting
        """
        report = find_obj(self.content, "report")
        # enforced_rep = fixTime(report)
        time = "2018-06-12T03:55:22.000Z"

        # self.assertEqual(report, enforced_rep)
        self.assertEqual(report["published"], time)

    # ignoring VerbFixer.py (relationship verbs)

    def test_net_traffic_ports(self):
        """
        Covers NetworkTrafficReqChecker.py
        -- network-traffic objects must have src_port & dst_port properties
        - should already be covered by stix-validator (code 301)
        """
        net_traffic = find_obj(self.content, "network-traffic")

        self.assertIn("src_port", net_traffic)
        self.assertTrue(net_traffic["src_port"])
        self.assertIn("dst_port", net_traffic)
        self.assertTrue(net_traffic["dst_port"])

    def test_software_cpe(self):
        """
        Covers SoftwareReqChecker.py
        -- software objects must have cpe property
        """
        soft = find_obj(self.content, "software")

        self.assertIn("cpe", soft)
        self.assertTrue(soft["cpe"])

    def test_software_version(self):
        """
        Covers SoftwareReqChecker.py
        -- software objects must have version property
        """
        soft = find_obj(self.content, "software")

        self.assertIn("version", soft)
        self.assertTrue(soft["version"])

    def test_software_vendor(self):
        """
        Covers SoftwareReqChecker.py
        -- software objects must have vendor property
        """
        soft = find_obj(self.content, "software")

        self.assertIn("vendor", soft)
        self.assertTrue(soft["vendor"])

    def test_attack_pat_refs(self):
        """
        Covers AttackPatternReqChecker.py
        -- attack-pattern objects must have the externel_references property with each element at least containing the source_name & external_id properties
        - if the external reference is a CVE, its source_name property must be set to cve and its corresponding external_id property formatted as CVE-YYYY-NNNN+
        - if the external reference is a CAPEC, its source_name property must be set to capec and its corresponding external_id property formatted as CAPEC-[id]
        - (validity of ids should be checked by validator)
        """
        attack_pat = find_obj(self.content, "attack-pattern")

        self.assertIn("external_references", attack_pat)
        self.assertIn("source_name", attack_pat["external_references"][0])
        self.assertTrue(attack_pat["external_references"][0]["source_name"])
        self.assertIn("external_id", attack_pat["external_references"][0])
        self.assertTrue(attack_pat["external_references"][0]["external_id"])
        self.assertEqual("capec", attack_pat["external_references"][1]["source_name"])
        self.assertEqual(
            attack_pat["external_references"][1]["external_id"][0:6], "CAPEC-"
        )

    @unittest.skipIf(True, "Not yet in converted report")
    def test_ext_def(self):
        """
        Enforced by ExtensionFixer.py
        -- the extensions property of objects must be a dictionary and must not be empty
        """
        attack_pat = find_obj(self.content, "attack-pattern")

        self.assertIsInstance(attack_pat["extensions"], dict)
        self.assertTrue(attack_pat["extensions"])
        self.assertIsInstance(list(attack_pat["extensions"].values())[0], dict)

    def test_attack_pat_desc(self):
        """
        Covers DescLenHolder.py & DescReqHolder.py
        -- attack-pattern objects must have descriptions of at least length 10
        """
        attack_pat = find_obj(self.content, "attack-pattern")

        self.assertIn("description", attack_pat)
        self.assertGreaterEqual(len(attack_pat["description"].split()), 10)

    @unittest.skipIf(True, "Not yet in converted report")
    def test_ext_def_desc(self):
        """
        Covers DescLenHolder.py & DescReqHolder.py
        -- extension-definition objects must have descriptions of at least length 10
        """
        ext_def = find_obj(self.content, "extension-definition")

        self.assertIn("description", ext_def)
        self.assertGreaterEqual(len(ext_def["description"].split()), 10)

    @unittest.skipIf(True, "Not yet in converted report")
    def test_identity_desc(self):
        """
        Covers DescLenHolder.py & DescReqHolder.py
        -- identity objects must have descriptions of at least length 10
        """
        id = find_obj(self.content, "identity")

        self.assertIn("description", id)
        self.assertGreaterEqual(len(id["description"].split()), 10)

    def test_mal_desc(self):
        """
        Covers DescLenHolder.py & DescReqHolder.py
        -- malware objects must have descriptions of at least length 10
        """
        mal = find_obj(self.content, "malware")

        self.assertIn("description", mal)
        self.assertGreaterEqual(len(mal["description"].split()), 10)

    def test_loc_desc(self):
        """
        Covers DescLenHolder.py & DescReqHolder.py
        -- location objects must have descriptions of at least length 10
        """
        loc = find_obj(self.content, "location")

        self.assertIn("description", loc)
        self.assertGreaterEqual(len(loc["description"].split()), 10)

    def test_report_desc(self):
        """
        Covers DescLenHolder.py & DescReqHolder.py
        -- report objects must have descriptions of at least length 10
        """
        report = find_obj(self.content, "report")

        self.assertIn("description", report)
        self.assertGreaterEqual(len(report["description"].split()), 10)

    def test_attack_pat_kill(self):
        """
        Covers KillChainReqChecker.py
        -- attack-pattern objects must have the kill_chain_phases property with the kill_chain_name & phase_name sub-properties
        """
        attack_pat = find_obj(self.content, "attack-pattern")

        self.assertIn("kill_chain_phases", attack_pat)
        self.assertIn("kill_chain_name", attack_pat["kill_chain_phases"][0])
        self.assertTrue(attack_pat["kill_chain_phases"][0]["kill_chain_name"])
        self.assertIn("phase_name", attack_pat["kill_chain_phases"][0])
        self.assertTrue(attack_pat["kill_chain_phases"][0]["phase_name"])

    def test_mal_kill(self):
        """
        Covers KillChainReqChecker.py
        -- malware objects must have the kill_chain_phases property with the kill_chain_name & phase_name sub-properties
        """
        mal = find_obj(self.content, "malware")

        self.assertIn("kill_chain_phases", mal)
        self.assertIn("kill_chain_name", mal["kill_chain_phases"][0])
        self.assertTrue(mal["kill_chain_phases"][0]["kill_chain_name"])
        self.assertIn("phase_name", mal["kill_chain_phases"][0])
        self.assertTrue(mal["kill_chain_phases"][0]["phase_name"])

    def test_file_hash(self):
        """
        Covers FileReqChecker.py
        -- file objects must have hashes property
        """
        file = find_obj(self.content, "file")

        self.assertIn("hashes", file)
        self.assertTrue(file["hashes"])

    def test_file_name(self):
        """
        Covers NameReqChecker.py
        -- file objects must have name property
        """
        file = find_obj(self.content, "file")

        self.assertIn("name", file)
        self.assertTrue(file["name"])

    def test_mal_name(self):
        """
        Covers NameReqChecker.py
        -- malware objects must have name property
        """
        mal = find_obj(self.content, "malware")

        self.assertIn("name", mal)
        self.assertTrue(mal["name"])

    def test_loc_name(self):
        """
        Covers NameReqChecker.py
        -- location objects must have name property
        """
        loc = find_obj(self.content, "location")

        self.assertIn("name", loc)
        self.assertTrue(loc["name"])

    def test_mal_types(self):
        """
        Covers MalwareReqChecker.py
        -- malware objects must have malware_types property
        """
        mal = find_obj(self.content, "malware")

        self.assertIn("malware_types", mal)
        self.assertTrue(mal["malware_types"])

    def test_mal_file_rel(self):
        """
        Covers MalwareFileReqChecker.py
        -- malware objects must have associated file objects (relationships to file objects)
        """
        rel = find_obj(
            self.content, "relationship", src_type="malware", dst_type="file"
        )
        self.assertIsNotNone(rel)

        file = find_obj(self.content, rel["target_ref"], property="id")
        self.assertIsNotNone(file)

    @classmethod
    def tearDownClass(cls):
        os.remove(converted_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

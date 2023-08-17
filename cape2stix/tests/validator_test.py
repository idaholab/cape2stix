# Copyright 2023, Battelle Energy Alliance, LLC
import unittest
import json
import os
import asyncio
from stix2validator import (
    validate_file,
    validate_instance,
    # print_results,
    ValidationOptions,
)
import asyncio
from cape2stix.scripts.convert import convert_file


dir = os.path.dirname(__file__)
report_path = os.path.join(dir, "test_report.json")
converted_path = os.path.join(dir, "converted_report.json")

SKIP_WARNINGS = True


def find_obj(container, type):
    """
    Search for first instance of desired object
    """

    for obj in container["objects"]:
        if obj["type"] == type:
            return obj
    return None  # in this event, error


class ConverterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        args = (report_path, True, False, converted_path)
        asyncio.run(convert_file(args))
        with open(converted_path, "r") as f:
            cls.content = json.load(f)
        f.close()

        cls.ops = ValidationOptions(disabled="202")  # disable suggested relationship

    def test_bundle(self):
        try:
            file_res = validate_file(converted_path, self.ops)
            self.assertTrue(file_res.is_valid)
        except Exception as err:
            print(self.content)
            print(err)

    def test_mal_valid(self):
        mal_res = validate_instance(find_obj(self.content, "malware"), self.ops)
        self.assertTrue(mal_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_mal_warn(
        self,
    ):
        mal_res = validate_instance(find_obj(self.content, "malware"), self.ops)
        self.assertFalse(mal_res.warnings)  # no warnings -> empty list

    def test_mal_anal_valid(self):
        mal_anal_res = validate_instance(
            find_obj(self.content, "malware-analysis"), self.ops
        )
        self.assertTrue(mal_anal_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_mal_anal_warn(self):
        mal_anal_res = validate_instance(
            find_obj(self.content, "malware-analysis"), self.ops
        )
        self.assertFalse(mal_anal_res.warnings)

    def test_report_valid(self):
        reportobj = find_obj(self.content, "report")
        if reportobj is not None:
            rep_res = validate_instance(reportobj, self.ops)
            self.assertTrue(rep_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_report_warn(self):
        rep_res = validate_instance(find_obj(self.content, "report"), self.ops)
        self.assertFalse(rep_res.warnings)

    def test_software_valid(self):
        soft_res = validate_instance(find_obj(self.content, "software"), self.ops)
        self.assertTrue(soft_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_software_warn(self):
        soft_res = validate_instance(find_obj(self.content, "software"), self.ops)
        self.assertFalse(soft_res.warnings)

    def test_net_traffic_valid(self):
        net_traffic_res = validate_instance(
            find_obj(self.content, "network-traffic"), self.ops
        )
        self.assertTrue(net_traffic_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_net_traffic_warn(self):
        net_traffic_res = validate_instance(
            find_obj(self.content, "network-traffic"), self.ops
        )
        self.assertFalse(net_traffic_res.warnings)

    def test_ipv4_addr_valid(self):
        ipv4_res = validate_instance(find_obj(self.content, "ipv4-addr"), self.ops)
        self.assertTrue(ipv4_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_ipv4_addr_warn(self):
        ipv4_res = validate_instance(find_obj(self.content, "ipv4-addr"), self.ops)
        self.assertFalse(ipv4_res.warnings)

    """
    def test_ipv6_addr_valid(self):
        ipv6_res = validate_instance(find_obj(self.content, 'ipv6-addr'), self.ops)
        self.assertTrue(ipv6_res.is_valid)

    def test_ipv6_addr_warn(self):
        ipv6_res = validate_instance(find_obj(self.content, 'ipv6-addr'), self.ops)
        self.assertFalse(ipv6_res.warnings)
    """

    def test_domain_valid(self):
            dom_res = validate_instance(find_obj(self.content, "domain-name"), self.ops)
            self.assertTrue(dom_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_domain_warn(self):
        dom_res = validate_instance(find_obj(self.content, "domain-name"), self.ops)
        self.assertFalse(dom_res.warnings)

    @unittest.skipIf(True, "Not yet in converted report")
    def test_identity_valid(self):
        id_res = validate_instance(find_obj(self.content, "identity"), self.ops)
        self.assertTrue(id_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_identity_warn(self):
        id_res = validate_instance(find_obj(self.content, "identity"), self.ops)
        self.assertFalse(id_res.warnings)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_att_ptrn_valid(self):
        att_ptrn_res = validate_instance(
            find_obj(self.content, "attack-pattern"), self.ops
        )
        self.assertTrue(att_ptrn_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_att_ptrn_warn(self):
        att_ptrn_res = validate_instance(
            find_obj(self.content, "attack-pattern"), self.ops
        )
        self.assertFalse(att_ptrn_res.warnings)

    @unittest.skipIf(True, "Not yet in converted report")
    def test_ext_def_valid(self):
        ext_def_res = validate_instance(
            find_obj(self.content, "extension-definition"), self.ops
        )
        self.assertTrue(ext_def_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_ext_def_warn(self):
        ext_def_res = validate_instance(
            find_obj(self.content, "extension-definition"), self.ops
        )
        self.assertFalse(ext_def_res.warnings)

    def test_loc_valid(self):
        loc_res = validate_instance(find_obj(self.content, "location"), self.ops)
        self.assertTrue(loc_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_loc_warn(self):
        loc_res = validate_instance(find_obj(self.content, "location"), self.ops)
        self.assertFalse(loc_res.warnings)

    def test_mutex_valid(self):
        mutex_res = validate_instance(find_obj(self.content, "mutex"), self.ops)
        self.assertTrue(mutex_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_mutex_warn(self):
        mutex_res = validate_instance(find_obj(self.content, "mutex"), self.ops)
        self.assertFalse(mutex_res.warnings)

    def test_reg_key_valid(self):
        reg_key_res = validate_instance(
            find_obj(self.content, "windows-registry-key"), self.ops
        )
        self.assertTrue(reg_key_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_reg_key_warn(self):
        reg_key_res = validate_instance(
            find_obj(self.content, "windows-registry-key"), self.ops
        )
        self.assertFalse(reg_key_res.warnings)

    def test_file_valid(self):
        file_res = validate_instance(find_obj(self.content, "file"), self.ops)
        self.assertTrue(file_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_file_warn(self):
        file_res = validate_instance(find_obj(self.content, "file"), self.ops)
        self.assertFalse(file_res.warnings)

    def test_dir_valid(self):
        dir_res = validate_instance(find_obj(self.content, "directory"), self.ops)
        self.assertTrue(dir_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_dir_warn(self):
        dir_res = validate_instance(find_obj(self.content, "directory"), self.ops)
        self.assertFalse(dir_res.warnings)

    def test_proc_valid(self):
        proc_res = validate_instance(find_obj(self.content, "process"), self.ops)
        self.assertTrue(proc_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_proc_warn(self):
        proc_res = validate_instance(find_obj(self.content, "process"), self.ops)
        self.assertFalse(proc_res.warnings)

    def test_rel_valid(self):
        rel_res = validate_instance(find_obj(self.content, "relationship"), self.ops)
        self.assertTrue(rel_res.is_valid)

    @unittest.skipIf(SKIP_WARNINGS, "Temporarily skip warnings")
    def test_rel_warn(self):
        rel_res = validate_instance(find_obj(self.content, "relationship"), self.ops)
        self.assertFalse(rel_res.warnings)

    @classmethod
    def tearDownClass(cls):
        os.remove(converted_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)

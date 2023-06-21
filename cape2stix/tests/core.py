# Copyright 2023, Battelle Energy Alliance, LLC
# from ipaddress import IPv4Address
import unittest
from stix2 import (
    File,
    Process,
    Software,
    Directory,
    Mutex,
    DomainName,
    WindowsRegistryKey,
    Artifact,
    EmailAddress,
    MACAddress,
    NetworkTraffic,
    URL,
    UserAccount,
    IPv6Address,
    X509Certificate,
    AutonomousSystem,
    IPv4Address,
)
from cape2stix.core.util import create_object
from cape2stix.core.stix_loader import StixLoader


# Tests to see if any SCO from <https://doself.cs.oasis-open.org/cti/stix/v2.1/self.csprd01/stix-v2.1-self.csprd01.html> is using UUIDv5 properly.
# STIX Cyber-observable Objects SHOULD use UUIDv5 for the UUID portion of the identifier and the UUID portion of the UUIDv5-based identifier SHOULD be generated according to the following rules:
# ●      The namespace SHOULD be 00abedb4-aa42-466c-9c01-fed23315a9b7
# ●      The value of the name portion SHOULD be the list of "ID Contributing Properties" defined on each SCO and those properties SHOULD be stringified according to Jself.cs to ensure a canonical representation of the JSON data.
# ●      Producers not following these rules MUST NOT use a namespace of 00abedb4-aa42-466c-9c01-fed23315a9b7.

# our tests: Artifact, AS, Directory, Domain Name, Email Address, Email Message, File Object w/ extensions (Archive File, NFTS File, PDF File, Raster Image File, Windows PE file), IPv4 Address, IPv6 Address, MAC Address, Mutex,
#           Network Traffic (HTTP Request Ext, ICMP Ext, TCP Ext), Process (Windows Process Ext, Windows Service Ext), Software, URL, User Account, Windows Registry Key, X.509

# def testSoftware():


class Tester:
    """
    Tester class
    """

    def __init__(self, allow_custom=True):
        self.allow_custom = allow_custom
        self.sl = StixLoader(allow_custom=self.allow_custom)
        self.objects = []

    def add_objects(self, obj):
        for item in obj:
            self.sl.add_item(item)

    def create_object(self, cls, *args, **kwargs):
        """
        wraps util.create_object to ensure that the custom_object parameter is set consistently.
        """
        return create_object(cls, *args, **kwargs, custom_object=self.allow_custom)

    # _id_contributing_properties = ["hashes", "payload_bin"]
    def genArtifact(self, payload_bin=None, hashes=None):
        payload_bin = payload_bin
        l = self.create_object(Artifact, payload_bin=payload_bin, hashes=hashes)
        return l

    # _id_contributing_properties = ["number"]
    def genAutonomousSystem(self, number):
        number = number
        l = self.create_object(AutonomousSystem, number=number)
        return l

    # _id_contributing_properties = ["path"]
    def genDirectory(self, path):
        thispath = path
        l = self.create_object(Directory, path=thispath)
        return l

    #  _id_contributing_properties = ["value"]
    def genDomainName(self, value):
        value = value
        l = self.create_object(DomainName, value=value)
        return l

    # _id_contributing_properties = ["value"]
    def genEmailAddress(self, thisemail):
        l = self.create_object(EmailAddress, value=thisemail)
        return l

    # Optional properties contribute to id
    # _id_contributing_properties = ["hashes", "name", "parent_directory_ref", "extensions"]
    def genFileObject(
        self, thisfile, hashes=None, parent_directory_ref=None, extensions=None
    ):
        l = self.create_object(File, name=thisfile)
        return l

    # _id_contributing_properties = ["value"]
    def genIPv4(self, thisvalue):
        l = self.create_object(IPv4Address, value=thisvalue)
        return l

    # _id_contributing_properties = ["value"]
    def genIPv6(self, thisvalue):
        l = self.create_object(IPv6Address, value=thisvalue)
        return l

    #  "value": "d2:fb:49:24:37:18"
    # _id_contributing_properties = ["value"]
    def genMAC(self, thismac):
        l = self.create_object(MACAddress, value=thismac)
        return l

    # _id_contributing_properties = ["name"]
    def genMutexes(self, mutex_name):
        # behavior/summary/mutexes
        l = self.create_object(Mutex, name=mutex_name)
        return l

    # required: protocols (LIST)
    # required: must create ipv4 object
    # _id_contributing_properties = ["start", "end", "src_ref", "dst_ref", "src_port", "dst_port", "protocols", "extensions"]
    def genNetworkTraffic(self, protocols):
        ipv4 = self.create_object(IPv4Address, value="198.51.100.2")
        l = self.create_object(NetworkTraffic, src_ref=ipv4, protocols=protocols)
        return l

    # recommend using uuidv4 for this
    # _id_contributing_properties = []
    def genProcess(self, command_line, hash):

        l = self.create_object(Process, command_line=command_line, hash=hash)
        return l

    # _id_contributing_properties = ["name", "cpe", "swid", "vendor", "version"]
    def genSoftware(self, name, cpe, swid, vendor, version):
        name = name

        l = self.create_object(
            Software, name=name, cpe=cpe, swid=swid, vendor=vendor, verison=version
        )
        return l

    # _id_contributing_properties = ["value"]
    def genURL(self, value):
        value = value
        l = self.create_object(URL, value=value)
        return l

    # _id_contributing_properties = ["account_type", "user_id", "account_login"]
    def genUserAccount(self, account_type, user_id, account_login):

        l = self.create_object(
            UserAccount,
            account_type=account_type,
            user_id=user_id,
            account_login=account_login,
        )
        return l

    # _id_contributing_properties = ["key", "values"]
    def genWinRegKey(self, key, values):
        l = self.create_object(WindowsRegistryKey, key=key, values=values)
        return l

    # _id_contributing_properties = ["hashes", "serial_number"]
    def genX509(self, serial_number):
        l = self.create_object(X509Certificate, serial_number=serial_number)
        return l

    def runTests(self):  # run all tests
        self.add_objects(self.genMutexes())
        self.sl.write_out("Test_MalwareAnalysisCAPE2.json")


class TestStringMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cs = Tester(allow_custom=True)

    def testArtifact(self):
        artifact = "VBORw0KGgoAAAANSUhEUgAAADI== ..."
        artifact2 = "VBORw0KGgoAAAANSUhEUgAAADI== ...12"
        self.assertTrue(
            self.cs.genArtifact(artifact).id == self.cs.genArtifact(artifact).id
        )
        self.assertFalse(
            self.cs.genArtifact(artifact).id == self.cs.genArtifact(artifact2).id
        )

    def testAutonomousSystem(self):
        number = 12345
        number2 = 12342
        self.assertTrue(
            self.cs.genAutonomousSystem(number).id
            == self.cs.genAutonomousSystem(number).id
        )
        self.assertFalse(
            self.cs.genAutonomousSystem(number).id
            == self.cs.genAutonomousSystem(number2).id
        )

    def testDirectory(self):
        path1 = "/home/franky/test/"
        path2 = "/home/alice/repos"
        self.assertTrue(
            self.cs.genDirectory(path1).id == self.cs.genDirectory(path1).id
        )
        self.assertFalse(
            self.cs.genDirectory(path1).id == self.cs.genDirectory(path2).id
        )

    def testDomainName(self):
        domainname = "purdue.edu"
        domainname2 = "rice.edu"
        self.assertTrue(
            self.cs.genDomainName(domainname).id == self.cs.genDomainName(domainname).id
        )
        self.assertFalse(
            self.cs.genDomainName(domainname).id
            == self.cs.genDomainName(domainname2).id
        )

    def testEmailAddress(self):
        email1 = "franky@purdue.edu"
        email2 = "alice@rice.edu"
        self.assertTrue(
            self.cs.genEmailAddress(email1).id == self.cs.genEmailAddress(email1).id
        )
        self.assertFalse(
            self.cs.genEmailAddress(email1).id == self.cs.genEmailAddress(email2).id
        )

    def testFileName(self):
        filename = "test.txt"
        filename2 = "text2.mp4"
        self.assertTrue(
            self.cs.genFileObject(filename).id == self.cs.genFileObject(filename).id
        )
        self.assertFalse(
            self.cs.genFileObject(filename).id == self.cs.genFileObject(filename2).id
        )

    # def testIPV4(self):
    #     ip1='169.254.255.215'
    #     ip2='169.254.255.252'
    #     self.assertTrue(self.cs.genIPv4(ip1).id == self.cs.genIPv4(ip1).id)
    #     self.assertFalse(self.cs.genIPv4(ip1).id == self.cs.genIPv4(ip2).id)

    def testIPV6(self):
        ip1 = "fe80::260:97ff:fe02:6ea5"
        ip2 = "fe80::210:5aff:feaa:20a2"
        self.assertTrue(self.cs.genIPv6(ip1).id == self.cs.genIPv6(ip1).id)
        self.assertFalse(self.cs.genIPv6(ip1).id == self.cs.genIPv6(ip2).id)

    def testMAC(self):
        mac1 = "00:00:5e:00:53:af"
        mac2 = "00:1b:63:84:45:e6"
        self.assertTrue(self.cs.genMAC(mac1).id == self.cs.genMAC(mac1).id)
        self.assertFalse(self.cs.genMAC(mac1).id == self.cs.genMAC(mac2).id)

    def testMutexes(self):
        mutexstring = "__CLEANSWEEP__"
        mutexstring2 = "__CLEANSWEEP2__"
        self.assertTrue(
            self.cs.genMutexes(mutexstring).id == self.cs.genMutexes(mutexstring).id
        )
        self.assertFalse(
            self.cs.genMutexes(mutexstring).id == self.cs.genMutexes(mutexstring2).id
        )

    def testNetworkTraffic(self):
        # TODO: add in more props
        protocols1 = ["ipv4", "tcp", "http"]
        protocols2 = ["tcp"]
        self.assertTrue(
            self.cs.genNetworkTraffic(protocols1).id
            == self.cs.genNetworkTraffic(protocols1).id
        )
        self.assertFalse(
            self.cs.genNetworkTraffic(protocols1).id
            == self.cs.genNetworkTraffic(protocols2).id
        )

    def testProcess(self):
        command_1 = "sudo su"
        command_2 = "cd /home/user"

        hash = {}
        hash[
            "SHA-256"
        ] = "aec070645fe53ee3b3763059376134f058cc337247c978add178b6ccdfb0019f"
        hash2 = {}
        hash[
            "SHA-256"
        ] = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        # Process should always be uuid4, so ensure no properties contribute to the uuid
        self.assertFalse(
            self.cs.genProcess(command_1, hash).id
            == self.cs.genProcess(command_1, hash).id
        )
        self.assertFalse(
            self.cs.genProcess(command_1, hash).id
            == self.cs.genProcess(command_2, hash2).id
        )

    def testSoftware(self):
        name = "Word"
        cpe = "cpe:2.3:a:microsoft:word:2000:*:*:*:*:*:*:*"
        version = "2002"
        vendor = "Microsoft"
        swid = ""

        swid2 = "asdf"
        version2 = "2006"

        self.assertTrue(
            self.cs.genSoftware(name, cpe, swid, vendor, version).id
            == self.cs.genSoftware(name, cpe, swid, vendor, version).id
        )

        # a single difference in contributing properties still returns the same uuid. (version)
        self.assertTrue(
            self.cs.genSoftware(name, cpe, swid, vendor, version).id
            == self.cs.genSoftware(name, cpe, swid, vendor, version2).id
        )
        # now change swid to swid2
        self.assertFalse(
            self.cs.genSoftware(name, cpe, swid, vendor, version).id
            == self.cs.genSoftware(name, cpe, swid2, vendor, version2).id
        )

    def testURL(self):
        """ """
        url = "https://example.com/research/index.html"
        url2 = "https://example2.com/research/index.html"

        self.assertTrue(self.cs.genURL(url).id == self.cs.genURL(url).id)
        self.assertFalse(self.cs.genURL(url).id == self.cs.genURL(url2).id)

    def testUserAccount(self):
        # _id_contributing_properties = ["account_type", "user_id", "account_login"]

        account_type = "unix"
        user_id = "1001"
        account_login = "jdoe"

        user_id2 = "1002"
        account_login2 = "jsmith"

        self.assertTrue(
            self.cs.genUserAccount(account_type, user_id, account_login).id
            == self.cs.genUserAccount(account_type, user_id, account_login).id
        )
        self.assertFalse(
            self.cs.genUserAccount(account_type, user_id, account_login).id
            == self.cs.genUserAccount(account_type, user_id2, account_login2).id
        )

    def testWinRegKey(self):
        # key, values
        key = "HKEY_LOCAL_MACHINE\\System\\Foo\\Bar"

        values = []
        values2 = []

        dict1 = {}
        dict1["name"] = "Foo"
        dict1["data"] = "qwerty"
        dict1["data_type"] = "REG_DWORD"

        dict2 = {}
        dict2["name"] = "Bar"
        dict2["data"] = "42"
        dict2["data_type"] = "REG_DWORD"

        values.append(dict1)
        values2.append(dict2)

        self.assertTrue(
            self.cs.genWinRegKey(key, values).id == self.cs.genWinRegKey(key, values).id
        )
        self.assertFalse(
            self.cs.genWinRegKey(key, values).id
            == self.cs.genWinRegKey(key, values2).id
        )

    def testX509Certificate(self):
        serial1 = "36:f7:d4:32:f4:ab:70:ea:d3:ce:98:6e:ea:99:93:49:32:0a:b7:06"
        serial2 = '02:08:87:83:f2:13:58:1f:79:52:1e:66:90:0a:02:24:c9:6b:c7:dc"'
        self.assertTrue(self.cs.genX509(serial1).id == self.cs.genX509(serial1).id)
        self.assertFalse(self.cs.genX509(serial1).id == self.cs.genX509(serial2).id)


if __name__ == "__main__":
    unittest.main()

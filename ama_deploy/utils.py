# Copyright 2023, Battelle Energy Alliance, LLC
import tomli
from tqdm import tqdm
from hashlib import sha256
from subprocess import run
import tarfile
import shutil
import os


def ovf_gen(ovf_template, replace_dict, outname):
    with open(ovf_template) as f:
        template = f.read()
    for key, val in replace_dict.items():
        template = template.replace(key, str(val))
    with open(outname, "w") as f:
        f.write(template)


def mf_gen(mf_template, replace_dict, outname):
    with open(mf_template) as f:
        template = f.read()
    for key, val in replace_dict.items():
        template = template.replace(key, str(val))
    with open(outname, "w") as f:
        f.write(template)


def sha256hashfile(file_path):
    with open(file_path, "rb") as f:
        m = sha256()
        chunk = f.read(8192)
        while chunk:
            m.update(chunk)
            chunk = f.read(8192)
    return str(m.hexdigest())


def convertqcow2(in_path, out_path):
    cmd = [
        "qemu-img",
        "convert",
        "-O",
        "vmdk",
        "-o",
        "subformat=streamOptimized",
        in_path,
        out_path,
    ]
    process = run(cmd)
    process.check_returncode()


def makeova(vm_name, vm_path):
    ovf_template = "./packertovcloud/testvm.ovf"
    mf_template = "./packertovcloud/testvm.mf"
    if not os.path.exists("./tmp"):
        os.mkdir("./tmp")

    base_name = vm_name
    disk_name = base_name + "-disk1.vmdk"
    file_path = vm_path
    new_disk_path = join("./tmp", disk_name)
    convertqcow2(file_path, new_disk_path)

    disk_size = os.path.getsize(new_disk_path)
    disk_hash = sha256hashfile(new_disk_path)
    ovf_path = join("./tmp", base_name + ".ovf")
    d = {
        "<disk_size>": disk_size,
        "<disk_hash>": disk_hash,
        "<vm_name>": base_name,
        "<disk_name>": disk_name,
    }
    ovf_gen(ovf_template, d, ovf_path)
    d["<ovf_hash>"] = sha256hashfile(ovf_path)
    mf_path = join("./tmp", base_name + ".mf")

    mf_gen(mf_template, d, mf_path)
    taritems([ovf_path, mf_path, new_disk_path], base_name + ".ova")
    return base_name + ".ova"


def taritems(in_items, tar_path):
    tar = tarfile.open(tar_path, mode="w")
    for name in in_items:
        tar.add(name, arcname=os.path.basename(name))
    tar.close()


def join(*args):
    return os.path.join(*args)

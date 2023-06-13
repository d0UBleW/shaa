from __future__ import annotations

from ruamel.yaml import YAML
from typing import Text, Dict, Any, Optional, List
from shaa_shell.utils.vault import vault_password
import subprocess
import os
import sys

from shaa_shell.utils.cis import CIS
from shaa_shell.utils.inventory import Inventory
from shaa_shell.utils.profile import Profile
from shaa_shell.utils.path import (
    PLAYBOOK_PATH,
    ANSIBLE_INV_PATH,
)

yaml = YAML(typ="rt")


def section_var(section_id: Text):
    return f"section_{section_id.replace('.', '_')}"


def convert_cis_to_ansible_vars(name: Text) -> Dict[Text, Any]:
    cis = CIS.load(name)
    if cis is None:
        return {}
    vars = {}
    for section_id, section in cis.sections.items():
        vars[section_var(section_id)] = section["enabled"]
        if "vars" in section.keys() and section["vars"] is not None:
            for var_key, var in section["vars"].items():
                val = var["value"]
                if val is None:
                    val = var["default"]
                vars[var_key] = val

    return vars


def generate_tags(profile: Profile) -> Optional[List]:
    presets = profile.presets
    if "cis" not in presets.keys():
        return None
    if presets["cis"] is None:
        return None
    cis: Optional[CIS] = CIS.load(presets["cis"])
    if cis is None:
        print("[!] CIS preset name not found")
        return None
    s = []
    for s_id in cis.sections.keys():
        if "subsections" in cis.sections[s_id].keys():
            continue
        if not cis.sections[s_id]["enabled"]:
            continue
        if s_id.count('.') < 2:
            s.append(f"{s_id}.x")
        else:
            s.append(s_id)
    return s


def generate_playbook(profile: Profile) -> bool:
    name = profile.name
    presets = profile.presets

    all_vars = {}
    if "cis" in presets.keys() and presets["cis"] is not None:
        cis_vars = convert_cis_to_ansible_vars(presets["cis"])
        all_vars.update(cis_vars)

    inv_name = profile.inv_name
    if inv_name is not None:
        inv = Inventory.load(inv_name)

    if inv is None:
        return False

    inv.groups["ungrouped"].group_vars = all_vars
    inv.save(name, ANSIBLE_INV_PATH)

    data = [{
        "name": name,
        "become": True,
        "gather_facts": True,
        "hosts": "all",  # TODO: allow group targeting
        "roles": [{
            "role": "cis_independent_linux",
        }]
    }]

    playbook_fpath = PLAYBOOK_PATH.joinpath(f"{name}.yml").resolve()

    with open(playbook_fpath, "w") as f:
        yaml.dump(data, f)

    return True


def run_playbook(name: Text,
                 tags: Optional[List],
                 verbose: Optional[bool] = True,
                 color: Optional[bool] = True) -> None:
    # TODO: verbose == False --> use tags
    inv_fpath = ANSIBLE_INV_PATH.joinpath(f"{name}.yml").resolve().__str__()
    playbook_fpath = PLAYBOOK_PATH.joinpath(f"{name}.yml").resolve().__str__()
    ansible_cfg = PLAYBOOK_PATH.joinpath("ansible.cfg").resolve().__str__()
    if vault_password is None:
        print("Missing ansible vault password")
        return
    envs = {
        "ANSIBLE_CONFIG": ansible_cfg,
        "VAULT_PASSWORD": vault_password,
        "ANSIBLE_FORCE_COLOR": str(color),
    }
    envs.update(os.environ)
    args = ["ansible-playbook", "-i", inv_fpath, playbook_fpath]
    if not verbose and tags is not None:
        args.append("--tags")
        args.append(",".join(tags))
    print(f"[*] {' '.join(args)}")
    with subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=envs
    ) as proc:
        with open("/tmp/shaa_shell_playbook.log", "w") as f:
            while proc.poll() is None:
                if proc.stdout is not None:
                    data: Text = proc.stdout.readline().decode('utf-8')
                    sys.stdout.write(data)
                    f.write(data)

        sys.stdout.write(f"return code: {proc.poll()}")

#!/usr/bin/env python3

from ruamel.yaml import YAML
from pathlib import Path
from typing import Text, Dict, Any
from utils.cis import CIS
from utils.inventory import Inventory

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


def generate_playbook(name: Text):
    with open(f"data/custom/profile/{name}.yml") as f:
        data = yaml.load(f)

    cis_vars = convert_cis_to_ansible_vars(data["cis"])
    inv = Inventory.load(data["inventory"])
    if inv is None:
        print("inv is None")
        return
    inv.groups["ungrouped"].group_vars = cis_vars
    inv.save(name, Path("../ansible/inventory"))

    data = [{
        "name": name,
        "become": True,
        "gather_facts": True,
        "hosts": "all",  # TODO: allow group targeting
        "roles": [{
            "role": "cis_independent_linux",
        }]
    }]

    playbook_file_path = Path("../ansible").joinpath(f"{name}.yml").resolve()

    with open(playbook_file_path, "w") as f:
        yaml.dump(data, f)

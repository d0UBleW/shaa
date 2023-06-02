from __future__ import annotations

from ruamel.yaml import YAML
from typing import Text, Dict, Any
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

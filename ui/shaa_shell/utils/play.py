from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Text, Tuple

from ruamel.yaml import YAML

from shaa_shell.utils import exception
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.inventory import Inventory
from shaa_shell.utils.path import (ANSIBLE_CFG_PATH, ANSIBLE_INV_PATH,
                                   ANSIBLE_VAULT_PASSWORD, LOG_PATH,
                                   OSCAP_REPORT_PATH, PLAYBOOK_PATH,
                                   SSH_PRIV_KEY_PATH)
from shaa_shell.utils.preset import PRESET_ROLE_MAP, PRESETS
from shaa_shell.utils.profile import Profile
from shaa_shell.utils.role import Role
from shaa_shell.utils.vault import vault_password

yaml = YAML(typ="rt")


def expand_nested_key(d: Dict[Text, Any]):
    nested_key = []
    for key in d.keys():
        if "." in key:
            nested_key.append(key)

    for key in nested_key:
        val = d[key]
        del d[key]
        ref = None
        child = key
        while child != "":
            parent, _, child = child.partition(".")
            if ref is None:
                if parent not in d.keys():
                    d[parent] = {}
                ref = d[parent]
            else:
                if child == "":
                    ref[parent] = val
                    break
                if parent not in ref.keys():
                    ref[parent] = {}
                ref = ref[parent]


def section_var(section_id: Text):
    """
    Convert section id with dots to underscore to match ansible role variables
    """
    return f"section_{section_id.replace('.', '_')}"


def convert_cis_to_ansible_vars(name: Text) -> Dict[Text, Any]:
    """
    Convert CIS preset to ansible role variables
    """
    cis = CIS.load(name)
    if cis is None:
        return {}
    ansible_vars = {}
    for s_id, section in cis.sections.items():
        ansible_vars[section_var(s_id)] = cis.get_enabled(s_id)
        if "vars" in section.keys() and section["vars"] is not None:
            for var_key, var in section["vars"].items():
                val = cis.get_var(s_id, var_key)
                if val is None:
                    val = var["default"]
                ansible_vars[var_key] = val

    # for variables with nested key
    # e.g., systemd_timesyncd.fallback_ntp
    expand_nested_key(ansible_vars)
    return ansible_vars


def convert_role_vars_to_ansible_vars(role_type: Text,
                                      name: Text) -> Dict[Text, Any]:
    """
    Convert role preset to ansible role variables
    """
    role: Optional[Role] = Role.load(role_type, name)
    if role is None:
        return {}
    ansible_vars = {}
    for action, task in role.actions.items():
        ansible_vars[action] = role.get_enabled(action)
        if not role.has_settable_vars(action):
            continue
        for var_key, var in task["vars"].items():
            val = role.get_var(action, var_key)
            if val is None:
                val = var["default"]
            ansible_vars[var_key] = val

    # for variables with nested key
    # e.g., systemd_timesyncd.fallback_ntp
    expand_nested_key(ansible_vars)
    return ansible_vars


def final_presets(profile: Profile, arg_presets: List[Text]) -> Dict:
    presets = {}
    if len(arg_presets) > 0:
        for preset in arg_presets:
            if preset not in PRESETS:
                raise exception.ShaaNameError(f"Invalid preset: {preset}")
            presets[preset] = profile.presets[preset]
    else:
        presets = profile.presets

    return presets


def generate_tags(profile: Profile, arg_presets: List[Text]) -> Optional[List]:
    """
    Generate ansible tags based on enabled sections or actions
    """
    try:
        presets = final_presets(profile, arg_presets)
    except exception.ShaaNameError:
        raise

    tags: List[Text] = []

    """
    Generate tags for CIS preset
    """
    if "cis" in presets.keys():
        try:
            cis_tags = generate_cis_tags(presets["cis"])
        except exception.ShaaNameError:
            raise
        if cis_tags is not None:
            tags += cis_tags

    """
    Generate tags for presets other than CIS
    """
    for role_type in presets.keys():
        if role_type == "cis":
            continue
        try:
            role_tags = generate_role_tags(role_type, presets[role_type])
        except exception.ShaaNameError:
            raise
        if role_tags is not None:
            tags += role_tags

    return tags


def generate_cis_tags(pre_name: Optional[Text]) -> Optional[List]:
    """
    Generate CIS tags
    """
    if pre_name is None:
        return None
    try:
        cis: Optional[CIS] = CIS.load(pre_name)
    except exception.ShaaNameError:
        raise
    if cis is None:
        print(f"[!] CIS preset name not found: {pre_name}")
        return None
    tags = []
    for s_id in cis.sections.keys():
        if "subsections" in cis.sections[s_id].keys():
            continue
        if not cis.get_enabled(s_id):
            continue
        if s_id.count('.') < 2:
            tags.append(f"{s_id}.x")
        else:
            tags.append(s_id)
    return tags


def generate_role_tags(role_type: Text,
                       pre_name: Optional[Text]) -> Optional[List]:
    """
    Generate tags for role preset other than CIS
    """
    if pre_name is None:
        return None
    try:
        role: Optional[Role] = Role.load(role_type, pre_name)
    except exception.ShaaNameError:
        raise
    if role is None:
        print(f"[!] {role_type} preset name not found: {pre_name}")
        return None
    tags = []
    for action in role.actions.keys():
        if not role.get_enabled(action):
            continue
        tags.append(action)
    return tags


def generate_inventory(profile: Profile, arg_presets: List[Text]) -> None:
    try:
        presets = final_presets(profile, arg_presets)
    except exception.ShaaNameError:
        raise

    all_vars = {}
    # Convert CIS variables
    if "cis" in presets.keys() and presets["cis"] is not None:
        print("[+] Converting CIS preset variables")
        cis_vars = convert_cis_to_ansible_vars(presets["cis"])
        all_vars.update(cis_vars)
        print("[+] Done converting CIS preset variable")

    # Convert role presets variables aside from CIS
    for role_type in presets.keys():
        if role_type == "cis":
            continue
        role_name = presets[role_type]
        if role_type in presets.keys() and role_name is not None:
            print(f"[+] Converting {role_type} preset variables")
            role_vars = convert_role_vars_to_ansible_vars(role_type, role_name)
            all_vars.update(role_vars)
            if role_type == "oscap":
                all_vars["oscap_report_dir"] = str(OSCAP_REPORT_PATH)
            print(f"[+] Done converting {role_type} preset variable")

    # Validate inventory data
    inv_name = profile.inv_name
    if inv_name is None:
        raise exception.ShaaInventoryError(
            "No inventory is set on current profile")
    if inv_name is not None:
        try:
            inv = Inventory.load(inv_name)
        except exception.ShaaInventoryError:
            raise

    if len(inv.groups) == 1 and len(inv.groups["ungrouped"].nodes) == 0:
        raise exception.ShaaInventoryError(
            "Inventory data is empty, try to save it first if you have not")

    # Generate inventory file with all variables
    inv.groups["ungrouped"].group_vars = all_vars

    for group in inv.groups.values():
        for node in group.nodes.values():
            if node.ssh_priv_key_path is not None:
                node.ssh_priv_key_path = str(SSH_PRIV_KEY_PATH.joinpath(
                    node.ssh_priv_key_path))
            expand_nested_key(node.host_vars)

    inv.save(profile.name, ANSIBLE_INV_PATH, overwrite=True)


def generate_playbook(profile: Profile,
                      arg_presets: List[Text],
                      targets: Optional[List] = ["all"]
                      ) -> None:
    """
    Generate playbook based on profile and specified presets
    """
    try:
        presets = final_presets(profile, arg_presets)
    except exception.ShaaNameError:
        raise

    # Collect roles that need to be run
    roles = []
    for preset, val in presets.items():
        if preset == "util" or val is None:
            continue
        role = {"role": PRESET_ROLE_MAP[preset]}
        roles.append(role)

    name = profile.name

    data = [{
        "name": name,
        "become": True,
        "gather_facts": True,
        "hosts": targets,
        "roles": roles,
    }]

    util_pb = [{
        "name": f"{name} - Util",
        "become": False,
        "gather_facts": False,
        "hosts": "localhost",
        "roles": [{
            "role": PRESET_ROLE_MAP["util"],
        }]
    }]

    if len(roles) == 0 and "util" not in presets:
        raise exception.ShaaNameError("No preset is provided, aborting!")

    playbook_fpath = PLAYBOOK_PATH.joinpath(f"{name}.yml").resolve()

    # Create the playbook
    playbook_fpath.parent.mkdir(parents=True, exist_ok=True)
    with playbook_fpath.open("w") as f:
        if len(roles) > 0:
            yaml.dump(data, f)
        if "util" in presets and presets["util"] is not None:
            yaml.dump(util_pb, f)


def run_playbook(name: Text,
                 tags: Optional[List],
                 verbose: Optional[bool] = True,
                 color: Optional[bool] = True) -> None:
    """
    Run playbook
    """
    inv_fpath = str(ANSIBLE_INV_PATH.joinpath(f"{name}.yml").resolve())
    playbook_fpath = str(PLAYBOOK_PATH.joinpath(f"{name}.yml").resolve())
    ansible_cfg = str(ANSIBLE_CFG_PATH.resolve())

    if vault_password is None:
        raise exception.ShaaVaultError("Missing ansible vault password")

    # Setup environment variable
    envs = {
        "ANSIBLE_CONFIG": ansible_cfg,
        "VAULT_PASSWORD": vault_password,
        "ANSIBLE_FORCE_COLOR": str(color),
        "ANSIBLE_HOST_KEY_CHECKING": "False",
        "ANSIBLE_VAULT_PASSWORD_FILE": str(ANSIBLE_VAULT_PASSWORD),
    }
    envs.update(os.environ)

    args = ["ansible-playbook", "-i", inv_fpath, playbook_fpath]

    # Prepare tags
    if not verbose and tags is not None:
        if len(tags) == 0:
            tags.append("NON_EXISTENT")
        args.append("--tags")
        args.append(",".join(tags))

    print(f"[*] {' '.join(args)}")

    # Run the playbook
    start_time = time.time()
    with subprocess.Popen(
        args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=envs
    ) as proc:
        now = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        log_file = LOG_PATH.joinpath(f"{name}-{now}")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("w") as f:
            f.write(f"[*] {' '.join(args)}\n\n")
            while proc.poll() is None:
                if proc.stdout is not None:
                    data: Text = proc.stdout.readline().decode('utf-8')
                    sys.stdout.write(data)
                    f.write(data)
    end_time = time.time()
    print(f"[*] Time taken: {timedelta(seconds=end_time-start_time)}")

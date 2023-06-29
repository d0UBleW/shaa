from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import Text, List
import re

ROOT_PATH = Path(importlib.resources.files("shaa_shell").__str__())

DATA_PATH = ROOT_PATH.joinpath("data/")

PROFILE_PATH = ROOT_PATH.joinpath("data/custom/profile")
INVENTORY_PATH = ROOT_PATH.joinpath("data/custom/inventory/")

CIS_PRESET_PATH = ROOT_PATH.joinpath("data/custom/cis/")
CIS_TEMPLATE_FILE = ROOT_PATH.joinpath("data/template/cis.yml")

OSCAP_PRESET_PATH = ROOT_PATH.joinpath("data/custom/oscap/")
OSCAP_TEMPLATE_FILE = ROOT_PATH.joinpath("data/template/oscap.yml")

UTIL_PRESET_PATH = ROOT_PATH.joinpath("data/custom/util/")
UTIL_TEMPLATE_FILE = ROOT_PATH.joinpath("data/template/util.yml")

SEC_TOOLS_PRESET_PATH = ROOT_PATH.joinpath("data/custom/sec_tools/")
SEC_TOOLS_TEMPLATE_FILE = ROOT_PATH.joinpath("data/template/sec_tools.yml")

PLAYBOOK_PATH = ROOT_PATH.joinpath("data/ansible/playbook")
ANSIBLE_INV_PATH = ROOT_PATH.joinpath("data/ansible/inventory/")
LOG_PATH = ROOT_PATH.joinpath("log/")

ANSIBLE_PATH = ROOT_PATH.joinpath("../../ansible")
ANSIBLE_VAULT_PASSWORD = ANSIBLE_PATH.joinpath("vault-password.py")
ROLE_PATH = ANSIBLE_PATH.joinpath("roles/")


def is_valid_file_path(parent: Path, file_name: Text) -> bool:
    for c in file_name:
        if c in "~`!@#$%^&*()+='\";:{}[]":
            return False

    file_path = parent.joinpath(file_name).resolve()
    try:
        file_path.relative_to(parent.resolve())
    except ValueError:
        return False

    return True


def filter_file(parent_path: Path, glob_pattern, search_pattern) -> List[Text]:
    files = parent_path.rglob(glob_pattern)
    result = []
    for file in files:
        if not file.is_file():
            continue
        fname_no_ext = file.parent.joinpath(file.stem)
        relative_path = fname_no_ext.relative_to(parent_path)
        if re.search(search_pattern, str(relative_path)):
            result.append(str(relative_path))
    return result


def resolve_path(str_path: Text, parent_path: Path) -> Text:
    final = parent_path.joinpath(str_path).resolve()
    fname_no_ext = final.parent.joinpath(final.stem)
    relative_path = fname_no_ext.relative_to(parent_path)
    return str(relative_path)

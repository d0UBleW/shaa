from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import Text

ROOT_PATH = Path(importlib.resources.files("shaa_shell").__str__())

PROFILE_PATH = ROOT_PATH.joinpath("data/custom/profile")
INVENTORY_PATH = ROOT_PATH.joinpath("data/custom/inventory/")

CIS_PRESET_PATH = ROOT_PATH.joinpath("data/custom/cis/")
CIS_TEMPLATE_FILE = ROOT_PATH.joinpath("data/template/cis.yml")

OSCAP_PRESET_PATH = ROOT_PATH.joinpath("data/custom/oscap/")
OSCAP_TEMPLATE_FILE = ROOT_PATH.joinpath("data/template/oscap.yml")

EXTRA_PRESET_PATH = ROOT_PATH.joinpath("data/custom/extra/")
EXTRA_TEMPLATE_FILE = ROOT_PATH.joinpath("data/template/extra.yml")

PLAYBOOK_PATH = ROOT_PATH.joinpath("../../ansible/")
ANSIBLE_INV_PATH = ROOT_PATH.joinpath("../../ansible/inventory/")


def is_valid_file_path(parent: Path, file_name: Text) -> bool:
    for c in file_name:
        if c in "/~`!@#$%^&*()+='\";:{}[]":
            return False

    file_path = parent.joinpath(file_name).resolve()
    try:
        file_path.relative_to(parent.resolve())
    except ValueError:
        return False

    return True

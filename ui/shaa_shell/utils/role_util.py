from __future__ import annotations

import re
from ruamel.yaml import YAML  # type: ignore[import]
from ruamel.yaml.comments import TaggedScalar  # type: ignore[import]
from typing import Optional, Text, Dict, List, Tuple, Any, Union
from pathlib import Path

from shaa_shell.utils.preset import list_preset
from shaa_shell.utils.path import (
    UTIL_PRESET_PATH,
    UTIL_TEMPLATE_FILE,
    is_valid_file_path,
)
from shaa_shell.utils.vault import vault

yaml = YAML(typ="rt")


class RoleUtil:
    def __init__(self, name: Text, data: Optional[Dict] = None):
        self.name = name

        if data is None:
            with open(UTIL_TEMPLATE_FILE, "r") as f:
                data = yaml.load(f)

        self.actions = data["actions"]

    def save(self, file_name: Optional[Text] = None) -> bool:
        """
        Dump role util data into a YAML file
        """
        if file_name is not None and file_name in RoleUtil.list_preset():
            print("[!] Specified util preset name exists")
            return False

        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(UTIL_PRESET_PATH, f"{file_name}.yml"):
            return False

        file_path = UTIL_PRESET_PATH.joinpath(f"{file_name}.yml").resolve()

        data = {
            "actions": self.actions
        }

        with open(file_path, 'w') as f:
            yaml.dump(data, f)

        return True

    def delete(self) -> None:
        file_path = UTIL_PRESET_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)

    def rename(self, new_name: Text) -> bool:
        if not self.save(new_name):
            return False

        self.delete()
        self.name = new_name
        return True

    @staticmethod
    def load(name: Text) -> Optional[RoleUtil]:
        """
        Load CIS preset from YAML file to Python object
        """
        if not is_valid_file_path(UTIL_PRESET_PATH, f"{name}.yml"):
            print("[!] Invalid util preset name")
            return None

        if name not in RoleUtil.list_preset():
            print(f"[!] util preset name not found: {name}")
            return None

        file_path = UTIL_PRESET_PATH.joinpath(f"{name}.yml").resolve()
        with open(file_path, "r") as f:
            data: Dict = yaml.load(f)

        if "actions" not in data.keys():
            print("[!] Invalid util preset file: missing `actions` key")
            return None

        role_util = RoleUtil(name, data)
        return role_util

    @staticmethod
    def create(name: Text) -> Optional[RoleUtil]:
        """
        Function wrapper for creating CIS object
        """
        if name in RoleUtil.list_preset():
            return None

        if not is_valid_file_path(UTIL_PRESET_PATH, f"{name}.yml"):
            return None

        role_util = RoleUtil(name)
        return role_util

    @staticmethod
    def list_preset(pattern: Text = ".*") -> List[Text]:
        """
        List util preset based on given pattern
        """
        return list_preset("util", pattern)

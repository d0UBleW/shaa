from __future__ import annotations

import re
from ruamel.yaml import YAML  # type: ignore[import]
from ruamel.yaml.comments import TaggedScalar  # type: ignore[import]
from typing import Optional, Text, Dict, List, Tuple, Any, Union
from pathlib import Path

from shaa_shell.utils.preset import list_preset
from shaa_shell.utils.path import (
    is_valid_file_path,
    UTIL_TEMPLATE_FILE,
    UTIL_PRESET_PATH,
    OSCAP_TEMPLATE_FILE,
    OSCAP_PRESET_PATH,
)
from shaa_shell.utils.vault import vault

yaml = YAML(typ="rt")


class Role:
    def __init__(self,
                 role_type: Text,
                 name: Text,
                 data: Optional[Dict] = None):
        self.name = name
        self.role_type = role_type
        if role_type == "util":
            self.template_file = UTIL_TEMPLATE_FILE
            self.preset_path = UTIL_PRESET_PATH
            self.root_key = "actions"
        elif role_type == "oscap":
            self.template_file = OSCAP_TEMPLATE_FILE
            self.preset_path = OSCAP_PRESET_PATH
            self.root_key = "actions"
        else:
            raise NotImplementedError(f"TODO: {role_type}")

        if data is None:
            with open(self.template_file, "r") as f:
                data = yaml.load(f)

        if self.root_key not in data.keys():
            err_msg = f"[!] Invalid {self.role_type} preset file:"
            err_msg += f" missing `{self.root_key}` key"
            raise KeyError(err_msg)

        self.actions = data[self.root_key]

    def is_valid_action(self, action: Text) -> bool:
        return action in self.actions.keys()

    def has_settable_vars(self, arg_action: Text) -> bool:
        action = self.actions[arg_action]
        return "vars" in action.keys() and action["vars"] is not None

    def is_valid_option_key(self, arg_action: Text, option_key: Text) -> bool:
        action_vars = self.actions[arg_action]["vars"]
        return option_key in action_vars.keys()

    def parse_option_val(
        self,
        action: Text,
        option_key: Text,
        option_val: List[Text]
    ) -> Optional[Union[List[Dict], List[Text], Text, Dict, TaggedScalar]]:
        option = self.actions[action]["vars"][option_key]
        valid = option["valid"]
        value_type = option["value_type"]

        if value_type == "single":
            return option_val[0]

        if value_type == "range":
            range_start = option["range_start"]
            range_end = option["range_end"]
            val = option_val[0]
            try:
                val = int(val)  # type: ignore[assignment]
            except ValueError:
                if valid is not None and val in valid:
                    return val
                print("[!] Invalid value, number is expected")
                return None
            if val < range_start:
                print("[!] Supplied value is lower than allowed value")
                print(f"    Min: {range_start}")
                return None
            if range_end is not None and val > range_end:
                print("[!] Supplied value is higher than allowed value")
                print(f"    Max: {range_end}")
                return None
            return option_val[0]

        if value_type == "choice":
            val = option_val[0]
            if val not in valid:
                return None
            return val

        if value_type == "list_choice":
            option_val_s = set(option_val)
            valid_s = set(valid)
            diff = option_val_s - valid_s
            if len(diff) > 0:
                print("[!] Invalid value provided")
                print(f"    {diff}")
                return None
            return list(set(option_val))

        if value_type == "list":
            return list(set(option_val))

        if value_type == "sensitive":
            val = option_val[0]
            return TaggedScalar(value=vault.dump(val), tag="!vault")

        return None

    def list_action_and_details(
        self,
        action: Optional[Text] = None,
        search_query: Optional[Text] = None,
    ) -> List[Tuple[Text, Any]]:
        data: List[Tuple[Text, Text]] = []
        for action_key, task in self.actions.items():
            if search_query is not None:
                if re.search(search_query, task["title"]):
                    data.append((action_key, task))
                continue
            if action is None:
                data.append((action_key, task))
                continue
        return data

    def list_action_w_vars_and_details(self) -> List[Tuple[Text, Any]]:
        data: List[Tuple[Text, Text]] = []
        for action, task in self.actions.items():
            if not self.has_settable_vars(action):
                continue
            data.append((action, task))
        return data

    def save(self, file_name: Optional[Text] = None) -> bool:
        """
        Dump role data into a YAML file
        """
        if file_name is not None:
            if file_name in list_preset(self.role_type):
                print(f"[!] Specified {self.role_type} preset name exists")
                return False

        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(self.preset_path, f"{file_name}.yml"):
            return False

        file_path = self.preset_path.joinpath(f"{file_name}.yml").resolve()

        data = {
            self.root_key: self.actions
        }

        with open(file_path, 'w') as f:
            yaml.dump(data, f)

        return True

    def delete(self) -> None:
        file_path = self.preset_path.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)

    def rename(self, new_name: Text) -> bool:
        if not self.save(new_name):
            return False

        self.delete()
        self.name = new_name
        return True

    @staticmethod
    def load(role_type: Text, name: Text) -> Optional[Role]:
        """
        Load role preset from YAML file to Python object
        """
        role = Role(role_type=role_type, name=name)
        if not is_valid_file_path(role.preset_path, f"{name}.yml"):
            print(f"[!] Invalid {role_type} preset name")
            return None

        if name not in list_preset(role_type):
            print(f"[!] {role_type} preset name not found: {name}")
            return None

        file_path = role.preset_path.joinpath(f"{name}.yml").resolve()
        with open(file_path, "r") as f:
            data: Dict = yaml.load(f)

        if role.root_key not in data.keys():
            err_msg = f"[!] Invalid {role_type} preset file:"
            err_msg += f" missing `{role.root_key}` key"
            print(err_msg)
            return None

        role.actions = data[role.root_key]
        return role

    @staticmethod
    def create(role_type: Text, name: Text) -> Optional[Role]:
        """
        Function wrapper for creating Role object
        """
        if name in list_preset(role_type):
            return None

        role = Role(role_type, name)
        if not is_valid_file_path(role.preset_path, f"{name}.yml"):
            return None

        return role

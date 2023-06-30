from __future__ import annotations

import re
from ruamel.yaml import YAML  # type: ignore[import]
from ruamel.yaml.comments import TaggedScalar  # type: ignore[import]
from typing import Optional, Text, Dict, List, Tuple, Any, Union
from pathlib import Path

from shaa_shell.utils.preset import list_preset
from shaa_shell.utils.path import (
    is_valid_file_path,
    resolve_path,
    UTIL_TEMPLATE_FILE,
    UTIL_PRESET_PATH,
    OSCAP_TEMPLATE_FILE,
    OSCAP_PRESET_PATH,
    SEC_TOOLS_TEMPLATE_FILE,
    SEC_TOOLS_PRESET_PATH,
)
from shaa_shell.utils.vault import vault
from shaa_shell.utils import exception

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
        elif role_type == "sec_tools":
            self.template_file = SEC_TOOLS_TEMPLATE_FILE
            self.preset_path = SEC_TOOLS_PRESET_PATH
            self.root_key = "actions"
        else:
            raise NotImplementedError(f"TODO: {role_type}")

        with self.template_file.open("r") as f:
            template = yaml.load(f)

        if self.root_key not in template.keys():
            err_msg = f"[!] Invalid {self.role_type} preset file:"
            err_msg += f" missing `{self.root_key}` key"
            raise KeyError(err_msg)

        self.actions = template[self.root_key]

        self.conf: Dict[Text, Dict[Text, Any]] = {}
        if data is not None:
            self.conf = data

    def get_enabled(self, action: Text) -> bool:
        enabled = False
        if action not in self.conf.keys():
            return enabled

        conf = self.conf[action]
        if "enabled" not in conf.keys():
            return enabled

        return conf["enabled"]

    def set_enabled(self, action: Text, enabled: bool) -> None:
        if action not in self.conf.keys():
            self.conf[action] = {}

        self.conf[action]["enabled"] = enabled

    def get_var(self, action: Text, var_key: Text) -> Optional[Any]:
        if action not in self.conf.keys():
            return None

        conf = self.conf[action]
        if "vars" not in conf.keys():
            return None

        if var_key not in conf["vars"]:
            return None

        return conf["vars"][var_key]

    def set_var(self, action: Text, var_key: Text, var_val: Any):
        if action not in self.conf.keys():
            self.conf[action] = {}

        if "vars" not in self.conf[action].keys():
            self.conf[action]["vars"] = {}

        self.conf[action]["vars"][var_key] = var_val

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
                raise exception.ValueNotNumber(val)
            if val < range_start:
                raise exception.ValueIsLower(val, range_start)
            if range_end is not None and val > range_end:
                raise exception.ValueIsHigher(val, range_end)
            return option_val[0]

        if value_type == "choice":
            val = option_val[0]
            if val not in valid:
                raise exception.ValueNotInChoice(val, valid)
            return val

        if value_type == "list_choice":
            option_val_s = set(option_val)
            valid_s = set(valid)
            diff = option_val_s - valid_s
            if len(diff) > 0:
                raise exception.ValueNotInChoice(diff, valid)
            return list(set(option_val))

        if value_type == "list":
            return list(set(option_val))

        if value_type == "sensitive":
            val = option_val[0]
            return TaggedScalar(value=vault.dump(val), tag="!vault")

        return None

    def list_action_and_details(
        self,
        search_query: Optional[Text] = None,
    ) -> List[Tuple[Text, Any]]:
        data: List[Tuple[Text, Text]] = []
        for action_key, task in self.actions.items():
            if search_query is not None:
                if re.search(search_query, task["title"]):
                    data.append((action_key, task))
                continue
            data.append((action_key, task))
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
                raise exception.NameExist(f"{self.role_type} preset",
                                          file_name)

        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(self.preset_path, f"{file_name}.yml"):
            raise exception.InvalidName(f"{self.role_type} preset", file_name)

        file_path = self.preset_path.joinpath(f"{file_name}.yml").resolve()

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w') as f:
            yaml.dump(self.conf, f)

        return True

    def delete(self) -> None:
        file_path = self.preset_path.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)

    def rename(self, new_name: Text) -> bool:
        try:
            if not self.save(new_name):
                return False
        except exception.ShaaNameError:
            raise

        self.delete()
        new_name = resolve_path(new_name, self.preset_path)
        self.name = new_name
        return True

    @staticmethod
    def load(role_type: Text, name: Text) -> Optional[Role]:
        """
        Load role preset from YAML file to Python object
        """
        role = Role(role_type=role_type, name=name)
        if not is_valid_file_path(role.preset_path, f"{name}.yml"):
            raise exception.InvalidName(f"{role_type} preset", name)

        if name not in list_preset(role_type):
            raise exception.NameNotFound(f"{role_type} preset", name)

        file_path = role.preset_path.joinpath(f"{name}.yml").resolve()
        with file_path.open("r") as f:
            data: Dict = yaml.load(f)

        role.conf = data
        return role

    @staticmethod
    def create(role_type: Text, name: Text) -> Optional[Role]:
        """
        Function wrapper for creating Role object
        """
        try:
            role = Role(role_type, name)
        except KeyError:
            raise exception.InvalidFile(f"{role_type} preset template",
                                        role.root_key)

        if not is_valid_file_path(role.preset_path, f"{name}.yml"):
            raise exception.InvalidName(f"{role_type} preset", name)

        name = resolve_path(name, role.preset_path)
        role.name = name

        if name in list_preset(role_type):
            raise exception.NameExist(f"{role_type} preset", name)

        return role

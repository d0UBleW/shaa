from __future__ import annotations

import re
from ruamel.yaml import YAML  # type: ignore[import]
from ruamel.yaml.comments import TaggedScalar  # type: ignore[import]
from typing import Optional, Text, Dict, List, Tuple, Any, Union
from pathlib import Path

from shaa_shell.utils.preset import list_preset
from shaa_shell.utils.path import (
    CIS_PRESET_PATH,
    CIS_TEMPLATE_FILE,
    is_valid_file_path,
    resolve_path,
)
from shaa_shell.utils.vault import vault
from shaa_shell.utils import exception

yaml = YAML(typ="rt")


class CIS:
    def __init__(self, name: Text, data: Optional[Dict] = None):
        self.name = name

        with CIS_TEMPLATE_FILE.open("r") as f:
            template = yaml.load(f)

        if "sections" not in template.keys():
            raise KeyError(
                "[!] Invalid CIS preset template file: missing `sections` key"
            )
        self.sections = template["sections"]

        self.conf: Dict[Text, Dict[Text, Any]] = {}
        if data is not None:
            self.conf = data

    def get_enabled(self, section_id: Text) -> bool:
        enabled = False
        if section_id not in self.conf.keys():
            return enabled

        conf = self.conf[section_id]
        if "enabled" not in conf.keys():
            return enabled

        return conf["enabled"]

    def set_enabled(self, section_id: Text, enabled: bool) -> None:
        if section_id not in self.conf.keys():
            self.conf[section_id] = {}

        self.conf[section_id]["enabled"] = enabled

    def get_var(self, section_id: Text, var_key: Text) -> Optional[Any]:
        if section_id not in self.conf.keys():
            return None

        conf = self.conf[section_id]
        if "vars" not in conf.keys():
            return None

        if var_key not in conf["vars"]:
            return None

        return conf["vars"][var_key]

    def set_var(self, section_id: Text, var_key: Text, var_val: Any):
        if section_id not in self.conf.keys():
            self.conf[section_id] = {}

        if "vars" not in self.conf[section_id].keys():
            self.conf[section_id]["vars"] = {}

        self.conf[section_id]["vars"][var_key] = var_val

    @staticmethod
    def is_subsection(parent: Text, child: Text) -> bool:
        while True:
            p_id, _, parent = parent.partition(".")
            c_id, _, child = child.partition(".")
            if p_id != c_id:
                return False
            if parent == "":
                return True

    def is_valid_section_id(self, section_id: Text) -> bool:
        return section_id in self.sections.keys()

    def has_settable_vars(self, section_id: Text) -> bool:
        section = self.sections[section_id]
        return "vars" in section.keys() and section["vars"] is not None

    def is_valid_option_key(self, section_id: Text, option_key: Text) -> bool:
        section_vars = self.sections[section_id]["vars"]
        return option_key in section_vars.keys()

    def parse_option_val(
        self,
        section_id: Text,
        option_key: Text,
        option_val: List[Text]
    ) -> Optional[Union[List[Dict], List[Text], Text, Dict, TaggedScalar]]:
        option = self.sections[section_id]["vars"][option_key]
        valid = option["valid"]
        value_type = option["value_type"]

        if value_type == "single":
            return option_val[0]

        if value_type == "dict":
            if section_id in ["3.3.2", "3.3.3"]:
                dict_data = {}
                idx = 0
                while idx <= len(option_val) // 2:
                    pattern = option_val[idx]
                    hosts = option_val[idx + 1]
                    dict_data[pattern] = [
                        host for host in hosts.split(',') if host != ""]
                    idx += 2
                return dict_data
            return option_val[0]

        if value_type == "list_dict":
            if section_id in ["3.5.1.4", "3.5.2.4"]:
                data = []
                for val in option_val:
                    port, _, proto = val.partition('/')
                    data.append({"port": port, "protocol": proto})
                return data
            return option_val

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

    def list_section(self, section_id: Optional[Text] = None) -> List[Text]:
        return list(self.sections.keys())

    def list_section_and_details(
        self,
        section_id: Optional[Text] = None,
        search_query: Optional[Text] = None
    ) -> List[Tuple[Text, Any]]:
        data: List[Tuple[Text, Text]] = []
        for s_id, section in self.sections.items():
            if search_query is not None:
                if re.search(search_query, section["title"]):
                    data.append((s_id, section))
                continue
            if section_id is None:
                data.append((s_id, section))
                continue
            if CIS.is_subsection(section_id, s_id):
                data.append((s_id, section))
        return data

    def list_section_unit(self,
                          section_id: Optional[Text] = None) -> List[Text]:
        section_units = []
        for s_id in self.sections.keys():
            if self.has_settable_vars(s_id):
                section_units.append(s_id)
        return section_units

    def list_section_unit_and_details(self) -> List[Tuple[Text, Any]]:
        data: List[Tuple[Text, Text]] = []
        for s_id, section in self.sections.items():
            if not self.has_settable_vars(s_id):
                continue
            data.append((s_id, section))
        return data

    def save(self, file_name: Optional[Text] = None) -> bool:
        """
        Dump CIS data into a YAML file
        """
        if file_name is not None and file_name in CIS.list_preset():
            raise exception.NameExist("CIS preset", file_name)

        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(CIS_PRESET_PATH, f"{file_name}.yml"):
            raise exception.InvalidName("CIS preset", file_name)

        file_path = CIS_PRESET_PATH.joinpath(f"{file_name}.yml").resolve()

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w') as f:
            yaml.dump(self.conf, f)

        return True

    def delete(self) -> None:
        file_path = CIS_PRESET_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)

    def rename(self, new_name: Text) -> bool:
        try:
            if not self.save(new_name):
                return False
        except exception.ShaaNameError:
            raise

        self.delete()
        new_name = resolve_path(new_name, CIS_PRESET_PATH)
        self.name = new_name
        return True

    @staticmethod
    def load(name: Text) -> Optional[CIS]:
        """
        Load CIS preset from YAML file to Python object
        """
        if not is_valid_file_path(CIS_PRESET_PATH, f"{name}.yml"):
            raise exception.InvalidName("CIS preset", name)

        if name not in CIS.list_preset():
            raise exception.NameNotFound("CIS preset", name)

        file_path = CIS_PRESET_PATH.joinpath(f"{name}.yml").resolve()
        with file_path.open("r") as f:
            data: Dict = yaml.load(f)

        cis = CIS(name, data)
        return cis

    @staticmethod
    def create(name: Text) -> Optional[CIS]:
        """
        Function wrapper for creating CIS object
        """
        if not is_valid_file_path(CIS_PRESET_PATH, f"{name}.yml"):
            raise exception.InvalidName("CIS preset", name)

        name = resolve_path(name, CIS_PRESET_PATH)

        if name in CIS.list_preset():
            raise exception.NameExist("CIS preset", name)

        try:
            cis = CIS(name)
        except KeyError:
            raise exception.InvalidFile("CIS preset template", "sections")

        return cis

    @staticmethod
    def list_preset(pattern: Text = ".*") -> List[Text]:
        """
        List CIS preset based on given pattern
        """
        return list_preset("cis", pattern)


def main():
    pass


if __name__ == "__main__":
    main()

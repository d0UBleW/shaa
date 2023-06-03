from __future__ import annotations

import re
from ruamel.yaml import YAML  # type: ignore[import]
from typing import Optional, Text, Dict, List, Tuple, Any
from pathlib import Path

from shaa_shell.utils.preset import list_preset
from shaa_shell.utils.path import (
    CIS_PRESET_PATH,
    CIS_TEMPLATE_FILE,
    is_valid_file_path,
)

yaml = YAML(typ="rt")


class CIS:
    def __init__(self, name: Text, data: Optional[Dict] = None):
        self.name = name

        if data is None:
            with open(CIS_TEMPLATE_FILE, "r") as f:
                data = yaml.load(f)

        if "sections" not in data.keys():
            print("[!] Invalid CIS preset file: missing `sections` key")
        self.sections = data["sections"]

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

    def is_valid_option_val(self,
                            section_id: Text,
                            option_key: Text,
                            option_val: List[Text]) -> bool:
        option = self.sections[section_id]["vars"][option_key]
        valid = option["valid"]
        value_type = option["value_type"]
        if value_type == "single":
            return True
        if value_type == "dict":
            return True
        if value_type == "list_dict":
            return True
        if value_type == "range":
            range_start = option["range_start"]
            range_end = option["range_end"]
            val = option_val[0]
            try:
                val = int(val)  # type: ignore[assignment]
            except ValueError:
                print("[!] Invalid value, number is expected")
                return False
            if valid is not None and val in valid:
                return True
            if val < range_start:
                print("[!] Supplied value is lower than allowed value")
                print(f"    Min: {range_start}")
                return False
            if range_end is not None and val > range_end:
                print("[!] Supplied value is higher than allowed value")
                print(f"    Max: {range_end}")
                return False
            return True
        if value_type == "choice":
            val = option_val[0]
            if val not in valid:
                return False
            return True
        if value_type == "list_choice":
            option_val_s = set(option_val)
            valid_s = set(valid)
            diff = option_val_s - valid_s
            if len(diff) > 0:
                print("[!] Invalid value provided")
                print(f"    {diff}")
                return False
        return True

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

    def list_section_unit_and_details(
            self, section_id: Optional[Text] = None) -> List[Text]:
        section_units = []
        for s_id in self.sections.keys():
            if self.has_settable_vars(s_id):
                section_units.append(s_id)
        return section_units

    def save(self, file_name: Optional[Text] = None) -> bool:
        """
        Dump CIS data into a YAML file
        """
        if file_name is not None and file_name in CIS.list_preset():
            print("[!] Specified CIS preset name exists")
            return False

        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(CIS_PRESET_PATH, f"{file_name}.yml"):
            return False

        file_path = CIS_PRESET_PATH.joinpath(f"{file_name}.yml").resolve()

        data = {
            "sections": self.sections
        }

        with open(file_path, 'w') as f:
            yaml.dump(data, f)

        return True

    def delete(self) -> None:
        file_path = CIS_PRESET_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)

    def rename(self, new_name: Text) -> bool:
        if not self.save(new_name):
            return False

        self.delete()
        self.name = new_name
        return True

    @staticmethod
    def load(name: Text) -> Optional[CIS]:
        """
        Load CIS preset from YAML file to Python object
        """
        if not is_valid_file_path(CIS_PRESET_PATH, f"{name}.yml"):
            print("[!] Invalid CIS preset name")
            return None

        if name not in CIS.list_preset():
            print(f"[!] CIS preset name not found: {name}")
            return None

        file_path = CIS_PRESET_PATH.joinpath(f"{name}.yml").resolve()
        with open(file_path, "r") as f:
            data: Dict = yaml.load(f)

        if "sections" not in data.keys():
            print("[!] Invalid CIS preset file: missing `sections` key")
            return None

        cis = CIS(name, data)
        return cis

    @staticmethod
    def create(name: Text) -> Optional[CIS]:
        """
        Function wrapper for creating CIS object
        """
        if name in CIS.list_preset():
            return None

        if not is_valid_file_path(CIS_PRESET_PATH, f"{name}.yml"):
            return None

        cis = CIS(name)
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

#!/usr/bin/env python3

from ruamel.yaml import YAML
from typing import Optional, Text, Dict, List, Tuple
from pathlib import Path
from utils.preset import list_preset

yaml = YAML(typ="rt")
CIS_PRESET_PATH = Path("data/custom/cis/")
cis_data_file_path = "data/template/cis.yml"


class CIS:
    def __init__(self, name: Text, data: Optional[Dict] = None):
        self.name = name

        if data is None:
            with open(cis_data_file_path, "r") as f:
                data = yaml.load(f)

        if "sections" not in data.keys():
            raise Exception("Missing `sections` key")
        self.sections = data["sections"]

    def is_valid_section_id(self, section_id: Text) -> bool:
        return section_id in self.sections.keys()

    def has_settable_vars(self, section_id: Text) -> bool:
        section = self.sections[section_id]
        return "vars" in section.keys() and section["vars"] is not None

    def is_valid_option(self, section_id: Text, option_key: Text) -> bool:
        section_vars = self.sections[section_id]["vars"]
        return option_key in section_vars.keys()

    def list_section(self, section_id: Optional[Text] = None) -> List[Text]:
        return list(self.sections.keys())

    def list_section_and_details(self) -> List[Tuple[Text, Text]]:
        data: List[Tuple[Text, Text]] = []
        for section_id, section in self.sections.items():
            data.append((section_id, section["title"]))
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
        if file_name is None:
            file_name = self.name

        if "/" in file_name:
            return False

        file_path = CIS_PRESET_PATH.joinpath(f"{file_name}.yml").resolve()
        try:
            file_path.relative_to(CIS_PRESET_PATH.resolve())
        except ValueError:
            return False

        data = {
            "sections": self.sections
        }

        with open(file_path, 'w') as f:
            yaml.dump(data, f)

        return True

    @staticmethod
    def load(name: Text) -> Optional["CIS"]:
        """
        Load CIS preset from YAML file to Python object
        """
        file_path = CIS_PRESET_PATH.joinpath(f"{name}.yml").resolve()
        try:
            file_path.relative_to(CIS_PRESET_PATH.resolve())
            with open(file_path, "r") as f:
                data: Dict = yaml.load(f)
        except ValueError:
            print("[!] Invalid CIS preset name")
            return None
        except FileNotFoundError:
            print("[!] CIS preset name not found")
            return None

        cis = CIS(name, data)
        return cis

    @staticmethod
    def create(name: Text) -> Optional["CIS"]:
        """
        Function wrapper for creating CIS object
        """
        if name in list_preset("cis"):
            return None

        file_path = CIS_PRESET_PATH.joinpath(f"{name}.yml").resolve()
        try:
            file_path.relative_to(CIS_PRESET_PATH.resolve())
        except ValueError:
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

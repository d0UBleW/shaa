from __future__ import annotations

from ruamel.yaml import YAML  # type: ignore[import]
from typing import Optional, Text, Dict, List, Tuple, Any
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

    def is_valid_option(self, section_id: Text, option_key: Text) -> bool:
        section_vars = self.sections[section_id]["vars"]
        return option_key in section_vars.keys()

    def list_section(self, section_id: Optional[Text] = None) -> List[Text]:
        return list(self.sections.keys())

    def list_section_and_details(
        self,
        section_id: Optional[Text] = None
    ) -> List[Tuple[Text, Any]]:
        data: List[Tuple[Text, Text]] = []
        for s_id, section in self.sections.items():
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
        if file_name is None:
            file_name = self.name

        if file_name in CIS.list_preset():
            print("[!] Specified CIS preset name exists")
            return False

        if not is_valid_file_path(CIS_PRESET_PATH, f"{file_name}.yml"):
            return False

        file_path = CIS_PRESET_PATH.joinpath(f"{file_name}.yml").resolve()

        data = {
            "sections": self.sections
        }

        with open(file_path, 'w') as f:
            yaml.dump(data, f)

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
            print("[!] CIS preset name not found")
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

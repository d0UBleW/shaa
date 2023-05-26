#!/usr/bin/env python3

from ruamel.yaml import YAML
from typing import Optional, Text, Dict, List
from pathlib import Path

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
            raise Exception(
                f"Missing `sections` key in {cis_data_file_path}"
            )
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

    def list_section_unit(self,
                          section_id: Optional[Text] = None) -> List[Text]:
        section_units = []
        for s_id in self.sections.keys():
            if self.has_settable_vars(s_id):
                section_units.append(s_id)
        return section_units

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

    # def _filter(file_name: Text):
    #     section = section_id
    #     if section is None:
    #         return True
    #     while True:
    #         num, _, section = section.partition(".")
    #         file_num, _, file_name = file_name.partition(".")
    #         if file_num != num:
    #             return False
    #         if section == "":
    #             break
    #     return True
    # return list(filter(_filter, map(lambda file: file.stem, sections)))


def main():
    pass


if __name__ == "__main__":
    main()

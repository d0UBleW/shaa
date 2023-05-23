#!/usr/bin/env python3

from ruamel.yaml import YAML
from typing import Optional, Text

yaml = YAML(typ="rt")
cis_data_file_path = "data/cis.yml"


class CIS:
    def __init__(self):
        with open(cis_data_file_path, "r") as f:
            data = yaml.load(f)
            if "sections" not in data.keys():
                raise Exception(
                    f"Missing `sections` key in {cis_data_file_path}"
                )
            self.sections = data["sections"]
            for section in self.sections.values():
                section["status"] = "enabled"

    def is_valid_section_id(self, section_id: Text) -> bool:
        return section_id in self.sections.keys()

    def list_section(self, section_id: Optional[Text] = None):
        return list(self.sections.keys())

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


cis = CIS()


def main():
    pass


if __name__ == "__main__":
    main()

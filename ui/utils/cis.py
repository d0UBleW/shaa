#!/usr/bin/env python3

from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML(typ="rt")
CIS_ROLE_PATH = Path("../ansible/roles/cis_independent_linux/")
CIS_VARIABLES_PATH = CIS_ROLE_PATH.joinpath("defaults/main")


def main():
    vars = CIS_VARIABLES_PATH.glob("*.yml")
    data = []
    for file in vars:
        if file.stem in list(map(str, range(1, 6))):
            with open(file) as f:
                data.append(yaml.load(f))
    return data


def list_section():
    tasks_path = Path("../ansible/roles/cis_independent_linux/tasks")
    sections = list(tasks_path.rglob("[0-9]*.yml"))
    return list(map(lambda file: file.stem, sections))


if __name__ == "__main__":
    main()

from __future__ import annotations

from typing import List, Text, Dict, Optional
from pathlib import Path
from ruamel.yaml import YAML
import re
from shaa_shell.utils.path import PROFILE_PATH, is_valid_file_path

yaml = YAML(typ="rt")


class Profile:
    def __init__(self, name: Text,
                 inv_name: Optional[Text] = None,
                 presets: Dict[Text, Optional[Text]] = {}):
        self.name: Text = name
        self.inv_name: Optional[Text] = inv_name
        if len(presets.keys()) == 0:
            self.presets: Dict[Text, Optional[Text]] = {
                "cis": None,
                "oscap": None,
                "extra": None,
            }
        else:
            self.presets = presets

    @staticmethod
    def list_profile(pattern: Text = ".*") -> List[Text]:
        files = PROFILE_PATH.glob("*.yml")
        return list(filter(lambda fname: re.match(pattern, fname),
                           [file.stem for file in files]))

    @staticmethod
    def create(name: Text) -> Optional[Profile]:
        if name in Profile.list_profile():
            return None

        if not is_valid_file_path(PROFILE_PATH, f"{name}.yml"):
            return None

        profile = Profile(name)
        return profile

    @staticmethod
    def load(name: Text) -> Optional[Profile]:
        if not is_valid_file_path(PROFILE_PATH, f"{name}.yml"):
            print("[!] Invalid profile name")
            return None

        if name not in Profile.list_profile():
            print("[!] Profile name not found")
            return None

        file_path = PROFILE_PATH.joinpath(f"{name}.yml").resolve()
        with open(file_path, "r") as f:
            data: Dict = yaml.load(f)

        if "inventory" not in data.keys():
            print("[!] Invalid profile file: missing `inventory` key")
            return None

        inv_name = data["inventory"]

        if "presets" not in data.keys():
            print("[!] Invalid profile file: missing `presets` key")
            return None

        presets = data["presets"]

        return Profile(name=name, inv_name=inv_name, presets=presets)

    def save(self, file_name: Optional[Text] = None) -> bool:
        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(PROFILE_PATH, f"{file_name}.yml"):
            return False

        file_path = PROFILE_PATH.joinpath(f"{file_name}.yml").resolve()

        data = {
            "inventory": self.inv_name,
            "presets": self.presets,
        }

        with open(file_path, 'w') as f:
            yaml.dump(data, f)

        return True

    def delete(self) -> None:
        file_path = PROFILE_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)

    def rename(self, new_name: Text) -> bool:
        if not self.save(new_name):
            return False
        old_file_path = PROFILE_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(old_file_path, missing_ok=True)
        self.name = new_name
        return True

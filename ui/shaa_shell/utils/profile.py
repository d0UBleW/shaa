from __future__ import annotations

from typing import List, Text, Dict, Optional
from pathlib import Path
from ruamel.yaml import YAML

from shaa_shell.utils.path import PROFILE_PATH, is_valid_file_path, filter_file
from shaa_shell.utils.preset import PRESETS
from shaa_shell.utils import exception

yaml = YAML(typ="rt")


class Profile:
    def __init__(self, name: Text,
                 inv_name: Optional[Text] = None,
                 presets: Dict[Text, Optional[Text]] = {}):
        self.name: Text = name
        self.inv_name: Optional[Text] = inv_name
        if len(presets.keys()) == 0:
            self.presets: Dict[Text, Optional[Text]] = {}
            for preset in PRESETS:
                self.presets[preset] = None
        else:
            self.presets = presets

    @staticmethod
    def list_profile(pattern: Text = ".*") -> List[Text]:
        return filter_file(PROFILE_PATH, "*.yml", pattern)

    @staticmethod
    def create(name: Text) -> Optional[Profile]:
        """
        Function wrapper to create a profile object
        """
        if name in Profile.list_profile():
            return None

        if name == "_shaa_unnamed_profile":
            raise exception.InvalidName("profile", name,
                                        message="Reserved profile name")

        if not is_valid_file_path(PROFILE_PATH, f"{name}.yml"):
            raise exception.InvalidName("profile", name)

        profile = Profile(name)
        return profile

    @staticmethod
    def load(name: Text) -> Optional[Profile]:
        """
        Load profile YAML file to Python object
        """
        if not is_valid_file_path(PROFILE_PATH, f"{name}.yml"):
            raise exception.InvalidName("profile", name)
            return None

        if name not in Profile.list_profile():
            raise exception.NameNotFound("profile", name)
            return None

        file_path = PROFILE_PATH.joinpath(f"{name}.yml").resolve()
        with file_path.open("r") as f:
            data: Dict = yaml.load(f)

        if "inventory" not in data.keys():
            raise exception.InvalidFile("profile", "inventory")

        inv_name = data["inventory"]

        if "presets" not in data.keys():
            raise exception.InvalidFile("profile", "presets")

        presets = data["presets"]

        return Profile(name=name, inv_name=inv_name, presets=presets)

    def save(self, file_name: Optional[Text] = None) -> bool:
        """
        Save Python object to YAML file
        """
        if file_name is not None and file_name in Profile.list_profile():
            raise exception.NameExist("profile", file_name)

        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(PROFILE_PATH, f"{file_name}.yml"):
            raise exception.InvalidName("profile", file_name)

        file_path = PROFILE_PATH.joinpath(f"{file_name}.yml").resolve()

        data = {
            "inventory": self.inv_name,
            "presets": self.presets,
        }

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w') as f:
            yaml.dump(data, f)

        return True

    def delete(self) -> None:
        """
        Delete profile
        """
        file_path = PROFILE_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)

    def rename(self, new_name: Text) -> bool:
        """
        Edit profile name
        """
        try:
            if not self.save(new_name):
                return False
        except exception.ShaaNameError:
            raise
        old_file_path = PROFILE_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(old_file_path, missing_ok=True)
        self.name = new_name
        return True

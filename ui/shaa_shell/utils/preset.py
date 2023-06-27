from __future__ import annotations

from typing import Text, List
from shaa_shell.utils import path

PRESETS: List[Text] = ["cis", "oscap", "wazuh_agent", "util"]


def list_preset(_type: Text, pattern: Text = ".*") -> List[Text]:
    preset_path = None
    if _type == "cis":
        preset_path = path.CIS_PRESET_PATH
    elif _type == "oscap":
        preset_path = path.OSCAP_PRESET_PATH
    elif _type == "util":
        preset_path = path.UTIL_PRESET_PATH
    else:
        raise ValueError(f"preset type `{_type}` does not exist")

    return path.filter_file(preset_path, "*.yml", pattern)

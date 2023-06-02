#!/usr/bin/env python3

import re
from typing import Text, List
from shaa_shell.utils import path


def list_preset(_type: Text, pattern: Text = ".*") -> List[Text]:
    preset_path = None
    if _type == "cis":
        preset_path = path.CIS_PRESET_PATH
    elif _type == "oscap":
        preset_path = path.OSCAP_PRESET_PATH
    elif _type == "extra":
        preset_path = path.EXTRA_PRESET_PATH
    else:
        raise ValueError(f"preset type `{_type}` does not exist")

    files = preset_path.glob("*.yml")
    return list(filter(lambda fname: re.match(pattern, fname),
                       [file.stem for file in files]))

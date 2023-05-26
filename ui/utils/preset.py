#!/usr/bin/env python3

import re
from pathlib import Path
from typing import Text, List


def list_preset(_type: Text, pattern: Text = ".*") -> List[Text]:
    CIS_PRESET_PATH = Path(f"data/custom/{_type}")
    files = CIS_PRESET_PATH.glob("*.yml")
    return list(filter(lambda fname: re.match(pattern, fname),
                       [file.stem for file in files]))

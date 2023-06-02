#!/usr/bin/env python3

import re
from pathlib import Path
from typing import Text, List


def list_preset(_type: Text, pattern: Text = ".*") -> List[Text]:
    PRESET_PATH = Path(f"shaa_shell/data/custom/{_type}")
    files = PRESET_PATH.glob("*.yml")
    return list(filter(lambda fname: re.match(pattern, fname),
                       [file.stem for file in files]))

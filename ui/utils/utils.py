#!/usr/bin/env python3

from typing import Text, List


def completion_filter(substr: Text, tokens: List[Text]):
    return list(filter(lambda s: s.startswith(substr), tokens))

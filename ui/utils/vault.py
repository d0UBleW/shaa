#!/usr/bin/env python3

from ansible_vault import Vault  # type: ignore[import]
import os

try:
    vault_password = os.environ["VAULT_PASSWORD"]
except KeyError:
    print("Missing ansible vault password!")
    print("Please set an environment variable named VAULT_PASSWORD")
    exit(1)

vault = Vault(vault_password)

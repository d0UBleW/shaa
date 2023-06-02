#!/usr/bin/env python3

from ansible_vault import Vault  # type: ignore[import]
from dotenv import dotenv_values  # type: ignore[import]

try:
    vault_password = dotenv_values(".env")["VAULT_PASSWORD"]
except KeyError:
    print("Missing ansible vault password!")
    print("Please set an environment variable named VAULT_PASSWORD via .env file")  # noqa: E501
    exit(1)

vault = Vault(vault_password)

from __future__ import annotations

from ansible_vault import Vault  # type: ignore[import]
from dotenv import dotenv_values  # type: ignore[import]
from shaa_shell.utils.path import ROOT_PATH

try:
    vault_password = dotenv_values(f"{ROOT_PATH}/.env")["VAULT_PASSWORD"]
except KeyError:
    print("Missing ansible vault password!")
    print("Please set an environment variable named VAULT_PASSWORD via .env file")  # noqa: E501
    exit(1)

vault = Vault(vault_password)

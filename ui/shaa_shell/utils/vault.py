from __future__ import annotations

from ansible_vault import Vault  # type: ignore[import]
from dotenv import dotenv_values  # type: ignore[import]
from shaa_shell.utils.path import USER_DATA_PATH
import os

VAR_NAME = "VAULT_PASSWORD"
dotenv_file = USER_DATA_PATH.joinpath(".env")

if dotenv_file.is_file():
    envs = dotenv_values(dotenv_file)
else:
    envs = os.environ  # type: ignore[assignment]

if VAR_NAME not in envs.keys():
    print("[!] Missing ansible vault password!")
    print("[!] Please set an environment variable named VAULT_PASSWORD")
    print(f"[!] This could be done by exporting or via {dotenv_file} file")
    exit(1)

vault_password = envs[VAR_NAME]

vault = Vault(vault_password)

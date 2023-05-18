#!/usr/bin/env python3

import os
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import TaggedScalar
from ansible_vault import Vault
from typing import List, Text, Optional, Dict, Self
from dataclasses import dataclass, field

yaml = YAML(typ="rt")
vault_password = os.environ["VAULT_PASSWORD"]
vault = Vault(vault_password)

INVENTORY_PATH = Path("../ansible/inventory/")


@dataclass(order=True)
class InventoryNode:
    name: Text
    ip_address: Text
    user: Text
    password: Text
    host_vars: Dict = field(default_factory=dict)

    def raw(self) -> Dict:
        data = dict()
        data['ansible_host'] = self.ip_address
        data['ansible_user'] = self.user
        data['ansible_password'] = TaggedScalar(
            value=vault.dump(self.password), tag="!vault")
        data.update(self.host_vars)
        return data

    @staticmethod
    def from_dict(name: Text, data: Dict) -> Optional[Self]:
        try:
            n_ip = data.pop("ansible_host")
            n_user = data.pop("ansible_user")
            n_password = vault.load(data.pop("ansible_password"))
            n_host_vars = data
            node = InventoryNode(
                name=name,
                ip_address=n_ip,
                user=n_user,
                password=n_password,
                host_vars=n_host_vars)
            return node
        except KeyError as ex:
            print(f"[{name}] Key not found: {ex}")
            return None


@dataclass(order=True)
class InventoryGroup:
    name: Text
    nodes: List[InventoryNode] = field(default_factory=list)

    def add_node(self, node: Optional[InventoryNode]) -> None:
        if node:
            self.nodes.append(node)

    def raw(self) -> Dict:
        data: Dict = {
            "hosts": {}
        }

        for node in self.nodes:
            data["hosts"][node.name] = node.raw()

        return data

    @staticmethod
    def from_dict(name: Text, data: Dict) -> Optional[Self]:
        group = InventoryGroup(name=name)
        for node_name, raw_node in data["hosts"].items():
            node = InventoryNode.from_dict(node_name, raw_node)
            group.add_node(node)
        if len(group.nodes) > 0:
            return group
        return None


@dataclass(order=True)
class Inventory:
    name: Text
    default_group: InventoryGroup = field(
        default_factory=lambda: InventoryGroup("_ungrouped"))
    groups: List[InventoryGroup] = field(default_factory=list)

    def add_group(self, group: Optional[InventoryGroup]) -> None:
        if group is None:
            return
        self.groups.append(group)

    def add_node(
            self,
            node: Optional[InventoryNode],
            group_name: Optional[Text] = None) -> None:
        if node is None:
            return

        if group_name is None:
            self.default_group.add_node(node)
            return

        for group in self.groups:
            if group.name == group_name:
                group.add_node(node)
                return
        else:
            group = InventoryGroup(group_name, [node])
            self.groups.append(group)

    def save(self) -> None:
        data: Dict = {
            "all": {
                "hosts": {}
            }
        }

        for node in self.default_group.nodes:
            data["all"]["hosts"][node.name] = node.raw()

        if len(self.groups) > 0:
            data["all"]["children"] = {}
            for group in self.groups:
                data["all"]["children"][group.name] = group.raw()

        with open(f"{INVENTORY_PATH}/{self.name}.yml", "w") as f:
            yaml.dump(data, f)

    @staticmethod
    def load(name: Text) -> Optional[Self]:
        file_path = INVENTORY_PATH.joinpath(f"{name}.yml").resolve()
        try:
            file_path.relative_to(INVENTORY_PATH.resolve())
            with open(file_path, "r") as f:
                data: Dict = yaml.load(f)
        except ValueError:
            print("[!] Invalid inventory name")
            return None
        except FileNotFoundError:
            print("[!] Inventory name not found")
            return None

        inv = Inventory(name)

        if "all" not in data.keys():
            raise Exception("utils/inventory.py: invalid inventory file")
            return

        # Ungrouped nodes
        if "hosts" in data["all"].keys():
            for node_name, raw_node in data["all"]["hosts"].items():
                node = InventoryNode.from_dict(node_name, raw_node)
                inv.add_node(node)

        # Grouped nodes
        if "children" in data["all"].keys():
            for group_name, raw_group in data["all"]["children"].items():
                group = InventoryGroup.from_dict(
                    name=group_name, data=raw_group)
                inv.add_group(group)

        if len(inv.groups) == 0 or len(inv.default_group.nodes) == 0:
            return None

        return inv


def list_inventory() -> List:
    files = INVENTORY_PATH.glob("*.yml")
    return [file.stem for file in files]


if __name__ == "__main__":
    alma = InventoryNode("alma", "192.168.56.211", "vagrant", "vagrant")
    alma.host_vars = {"selinuxtype": "mls"}
    ubuntu = InventoryNode("ubuntu", "192.168.56.212", "vagrant", "vagrant")
    opensuse = InventoryNode(
        "opensuse",
        "192.168.56.213",
        "vagrant",
        "vagrant")
    alma9 = InventoryNode("alma9", "192.168.56.214", "vagrant", "vagrant")
    alma9.host_vars = {"selinuxtype": "mls"}
    alma8 = InventoryNode("alma8", "192.168.56.215", "vagrant", "vagrant")
    alma8.host_vars = {"selinuxtype": "mls"}

    testing = InventoryGroup("testing", [alma])

    inv = Inventory("main_inventory")
    inv.add_group(testing)
    inv.add_node(ubuntu, "testing")
    inv.add_node(opensuse, "testing")
    inv.add_node(alma9)
    inv.add_node(alma8)
    inv.save()

    new_inv = Inventory.load("main_inventory")
    if new_inv is None:
        quit(1)

    new_inv.name = "test_inv"
    new_inv.save()
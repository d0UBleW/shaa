#!/usr/bin/env python3

from ansible_vault import Vault
from dataclasses import dataclass, field
from itertools import product
import os
from pathlib import Path
import re
from ruamel.yaml import YAML
from ruamel.yaml.comments import TaggedScalar
from typing import List, Text, Optional, Dict, Tuple

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
    def from_dict(name: Text, data: Dict) -> Optional["InventoryNode"]:
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
    nodes: Dict[Text, InventoryNode] = field(default_factory=dict)

    def add_node(self, node: Optional[InventoryNode]) -> int:
        if node and node.name not in self.nodes.keys():
            self.nodes[node.name] = node
            return 0

        return -1

    def raw(self) -> Dict:
        data: Dict = {
            "hosts": {}
        }

        for node in self.nodes.values():
            data["hosts"][node.name] = node.raw()

        return data

    @staticmethod
    def from_dict(name: Text, data: Dict) -> Optional["InventoryGroup"]:
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
    groups: Dict[Text, InventoryGroup] = field(
        default_factory=lambda: {"ungrouped": InventoryGroup("ungrouped")}
    )

    def add_group(self, group: Optional[InventoryGroup]) -> int:
        if group and group.name not in self.groups.keys():
            self.groups[group.name] = group
            return 0
        return -1

    def add_node(self,
                 node: Optional[InventoryNode],
                 group_name: Text = "ungrouped") -> int:
        if node is None:
            return -1

        if group_name in self.groups.keys():
            return self.groups[group_name].add_node(node)

        else:
            group = InventoryGroup(group_name)
            self.groups[group_name] = group
            return group.add_node(node)

    def delete_node(self,
                    node_name: Text,
                    group_name: Text = "ungrouped") -> int:
        nodes = self.groups[group_name].nodes
        if node_name in nodes.keys():
            nodes.pop(node_name)
            return 0
        return -1

    def list_node(
        self,
        pattern: Text = '.*',
        groups: Optional[List[Text]] = None
    ) -> List[Tuple[InventoryNode, Text]]:

        nodes: List[Tuple[InventoryNode, Text]] = []

        for group in self.groups.values():
            if groups is None or group.name in groups:
                nodes += product(
                    list(filter(lambda node: re.match(pattern, node.name),
                                group.nodes.values())),
                    [group.name]
                )

        return nodes

    def save(self) -> None:
        data: Dict = {
            "all": {
                "hosts": {}
            }
        }

        for node in self.groups["ungrouped"].nodes.values():
            data["all"]["hosts"][node.name] = node.raw()

        if len(self.groups) > 1:
            data["all"]["children"] = {}

        for group in self.groups.values():
            if group.name == "ungrouped":
                continue
            data["all"]["children"][group.name] = group.raw()

        with open(f"{INVENTORY_PATH}/{self.name}.yml", "w") as f:
            yaml.dump(data, f)

    @staticmethod
    def load(name: Text) -> Optional["Inventory"]:
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
            raise Exception("[!] Invalid inventory file: missing `all` key")
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

        if len(inv.groups) == 0 or len(inv.groups["ungrouped"].nodes) == 0:
            return None

        return inv


def list_inventory() -> List:
    files = INVENTORY_PATH.glob("*.yml")
    return [file.stem for file in files]


if __name__ == "__main__":
    INVENTORY_PATH = Path("../../ansible/inventory/")
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

    testing = InventoryGroup("testing")
    testing.add_node(alma)

    inv = Inventory("main_inventory")
    inv.add_group(testing)
    inv.add_node(ubuntu, "testing")
    inv.add_node(opensuse, "testing")
    inv.add_node(alma9)
    inv.add_node(alma8)
    inv.add_node(alma9, "web")
    inv.add_node(alma8, "db")
    inv.save()

    new_inv = Inventory.load("main_inventory")
    if new_inv is None:
        quit(1)

    new_inv.name = "test_inv"
    new_inv.save()

#!/usr/bin/env python3

from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
import re
from ruamel.yaml import YAML  # type: ignore[import]
from ruamel.yaml.comments import TaggedScalar  # type: ignore[import]
from typing import List, Text, Optional, Dict, Tuple, Any
from shaa_shell.utils.vault import vault
from ansible.parsing.vault import AnsibleVaultError  # type: ignore[import]
from shaa_shell.utils.path import INVENTORY_PATH, is_valid_file_path

yaml = YAML(typ="rt")


@dataclass(order=True)
class InventoryNode:
    name: Text
    ip_address: Text
    user: Text
    password: Text
    host_vars: Dict[Text, Any] = field(default_factory=dict)

    def set_var(self, key: Text, value: Any) -> None:
        """
        Helper function to set `host_vars`
        """
        self.host_vars[key] = value

    def raw(self) -> Dict[Text, Any]:
        """
        Convert node data into Ansible compatible format
        """
        data = dict()
        data['ansible_host'] = self.ip_address
        data['ansible_user'] = self.user
        data['ansible_password'] = TaggedScalar(  # type: ignore[assignment]
            value=vault.dump(self.password), tag="!vault")
        data.update(self.host_vars)
        return data

    @staticmethod
    def from_dict(name: Text, data: Dict) -> Optional["InventoryNode"]:
        """
        Convert Ansible data into Python object format
        """
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
        except AnsibleVaultError as ex:
            if "no vault secrets were found that could decrypt" in ex.message:
                print("[!] Invalid vault password", end=" ")
                print(f"unable to decrypt node {name}")
            else:
                print(f"AnsibleVaultError: {ex}")
            return None


@dataclass(order=True)
class InventoryGroup:
    name: Text
    nodes: Dict[Text, InventoryNode] = field(default_factory=dict)
    group_vars: Dict[Text, Any] = field(default_factory=dict)

    def set_var(self, key: Text, value: Any) -> None:
        """
        Helper function to set `group_vars`
        """
        if self.name == "ungrouped":
            print("[!] This operation is not valid for `ungrouped`")
            return
        self.group_vars[key] = value

    def add_node(self, node: Optional[InventoryNode]) -> int:
        """
        Add a node object into a group
        """
        if node and node.name not in self.nodes.keys():
            self.nodes[node.name] = node
            return 0

        return -1

    def raw(self) -> Dict:
        """
        Convert group data into Ansible compatible format
        """
        data: Dict = {
            "hosts": None,
        }

        if len(self.nodes) > 0:
            data["hosts"] = {}

        for node in self.nodes.values():
            data["hosts"][node.name] = node.raw()

        if len(self.group_vars) > 0:
            data["vars"] = self.group_vars

        return data

    @staticmethod
    def from_dict(
        name: Text,
        data: Dict[Text, Dict]
    ) -> Optional["InventoryGroup"]:
        """
        Convert Ansible data into Python object format
        """
        group = InventoryGroup(name=name)
        for node_name, raw_node in data["hosts"].items():
            node = InventoryNode.from_dict(node_name, raw_node)
            group.add_node(node)

        if "vars" in data.keys():
            group.group_vars = data["vars"]

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
        """
        Add a group object into an inventory
        """
        if group and group.name not in self.groups.keys():
            self.groups[group.name] = group
            return 0
        return -1

    def delete_group(self, group_name: Text) -> int:
        """
        Delete a group object and its nodes from an inventory
        """
        if group_name not in self.groups.keys():
            return -1
        nodes: List[Text] = []
        for node in self.groups[group_name].nodes.values():
            nodes.append(node.name)

        for node_name in nodes:
            self.delete_node(node_name, group_name)

        if group_name != "ungrouped":
            self.groups.pop(group_name)
        return 0

    def list_group(self, pattern: Text = '.*') -> List[InventoryGroup]:
        """
        Filter group name based on given pattern
        """
        return list(filter(lambda group: re.match(pattern, group.name),
                           self.groups.values()))

    def add_node(self,
                 node: Optional[InventoryNode],
                 group_name: Text = "ungrouped") -> int:
        """
        Add a node object into an inventory within the specified group name
        """
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
        """
        Delete a node object from an inventory
        """
        if group_name not in self.groups.keys():
            return -1

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
        """
        Filter node name based on given pattern and group
        """
        nodes: List[Tuple[InventoryNode, Text]] = []

        for group in self.groups.values():
            if groups is None or group.name in groups:
                nodes += product(
                    list(filter(lambda node: re.match(pattern, node.name),
                                group.nodes.values())),
                    [group.name]
                )

        return nodes

    def save(
            self,
            file_name: Optional[Text] = None,
            inv_path: Path = INVENTORY_PATH) -> bool:
        """
        Dump inventory data into a YAML file which is compatible with Ansible
        inventory format
        """
        if file_name is None:
            file_name = self.name

        if not is_valid_file_path(inv_path, f"{file_name}.yml"):
            return False

        file_path = inv_path.joinpath(f"{file_name}.yml").resolve()

        data: Dict = {
            "all": None
        }

        default_group = self.groups["ungrouped"]

        if len(default_group.nodes) > 0:
            data["all"] = {"hosts": {}}

        for node in default_group.nodes.values():
            data["all"]["hosts"][node.name] = node.raw()

        if len(default_group.group_vars) > 0:
            data["all"]["vars"] = default_group.group_vars

        if len(self.groups) > 1:
            data["all"]["children"] = {}

        for group in self.groups.values():
            if group.name == "ungrouped":
                continue
            data["all"]["children"][group.name] = group.raw()

        with open(file_path, "w") as f:
            yaml.dump(data, f)

        return True

    @staticmethod
    def load(name: Text) -> Optional["Inventory"]:
        """
        Load Ansible inventory from YAML file to Python object
        """
        if not is_valid_file_path(INVENTORY_PATH, f"{name}.yml"):
            print("[!] Invalid inventory name")
            return None

        if name not in Inventory.list_inventory():
            print("[!] Inventory name not found")
            return None

        file_path = INVENTORY_PATH.joinpath(f"{name}.yml").resolve()
        with open(file_path, "r") as f:
            data: Dict = yaml.load(f)

        inv = Inventory(name)

        if "all" not in data.keys():
            print("[!] Invalid inventory file: missing `all` key")
            return None

        if data["all"] is None:
            return inv

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

        if len(inv.groups) == 1 and len(inv.groups["ungrouped"].nodes) == 0:
            return None

        return inv

    @staticmethod
    def list_inventory(pattern: Text = ".*") -> List[Text]:
        """
        List inventory based on given pattern
        """
        files = INVENTORY_PATH.glob("*.yml")
        return list(filter(lambda fname: re.match(pattern, fname),
                           [file.stem for file in files]))

    @staticmethod
    def create_inventory(name: Text) -> Optional["Inventory"]:
        if name in Inventory.list_inventory():
            return None

        if not is_valid_file_path(INVENTORY_PATH, f"{name}.yml"):
            return None

        inv = Inventory(name)
        return inv

    def delete_inventory(self) -> None:
        groups: List[Text] = [group_name for group_name in self.groups.keys()]
        for group in groups:
            self.delete_group(group)

        file_path = INVENTORY_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(file_path, missing_ok=True)
        return

    def rename_inventory(self, new_name: Text) -> bool:
        if not self.save(new_name):
            return False
        old_file_path = INVENTORY_PATH.joinpath(f"{self.name}.yml").resolve()
        Path.unlink(old_file_path, missing_ok=True)
        self.name = new_name
        return True


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

    testing = InventoryGroup("testing")
    testing.add_node(alma)
    testing.group_vars = {"foo": "bar", "nested": {"bar": "foo"}}

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

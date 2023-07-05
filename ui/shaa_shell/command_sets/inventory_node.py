from __future__ import annotations

import argparse
import pprint
import re
from dataclasses import asdict
from typing import Dict, List, Text, Tuple

from cmd2 import (Cmd2ArgumentParser, CommandSet, CompletionError,
                  as_subcommand_to, with_argparser, with_default_category)
from cmd2.table_creator import Column, SimpleTable
from ruamel.yaml.comments import TaggedScalar

from shaa_shell.utils import exception, path
from shaa_shell.utils.inventory import Inventory, InventoryNode
from shaa_shell.utils.parser import inventory_node_parser
from shaa_shell.utils.vault import vault


@with_default_category("inventory node")
class inventory_node_cmd(CommandSet):

    @with_argparser(inventory_node_parser)
    def do_node(self: CommandSet, ns: argparse.Namespace):
        """
        Manage inventory node
        """
        if self._cmd is None:
            return
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help('node')


@with_default_category("inventory node")
class inventory_node_subcmd(CommandSet):
    def _choices_priv_key(self: CommandSet) -> List[Text]:
        if self._cmd is None:
            return []
        key_list = list(path.filter_file(path.SSH_PRIV_KEY_PATH,
                                         "*",
                                         with_ext=True))
        if len(key_list) == 0:
            raise CompletionError('[!] No private key found in search path')
        return key_list

    def _choices_group_name(self: CommandSet) -> List[Text]:
        if self._cmd is None:
            return []
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        return list(inv.groups.keys())

    def _choices_node_name(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        if self._cmd is None:
            return []
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        group = "all"
        if "node_group" in arg_tokens:
            group = arg_tokens["node_group"][0]
        nodes = list(map(lambda n: n[0].name, inv.list_node(groups=[group])))
        return nodes

    def _choices_host_var(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        if self._cmd is None:
            return []
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        group_name = "all"
        if "node_group" in arg_tokens:
            group_name = arg_tokens["node_group"][0]

        node_name = None
        if "node_name" in arg_tokens:
            node_name = arg_tokens["node_name"][0]

        if node_name is None:
            raise CompletionError("[!] Missing node name to be targeted")

        node: InventoryNode = inv.groups[group_name].nodes[node_name]
        return list(node.host_vars.keys())

    rename_parser = Cmd2ArgumentParser()
    rename_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='?',
        default="all",
        metavar='group_name',
        help="""node group name (all is a reserved group name, \
leaving it blank defaults to all)""",
        choices_provider=_choices_group_name,
    )
    rename_parser.add_argument(
        'name',
        metavar="node_name",
        help="node name to be renamed",
        choices_provider=_choices_node_name,
    )
    rename_parser.add_argument(
        'new_name',
        metavar="new_node_name",
        help="new node_name",
    )

    edit_parser = Cmd2ArgumentParser()
    edit_parser.add_argument(
        "node_name",
        choices_provider=_choices_node_name,
        help="node name to be edited",
    )
    edit_parser.add_argument(
        "-g",
        "--group",
        dest="node_group",
        nargs='?',
        default="all",
        metavar='group_name',
        choices_provider=_choices_group_name,
        help="""node group name (all is a reserved group name, \
leaving it blank defaults to all)""",
    )
    edit_parser.add_argument(
        "-i",
        "--ip",
        nargs="?",
        help="node ip address",
    )
    edit_parser.add_argument(
        "-u",
        "--user",
        nargs="?",
        help="node SSH user",
    )
    edit_parser.add_argument(
        "-p",
        "--password",
        nargs="?",
        help="node SSH password, pass empty string to unset the field",
    )
    edit_parser.add_argument(
        "-k",
        "--key",
        nargs="?",
        help="node SSH private key path, pass empty string to unset the field",
        choices_provider=_choices_priv_key,
    )

    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument(
        "node_name",
        help="node name")

    create_parser.add_argument(
        "node_ip",
        help="node ip address")

    create_parser.add_argument(
        "node_user",
        help="node SSH user")

    create_parser.add_argument(
        "-p",
        "--password",
        dest="node_password",
        metavar="node_password",
        nargs="?",
        help="node SSH password")

    create_parser.add_argument(
        '-k',
        '--key',
        dest="node_ssh_priv_key_path",
        metavar="node_ssh_priv_key_path",
        help="node SSH private key path",
        nargs="?",
        choices_provider=_choices_priv_key,
    )

    create_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        default="all",
        metavar='group_name',
        type=str,
        help="""node group name (all is a reserved group name, \
leaving it blank defaults to all)""",
        choices_provider=_choices_group_name,
    )

    list_parser = Cmd2ArgumentParser()
    list_parser.add_argument(
        'pattern',
        nargs='?',
        default='.*',
        help='node name pattern in regex to be searched'
    )
    list_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='*',
        metavar='group_name',
        type=str,
        help="""node group name (all is a reserved group name, \
leaving it blank defaults to all groups)""",
        choices_provider=_choices_group_name,
    )

    info_parser = Cmd2ArgumentParser()
    info_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='?',
        default="all",
        metavar='group_name',
        type=str,
        help="""node group name (all is a reserved group name, \
leaving it blank defaults to all)""",
        choices_provider=_choices_group_name,
    )

    info_parser.add_argument(
        'pattern',
        type=str,
        metavar="pattern",
        help="""node name regex pattern (if the group flag is set, tab \
completion would list out nodes from the specified group, otherwise it would \
just list out all nodes)""",
        choices_provider=_choices_node_name,
    )

    delete_parser = Cmd2ArgumentParser()
    delete_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='?',
        default="all",
        metavar='group_name',
        type=str,
        help="""node group name (all is a reserved group name, \
leaving it blank defaults to all)""",
        choices_provider=_choices_group_name,
    )

    delete_parser.add_argument(
        'name',
        type=str,
        metavar="node_name",
        help="""node name (if group flag is set, tab completion would list \
out nodes from the specified group, otherwise it would just list \
out all nodes)""",
        choices_provider=_choices_node_name,
    )

    unset_parser = Cmd2ArgumentParser()
    unset_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='?',
        default="all",
        metavar='group_name',
        type=str,
        help="""node group name (all is a reserved group name, \
leaving it blank defaults to all)""",
        choices_provider=_choices_group_name,
    )
    unset_parser.add_argument(
        'node_name',
        help='name of target node whose host variable to be unset',
        choices_provider=_choices_node_name,
    )
    unset_parser.add_argument(
        'host_var',
        help="name of host variable to be unset",
        choices_provider=_choices_host_var,
    )

    @as_subcommand_to("node", "rename", rename_parser,
                      help="rename node on current inventory")
    def inv_node_rename(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        if inv.edit_node(node_name=ns.name,
                         new_name=ns.new_name,
                         group_name=ns.node_group) == 0:
            self._cmd.poutput("[+] Node has been renamed successfully")
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]

    @as_subcommand_to("node", "edit", edit_parser,
                      help="edit node on current inventory")
    def inv_node_edit(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        try:
            if inv.edit_node(node_name=ns.node_name,
                             ip=ns.ip,
                             user=ns.user,
                             password=ns.password,
                             ssh_priv_key_path=ns.key,
                             group_name=ns.node_group) == 0:
                self._cmd.poutput("[+] Node has been edited successfully")
                self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
        except exception.ShaaInventoryError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

    @as_subcommand_to("node", "create", create_parser,
                      aliases=["add"],
                      help="create node on current inventory")
    def inv_node_create(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        if ns.node_password is None and ns.node_ssh_priv_key_path is None:
            self._cmd.perror("[!] Missing both password and SSH private key")
            self._cmd.perror("    Please specify either one of them")
            return
        node = InventoryNode(
            name=ns.node_name,
            ip_address=ns.node_ip,
            user=ns.node_user,
            password=ns.node_password,
            ssh_priv_key_path=ns.node_ssh_priv_key_path,
        )
        if inv.add_node(node, ns.node_group) == 0:
            self._cmd.poutput("[+] Node has been created successfully")
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd.perror("[!] Specified node name already exists")
            return

    @as_subcommand_to("node", "delete", delete_parser,
                      aliases=["del", "rm"],
                      help="delete node from current inventory")
    def inv_node_delete(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        if inv.delete_node(ns.name, group_name=ns.node_group) == 0:
            self._cmd.poutput("[+] Node has been deleted successfully")
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd.perror("[!] Specified node name does not exist")

    @as_subcommand_to("node", "list", list_parser,
                      aliases=["ls"],
                      help="list nodes from current inventory")
    def inv_node_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        nodes: List[Tuple[InventoryNode, Text]] = inv.list_node(ns.pattern,
                                                                ns.node_group)
        data_list = []
        for node, group_name in nodes:
            data_list.append([node.name,
                              group_name,
                              f"{node.user}@{node.ip_address}"])

        columns: List[Column] = [
            Column("Name", width=16),
            Column("Group", width=16),
            Column("Connection Info", width=32),
        ]
        st = SimpleTable(columns)
        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to("node", "info", info_parser,
                      help="display node details")
    def inv_node_info(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]

        columns: List[Column] = [
            Column("Key", width=20),
            Column("Value", width=64),
        ]
        st = SimpleTable(columns)

        for node in inv.groups[ns.node_group].nodes.values():
            if re.search(ns.pattern, node.name):
                data_list = list(asdict(node).items())
                for i in range(len(data_list[:-1])):
                    if data_list[i][1] is None:
                        data_list[i] = (data_list[i][0], "")
                # node host vars
                vars = []
                for key, val in data_list[-1][1].items():
                    if isinstance(val, TaggedScalar):
                        val = vault.load(val)
                    val = pprint.pformat(val, sort_dicts=False)
                    vars.append(f"{key}: {val}")
                data_list[-1] = (data_list[-1][0], "\n".join(vars))
                tbl = st.generate_table(data_list,
                                        row_spacing=0,
                                        include_header=False)
                sep = "-" * 16
                self._cmd.poutput(f"\n{sep}\n{tbl}\n{sep}\n")

    @as_subcommand_to("node", "unset", unset_parser,
                      help="unset node host var")
    def inv_node_unset(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore
        if ns.node_group not in inv.groups.keys():
            self._cmd.perror(f"[!] Invalid group name: {ns.node_group}")
            return
        if ns.node_name not in inv.groups[ns.node_group].nodes.keys():
            self._cmd.perror(f"[!] Invalid node name: {ns.node_name}")
            return

        node: InventoryNode = inv.groups[ns.node_group].nodes[ns.node_name]

        if ns.host_var not in node.host_vars.keys():
            self._cmd.perror(f"[!] Invalid host var: {ns.host_var}")
            return
        old_value = node.host_vars[ns.host_var]
        del node.host_vars[ns.host_var]
        if isinstance(old_value, TaggedScalar):
            old_value = vault.load(old_value)

        self._cmd.poutput(f"[+] {ns.host_var}:")
        self._cmd.poutput(f"    old: {old_value}")
        self._cmd._inv_has_changed = True  # type: ignore[attr-defined]

#!/usr/bin/env python3

import argparse
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    with_argparser,
    as_subcommand_to,
)
from cmd2.table_creator import (
    SimpleTable,
    Column,
)
from dataclasses import asdict
import pprint
import re
from typing import List, Text, Tuple, Dict
from utils.inventory import (
    Inventory,
    InventoryNode,
)
from utils.parser import inventory_node_parser


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
        group = "ungrouped"
        if "node_group" in arg_tokens:
            group = arg_tokens["node_group"][0]
        nodes = list(map(lambda n: n[0].name, inv.list_node(groups=[group])))
        return nodes

    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument(
        '-n',
        '--name',
        dest="node_name",
        required=True,
        type=str,
        help='node name')

    create_parser.add_argument(
        '-i',
        '--ip-address',
        dest="node_ip",
        required=True,
        type=str,
        help='node ip address')

    create_parser.add_argument(
        '-u',
        '--user',
        dest="node_user",
        required=True,
        type=str,
        help='node SSH user')

    create_parser.add_argument(
        '-p',
        '--password',
        dest="node_password",
        required=True,
        type=str,
        help='node SSH password')

    create_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        default=["ungrouped"],
        nargs='*',
        metavar='group_name',
        type=str,
        help="""list of node group name (ungrouped is a reserved group name, \
leaving it blank defaults to ungrouped)""",
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
        help="""node group name (ungrouped is a reserved group name, \
leaving it blank defaults to all groups)""",
        choices_provider=_choices_group_name,
    )

    info_parser = Cmd2ArgumentParser()
    info_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='?',
        default="ungrouped",
        metavar='group_name',
        type=str,
        help="""node group name (ungrouped is a reserved group name, \
leaving it blank defaults to ungrouped)""",
        choices_provider=_choices_group_name,
    )

    info_parser.add_argument(
        'pattern',
        type=str,
        metavar="pattern",
        help="""node name regex pattern (if the group flag is set, tab \
completion would list out nodes from the specified group, otherwise it would \
just list out ungrouped nodes)""",
        choices_provider=_choices_node_name,
    )

    delete_parser = Cmd2ArgumentParser()
    delete_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='?',
        default="ungrouped",
        metavar='group_name',
        type=str,
        help="""node group name (ungrouped is a reserved group name, \
leaving it blank defaults to ungrouped)""",
        choices_provider=_choices_group_name,
    )

    delete_parser.add_argument(
        'name',
        type=str,
        metavar="node_name",
        help="""node name (if group flag is set, tab completion would list \
out nodes from the specified group, otherwise it would just list \
out ungrouped nodes)""",
        choices_provider=_choices_node_name,
    )

    @as_subcommand_to("node", "create", create_parser,
                      aliases=["add"],
                      help="create node on current inventory")
    def inv_node_create(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        node = InventoryNode(
            name=ns.node_name,
            ip_address=ns.node_ip,
            user=ns.node_user,
            password=ns.node_password,
        )
        for group in ns.node_group:
            if inv.add_node(node, group) == 0:
                self._cmd.poutput("[+] Node has been created successfully")
                self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
            else:
                self._cmd.poutput("[!] Specified node name already existed")

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
            self._cmd.poutput("[!] Specified node name does not exist")

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
            Column("Key", width=16),
            Column("Value", width=64),
        ]
        st = SimpleTable(columns)

        for node in inv.groups[ns.node_group].nodes.values():
            if re.match(ns.pattern, node.name):
                data_list = list(asdict(node).items())
                data_list[-1] = (data_list[-1][0],
                                 pprint.pformat(dict(data_list[-1][-1]),
                                                sort_dicts=False))
                tbl = st.generate_table(data_list, row_spacing=0)
                self._cmd.poutput(f"\n{tbl}\n")

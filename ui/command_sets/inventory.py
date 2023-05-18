#!/usr/bin/env python3

import argparse
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    with_argparser,
    as_subcommand_to,
)
from cmd2.table_creator import BorderedTable, Column
from cmd2.exceptions import CommandSetRegistrationError
from dataclasses import asdict
import pprint
import re
from typing import List, Any, Text, Tuple, Dict
from utils.inventory import list_inventory, Inventory, InventoryNode
from utils.parser import inventory_node_parser


@with_default_category("inventory")
class inventory_subcmd(CommandSet):
    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument('name', help='name of inventory')

    delete_parser = Cmd2ArgumentParser()
    delete_parser.add_argument('name', choices=list_inventory(),
                               help='name of inventory')

    list_parser = Cmd2ArgumentParser()
    list_parser.add_argument('pattern', nargs='?', default='.*',
                             help='name pattern in regex to be searched')

    load_parser = Cmd2ArgumentParser()
    load_parser.add_argument('name', choices=list_inventory(),
                             help='name of inventory')

    unload_parser = Cmd2ArgumentParser()

    @as_subcommand_to('inventory', 'create', create_parser,
                      help='create inventory')
    def inventory_create(self, ns: argparse.Namespace):
        self._cmd.poutput(f"Create inventory: {ns.name}")

    @as_subcommand_to('inventory', 'delete', delete_parser,
                      help='delete inventory')
    def inventory_delete(self, ns: argparse.Namespace):
        self._cmd.poutput(f"Delete inventory: {ns.name}")

    @as_subcommand_to('inventory', 'list', list_parser, help='list inventory')
    def inventory_list(self, ns: argparse.Namespace):
        data_list: List[List[Any]] = list()

        max_width = 0
        for inv in list_inventory():
            if re.match(ns.pattern, inv):
                if max_width < len(inv):
                    max_width = len(inv)
                data_list.append([inv])

        columns: List[Column] = list()
        columns.append(Column("Name", width=max_width))
        bt = BorderedTable(columns)
        tbl = bt.generate_table(data_list)
        self._cmd.poutput(f"{tbl}\n")

    @as_subcommand_to('inventory', 'load', load_parser, help='load inventory')
    def inventory_load(self, ns: argparse.Namespace):
        inv = Inventory.load(ns.name)
        self._cmd._inventory = inv
        try:
            self._cmd.register_command_set(self._cmd._inventory_node_cmd)
            self._cmd.register_command_set(self._cmd._inventory_node_subcmd)
            self._cmd.poutput("[*] inventory node module loaded")
            self._cmd.poutput("[*] check `help node` for usage information")
        except CommandSetRegistrationError:
            pass

    @as_subcommand_to('inventory', 'unload', unload_parser,
                      help='unload inventory')
    def inventory_unload(self, _):
        self._cmd._inventory = None
        self._cmd.unregister_command_set(self._cmd._inventory_node_subcmd)
        self._cmd.unregister_command_set(self._cmd._inventory_node_cmd)
        self._cmd.poutput("[*] inventory node module unloaded")


@with_default_category("inventory node")
class inventory_node_cmd(CommandSet):

    @with_argparser(inventory_node_parser)
    def do_node(self, ns: argparse.Namespace):
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help('node')


@with_default_category("inventory node")
class inventory_node_subcmd(CommandSet):
    def _choices_group_name(self) -> List[Text]:
        inv: Inventory = self._cmd._inventory
        return list(inv.groups.keys())

    def _choices_node_name(
        self,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:

        inv: Inventory = self._cmd._inventory
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
        help="""node group name (ungrouped is a reserved group name, \
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
        'name',
        type=str,
        metavar="node_name",
        help="""node name (if group flag is set, tab completion would list \
out nodes from the specified group, otherwise it would just list \
out ungrouped nodes)""",
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

    @as_subcommand_to("node", "create", create_parser)
    def inv_node_create(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        node = InventoryNode(
            name=ns.node_name,
            ip_address=ns.node_ip,
            user=ns.node_user,
            password=ns.node_password,
        )
        for group in ns.node_group:
            if inv.add_node(node, group) == 0:
                self._cmd.poutput("[+] Node has been created successfully")
            else:
                self._cmd.poutput("[!] Specified node name already existed")
                self._cmd.poutput("[!] Creation aborted!")

    @as_subcommand_to("node", "delete", delete_parser)
    def inv_node_delete(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        if inv.delete_node(ns.name, group_name=ns.node_group) == 0:
            self._cmd.poutput("[+] Node has been deleted successfully")
        else:
            self._cmd.poutput("[!] Specified node name does not exist")

    @as_subcommand_to("node", "list", list_parser)
    def inv_node_list(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        nodes: List[Tuple[InventoryNode, Text]] = inv.list_node(ns.pattern,
                                                                ns.node_group)
        data_list = []
        for node, group_name in nodes:
            data_list.append([node.name, group_name, node.ip_address])

        columns: List[Column] = [
            Column("Name", width=16),
            Column("Group", width=16),
            Column("IP Address", width=16),
        ]
        bt = BorderedTable(columns)
        tbl = bt.generate_table(data_list)
        self._cmd.poutput(f"{tbl}\n")

    @as_subcommand_to("node", "info", info_parser)
    def inv_node_info(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        node = inv.groups[ns.node_group].nodes[ns.name]
        data_list = list(asdict(node).items())
        data_list[-1] = (data_list[-1][0],
                         pprint.pformat(dict(data_list[-1][-1]),
                                        sort_dicts=False))

        columns: List[Column] = [
            Column("Key", width=16),
            Column("Value", width=64),
        ]

        bt = BorderedTable(columns)
        tbl = bt.generate_table(data_list)
        self._cmd.poutput(f"{tbl}\n")

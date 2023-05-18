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
import re
from typing import List, Any
from utils.inventory import list_inventory, Inventory
from utils.parser import inventory_node_parser
from utils.utils import completion_filter


@with_default_category("inventory")
class inventory_subcmd(CommandSet):
    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument('name', help='name of inventory')

    delete_parser = Cmd2ArgumentParser()
    delete_parser.add_argument('name', choices=list_inventory(),
                               help='name of inventory')

    list_parser = Cmd2ArgumentParser()
    list_parser.add_argument('pattern', nargs='?', default='.*',
                             help='name pattern in regex to search for')

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
    def _complete_group_name(self, text, line, begidx, endidx):
        inv: Inventory = self._cmd._inventory
        groups = []
        for group in inv.groups:
            groups.append(group.name)
        return completion_filter(text, groups)

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
        help='node user')

    create_parser.add_argument(
        '-p',
        '--password',
        dest="node_password",
        required=True,
        type=str,
        help='node password')

    create_parser.add_argument(
        '-g',
        '--group',
        dest="node_group",
        nargs='*',
        metavar='group_name',
        type=str,
        help='node group name',
        completer=_complete_group_name,
    )

    list_parser = Cmd2ArgumentParser()

    @as_subcommand_to("node", "create", create_parser)
    def inv_node_create(self, ns: argparse.Namespace):
        self._cmd.poutput("Node create: TODO")
        self._cmd.poutput(ns.node_name)
        self._cmd.poutput(ns.node_group)

    @as_subcommand_to("node", "list", list_parser)
    def inv_node_list(self, ns: argparse.Namespace):
        self._cmd.poutput("Node list: TODO")

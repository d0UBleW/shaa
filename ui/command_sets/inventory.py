#!/usr/bin/env python3

import argparse
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
)
from cmd2.table_creator import (
    SimpleTable as BorderedTable,
    Column,
)
from cmd2.exceptions import CommandSetRegistrationError
from typing import List
from utils.inventory import (
    list_inventory,
    Inventory,
)


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
        data_list = []

        for inv in list_inventory(ns.pattern):
            data_list.append([inv])

        columns: List[Column] = list()
        columns.append(Column("Name", width=64))
        bt = BorderedTable(columns)
        tbl = bt.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to('inventory', 'load', load_parser, help='load inventory')
    def inventory_load(self, ns: argparse.Namespace):
        inv = Inventory.load(ns.name)
        self._cmd._inventory = inv
        try:
            self._cmd.register_command_set(self._cmd._inventory_node_cmd)
            self._cmd.register_command_set(self._cmd._inventory_node_subcmd)
            self._cmd.register_command_set(self._cmd._inventory_group_cmd)
            self._cmd.register_command_set(self._cmd._inventory_group_subcmd)
            self._cmd.poutput("[*] inventory node and group modules loaded")
            self._cmd.poutput(
                "[*] check `help (node|group)` for usage information")
        except CommandSetRegistrationError:
            pass

    @as_subcommand_to('inventory', 'unload', unload_parser,
                      help='unload inventory')
    def inventory_unload(self, _):
        self._cmd._inventory = None
        self._cmd.unregister_command_set(self._cmd._inventory_node_subcmd)
        self._cmd.unregister_command_set(self._cmd._inventory_node_cmd)
        self._cmd.unregister_command_set(self._cmd._inventory_group_subcmd)
        self._cmd.unregister_command_set(self._cmd._inventory_group_cmd)
        self._cmd.poutput("[*] inventory node and group modules unloaded")

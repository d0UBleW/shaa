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
from typing import List, Text, Optional
from utils.inventory import Inventory


@with_default_category("inventory")
class inventory_subcmd(CommandSet):
    def _choices_inventory_name(self) -> List[Text]:
        return Inventory.list_inventory()

    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument('name', help='name of inventory')

    delete_parser = Cmd2ArgumentParser()

    list_parser = Cmd2ArgumentParser()
    list_parser.add_argument('pattern', nargs='?', default='.*',
                             help='name pattern in regex to be searched')

    load_parser = Cmd2ArgumentParser()
    load_parser.add_argument('name',
                             choices_provider=_choices_inventory_name,
                             help='name of inventory')

    unload_parser = Cmd2ArgumentParser()

    save_parser = Cmd2ArgumentParser()

    rename_parser = Cmd2ArgumentParser()
    rename_parser.add_argument('name',
                               help='new name of inventory')

    duplicate_parser = Cmd2ArgumentParser()
    duplicate_parser.add_argument('name',
                                  help='new name of duplicated inventory')

    @as_subcommand_to('inventory', 'create', create_parser,
                      help='create inventory')
    def inventory_create(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv = Inventory.create_inventory(ns.name)
        if inv is None:
            warning_text = "[!] Invalid name or specified inventory name"
            warning_text += "already existed"
            self._cmd.poutput(warning_text)
            return
        if self._cmd._inventory is None:
            self._cmd._inventory = inv
            return self.inventory_load(None, True)

    @as_subcommand_to('inventory', 'delete', delete_parser,
                      help='delete inventory')
    def inventory_delete(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            self._cmd.poutput("[!] Currently, there is no inventory loaded")
            return
        warning_text = "[!] Deleting this inventory would also delete all of "
        warning_text += "its corresponding groups and nodes"
        self._cmd.poutput(warning_text)
        if (_ := self._cmd.read_input(
                "[+] Do you want to proceed [y/N]? ")) != "y":
            self._cmd.poutput("[!] Deletion aborted")
            return
        inv.delete_inventory()
        self._cmd.poutput("[+] Inventory has been deleted successfully")
        self._cmd._inventory = None  # type: ignore[attr-defined]

    @as_subcommand_to('inventory', 'list', list_parser, help='list inventory')
    def inventory_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        data_list = []

        for inv in Inventory.list_inventory(ns.pattern):
            data_list.append([inv])

        columns: List[Column] = list()
        columns.append(Column("Name", width=32))
        bt = BorderedTable(columns)
        tbl = bt.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to('inventory', 'load', load_parser, help='load inventory')
    def inventory_load(self: CommandSet, ns: argparse.Namespace,
                       empty: bool = False):
        if self._cmd is None:
            return
        self._cmd.check_if_inv_changed()  # type: ignore[attr-defined]
        if not empty:
            inv = Inventory.load(ns.name)
            self._cmd._inventory = inv  # type: ignore[attr-defined]

        try:
            self._cmd.register_command_set(
                self._cmd._inventory_node_cmd  # type: ignore[attr-defined]
            )
            self._cmd.register_command_set(
                self._cmd._inventory_node_subcmd  # type: ignore[attr-defined]
            )
            self._cmd.register_command_set(
                self._cmd._inventory_group_cmd  # type: ignore[attr-defined]
            )
            self._cmd.register_command_set(
                self._cmd._inventory_group_subcmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] inventory node and group modules loaded")
            self._cmd.poutput(
                "[*] check `help (node|group)` for usage information")
        except CommandSetRegistrationError:
            pass

    @as_subcommand_to('inventory', 'unload', unload_parser,
                      help='unload inventory')
    def inventory_unload(self: CommandSet, _):
        if self._cmd is None:
            return
        self._cmd.check_if_inv_changed()  # type: ignore[attr-defined]
        self._cmd._inventory = None  # type: ignore[attr-defined]
        self._cmd.unregister_command_set(
            self._cmd._inventory_node_subcmd)  # type: ignore[attr-defined]
        self._cmd.unregister_command_set(
            self._cmd._inventory_node_cmd)  # type: ignore[attr-defined]
        self._cmd.unregister_command_set(
            self._cmd._inventory_group_subcmd)  # type: ignore[attr-defined]
        self._cmd.unregister_command_set(
            self._cmd._inventory_group_cmd)  # type: ignore[attr-defined]
        self._cmd.poutput("[*] inventory node and group modules unloaded")

    @as_subcommand_to('inventory', 'save', save_parser,
                      help='save inventory data')
    def inventory_save(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            self._cmd.poutput("[!] Currently, there is no inventory loaded")
            return
        if not inv.save():
            self._cmd.poutput("[!] Invalid inventory name")
            return
        self._cmd._inv_has_changed = False  # type: ignore[attr-defined]
        self._cmd.poutput("[+] inventory has been saved")

    @as_subcommand_to('inventory', 'rename', rename_parser)
    def inventory_rename(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            self._cmd.poutput("[!] Currently, there is no inventory loaded")
            return
        old_name = inv.name
        if not inv.rename_inventory(ns.name):
            self._cmd.poutput("[!] Invalid inventory name")
            return
        self._cmd.poutput("[+] inventory has been renamed")
        self._cmd.poutput(f"[*] old: {old_name}")
        self._cmd.poutput(f"[*] new: {inv.name}")

    @as_subcommand_to('inventory', 'duplicate', duplicate_parser)
    def inventory_duplicate(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            self._cmd.poutput("[!] Currently, there is no inventory loaded")
            return
        status, msg = inv.duplicate_inventory(ns.name)
        if not status:
            self._cmd.poutput(f"[!] {msg}")
            return
        self._cmd.poutput("[+] inventory has been duplicated")

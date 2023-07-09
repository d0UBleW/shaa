from __future__ import annotations

import argparse
from typing import List, Optional, Text

from cmd2 import (Cmd2ArgumentParser, CommandSet, as_subcommand_to,
                  with_default_category)
from cmd2.exceptions import CommandSetRegistrationError
from cmd2.table_creator import Column, SimpleTable

from shaa_shell.utils import exception
from shaa_shell.utils.inventory import Inventory
from shaa_shell.utils.profile import Profile


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
    save_parser.add_argument("name",
                             nargs="?",
                             help="(save as) name of inventory")

    rename_parser = Cmd2ArgumentParser()
    rename_parser.add_argument('name',
                               help='new name of inventory')

    @as_subcommand_to('inventory', 'create', create_parser,
                      aliases=["add"],
                      help='create inventory')
    def inventory_create(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.check_if_inv_changed()  # type: ignore[attr-defined]
        try:
            inv = Inventory.create_inventory(ns.name)
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._inv_has_changed = False  # type: ignore[attr-defined]
        self._cmd._inventory = inv  # type: ignore[attr-defined]
        return self.inventory_load(None, inv)  # type: ignore[attr-defined]

    @as_subcommand_to('inventory', 'delete', delete_parser,
                      aliases=["del", "rm"],
                      help='delete current inventory')
    def inventory_delete(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            self._cmd.perror("[!] Currently, there is no inventory loaded")
            return
        warning_text = "[!] Deleting this inventory would also delete all of "
        warning_text += "its corresponding groups and nodes"
        self._cmd.perror(warning_text)
        if (_ := self._cmd.read_input(
                "[+] Do you want to proceed [y/N]? ")) != "y":
            self._cmd.perror("[!] Deletion aborted")
            return
        inv.delete_inventory()
        self._cmd.pfeedback("[+] Inventory has been deleted successfully")
        self._cmd._inv_has_changed = False  # type: ignore[attr-defined]
        self.inventory_unload(None)  # type: ignore[attr-defined]

    @as_subcommand_to('inventory', 'list', list_parser,
                      aliases=["ls"],
                      help='list inventory')
    def inventory_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        data_list = []

        for inv in Inventory.list_inventory(ns.pattern):
            data_list.append([inv])

        columns: List[Column] = list()
        columns.append(Column("Name", width=32))
        st = SimpleTable(columns)
        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to('inventory', 'load', load_parser, help='load inventory')
    def inventory_load(self: CommandSet, ns: argparse.Namespace,
                       inv: Optional[Inventory] = None):
        if self._cmd is None:
            return
        self._cmd.check_if_inv_changed()  # type: ignore[attr-defined]

        if inv is not None:
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd._inv_has_changed = False  # type: ignore[attr-defined]

        if inv is None:
            try:
                inv = Inventory.load(ns.name)
            except exception.ShaaNameError as ex:
                self._cmd.perror(f"[!] {ex}")
                return
            self._cmd._inventory = inv  # type: ignore[attr-defined]

        # if inv is None:
        #     return

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
            self._cmd.pfeedback("[*] inventory node and group modules loaded")
            self._cmd.pfeedback(
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
        self._cmd.pfeedback("[*] inventory node and group modules unloaded")
        self._cmd._inv_has_changed = False  # type: ignore[attr-defined]

    @as_subcommand_to('inventory', 'save', save_parser,
                      help='save inventory data')
    def inventory_save(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            self._cmd.perror("[!] Currently, there is no inventory loaded")
            return
        try:
            if not inv.save(ns.name):
                self._cmd.perror("[!] Unable to save")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._inv_has_changed = False  # type: ignore[attr-defined]
        self._cmd.pfeedback("[+] inventory has been saved")

    @as_subcommand_to('inventory', 'rename', rename_parser,
                      help="""rename inventory name (save current changes \
automatically)""")
    def inventory_rename(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            self._cmd.perror("[!] Currently, there is no inventory loaded")
            return
        old_name = inv.name
        try:
            if not inv.rename_inventory(ns.name):
                self._cmd.perror("[!] Unable to rename")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._inv_has_changed = False  # type: ignore[attr-defined]
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is not None:
            profile.inv_name = inv.name
            self._cmd._profile_has_changed = True  # type: ignore[attr-defined]

        self._cmd.pfeedback("[+] inventory has been renamed")
        self._cmd.pfeedback(f"    old: {old_name}")
        self._cmd.pfeedback(f"    new: {inv.name}")

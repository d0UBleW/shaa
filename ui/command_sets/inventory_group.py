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
    HorizontalAlignment,
)
from dataclasses import asdict
import pprint
import re
from typing import List, Text
from utils.inventory import (
    Inventory,
    InventoryGroup,
)
from utils.parser import inventory_group_parser


@with_default_category("inventory group")
class inventory_group_cmd(CommandSet):

    @with_argparser(inventory_group_parser)
    def do_group(self, ns: argparse.Namespace):
        """
        Manage inventory group
        """
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help('group')
    pass


@with_default_category("inventory group")
class inventory_group_subcmd(CommandSet):
    def _choices_group_name(self) -> List[Text]:
        inv: Inventory = self._cmd._inventory
        return list(inv.groups.keys())

    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument(
        'name',
        type=str,
        metavar="group_name",
        help="group name to be created"
    )

    delete_parser = Cmd2ArgumentParser()
    delete_parser.add_argument(
        '-f',
        '--force',
        action="store_true",
        help="force deletion"
    )

    delete_parser.add_argument(
        'name',
        type=str,
        metavar="group_name",
        help="group name to be deleted",
        choices_provider=_choices_group_name
    )

    list_parser = Cmd2ArgumentParser()
    list_parser.add_argument(
        'pattern',
        nargs='?',
        default='.*',
        help='group name pattern in regex to be searched'
    )

    info_parser = Cmd2ArgumentParser()
    info_parser.add_argument(
        'pattern',
        type=str,
        metavar="pattern",
        help="group name regex pattern to be inspected",
        choices_provider=_choices_group_name
    )

    @as_subcommand_to("group", "create", create_parser,
                      help="create group on current inventory")
    def inv_group_create(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        group = InventoryGroup(ns.name)
        if inv.add_group(group) == 0:
            self._cmd.poutput("[+] Group has been created successfully")
        else:
            self._cmd.poutput("[!] Specified group name already existed")
            self._cmd.poutput("[!] Creation aborted!")

    @as_subcommand_to("group", "delete", delete_parser,
                      help="delete group from current inventory")
    def inv_group_delete(self, ns: argparse.Namespace):
        if not ns.force:
            self._cmd.poutput("[*] Deleting this group would also delete all")
            self._cmd.poutput("    the nodes within this group.")
            self._cmd.poutput("[*] Use -f/--force to skip this prompt")
            if (_ := self._cmd.read_input(
                    "[*] Do you want to proceed [y/N]? ")) != "y":
                self._cmd.poutput("[!] Deletion aborted")
                return
        inv: Inventory = self._cmd._inventory
        if inv.delete_group(ns.name) == 0:
            self._cmd.poutput("[+] Group has been deleted successfully")
        else:
            self._cmd.poutput("[!] Specified group name does not exist")

    @as_subcommand_to("group", "list", list_parser,
                      help="list groups from current inventory")
    def inv_group_list(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        groups: List[InventoryGroup] = inv.list_group(ns.pattern)

        data_list = []
        for group in groups:
            vars = pprint.pformat(group.group_vars, sort_dicts=False)
            data_list.append([group.name, len(group.nodes), vars])

        columns: List[Column] = [
            Column("Name", width=16),
            Column("Node Count",
                   width=10,
                   header_horiz_align=HorizontalAlignment.RIGHT,
                   data_horiz_align=HorizontalAlignment.RIGHT),
            Column("Vars", width=64),
        ]
        st = SimpleTable(columns)
        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to("group", "info", info_parser,
                      help="display group details")
    def inv_group_info(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        columns: List[Column] = [
            Column("Key", width=16),
            Column("Value", width=64),
        ]
        st = SimpleTable(columns)
        for group in inv.groups.values():
            if re.match(ns.pattern, group.name):
                data_list = list(asdict(group).items())
                data_list[1] = (data_list[1][0],
                                pprint.pformat(dict(data_list[1][1]),
                                               sort_dicts=False))
                data_list[-1] = (data_list[-1][0],
                                 pprint.pformat(dict(data_list[-1][-1]),
                                                sort_dicts=False))
                tbl = st.generate_table(data_list, row_spacing=1)
                self._cmd.poutput(f"\n{tbl}\n")

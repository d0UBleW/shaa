from __future__ import annotations

import argparse
import pprint
import re
from dataclasses import asdict
from typing import Dict, List, Text

from cmd2 import (Cmd2ArgumentParser, CommandSet, CompletionError,
                  as_subcommand_to, with_argparser, with_default_category)
from cmd2.table_creator import Column, HorizontalAlignment, SimpleTable
from ruamel.yaml.comments import TaggedScalar

from shaa_shell.utils import exception
from shaa_shell.utils.inventory import Inventory, InventoryGroup
from shaa_shell.utils.parser import inventory_group_parser
from shaa_shell.utils.vault import vault


@with_default_category("inventory group")
class inventory_group_cmd(CommandSet):

    @with_argparser(inventory_group_parser)
    def do_group(self: CommandSet, ns: argparse.Namespace):
        """
        Manage inventory group
        """
        if self._cmd is None:
            return
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
        if self._cmd is None:
            return []
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        return list(inv.groups.keys())

    def _choices_group_var(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        if self._cmd is None:
            return []
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]

        if "name" not in arg_tokens:
            raise CompletionError("[!] Missing group name to be targeted")

        group_name = arg_tokens["name"][0]

        group: InventoryGroup = inv.groups[group_name]
        g_vars = list(group.group_vars.keys())
        if len(g_vars) == 0:
            raise CompletionError("[!] No group_vars to be unset")
        return g_vars

    rename_parser = Cmd2ArgumentParser()
    rename_parser.add_argument(
        'name',
        metavar="group_name",
        help="group name to be renamed",
        choices_provider=_choices_group_name,
    )
    rename_parser.add_argument(
        'new_name',
        metavar="new_group_name",
        help="new group name",
    )

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

    unset_parser = Cmd2ArgumentParser()
    unset_parser.add_argument(
        'name',
        help="name of target group whose group variable to be unset",
        choices_provider=_choices_group_name,
    )
    unset_parser.add_argument(
        'group_var',
        help="name of group variable to be unset",
        choices_provider=_choices_group_var,
    )

    @as_subcommand_to("group", "rename", rename_parser,
                      help="rename group on current inventory")
    def inv_group_rename(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        try:
            if inv.rename_group(ns.name, ns.new_name) == 0:
                self._cmd.poutput("[+] Group has been renamed successfully")
                self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
        except exception.ShaaInventoryError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

    @as_subcommand_to("group", "create", create_parser,
                      aliases=["add"],
                      help="create group on current inventory")
    def inv_group_create(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        group = InventoryGroup(ns.name)
        if inv.add_group(group) == 0:
            self._cmd.poutput("[+] Group has been created successfully")
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd.perror("[!] Specified group name already existed")

    @as_subcommand_to("group", "delete", delete_parser,
                      aliases=["del", "rm"],
                      help="delete group from current inventory")
    def inv_group_delete(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        if not ns.force:
            self._cmd.perror("[!] Deleting this group would also delete all")
            self._cmd.perror("    the nodes within this group.")
            self._cmd.poutput("[*] Use -f/--force to skip this prompt")
            if (_ := self._cmd.read_input(
                    "[+] Do you want to proceed [y/N]? ")) != "y":
                self._cmd.perror("[!] Deletion aborted")
                return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        if inv.delete_group(ns.name) == 0:
            self._cmd.poutput("[+] Group has been deleted successfully")
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd.perror("[!] Specified group name does not exist")

    @as_subcommand_to("group", "list", list_parser,
                      aliases=["ls"],
                      help="list groups from current inventory")
    def inv_group_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        groups: List[InventoryGroup] = inv.list_group(ns.pattern)

        data_list: List[List] = []
        for group in groups:
            vars = []
            for key, val in group.group_vars.items():
                if isinstance(val, TaggedScalar):
                    val = vault.load(val)
                val = pprint.pformat(val, sort_dicts=False)
                vars.append(f"{key}: {val}")
            data_list.append([group.name, len(group.nodes), "\n".join(vars)])

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
    def inv_group_info(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        columns: List[Column] = [
            Column("Key", width=20),
            Column("Value", width=64),
        ]
        st = SimpleTable(columns)
        for group in inv.groups.values():
            if re.search(ns.pattern, group.name):
                data_list = list(asdict(group).items())
                # group nodes
                nodes = []
                for node in group.nodes.values():
                    node_data_list = list(asdict(node).items())
                    for i in range(len(node_data_list[:-1])):
                        if node_data_list[i][1] is None:
                            node_data_list[i] = (node_data_list[i][0], "")
                    node_vars = []
                    for key, val in node_data_list[-1][1].items():
                        if isinstance(val, TaggedScalar):
                            val = vault.load(val)
                        val = pprint.pformat(val, sort_dicts=False)
                        node_vars.append(f"{key}: {val}")
                    node_data_list[-1] = (node_data_list[-1]
                                          [0], "".join(node_vars))
                    node_tbl = st.generate_table(node_data_list,
                                                 row_spacing=0,
                                                 include_header=False)
                    nodes.append(node_tbl)
                data_list[1] = (data_list[1][0],
                                "\n---\n\n".join(nodes))
                # group vars
                vars = []
                for key, val in data_list[2][1].items():
                    if isinstance(val, TaggedScalar):
                        val = vault.load(val)
                    val = pprint.pformat(val, sort_dicts=False)
                    vars.append(f"{key}: {val}")

                data_list[2] = (data_list[2][0], "\n".join(vars))

                tbl = st.generate_table(data_list,
                                        row_spacing=1,
                                        include_header=False)
                sep = "-" * 16
                self._cmd.poutput(f"\n{sep}\n{tbl}\n{sep}\n")

    @as_subcommand_to("group", "unset", unset_parser,
                      help="unset group's group var")
    def inv_node_unset(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        inv: Inventory = self._cmd._inventory  # type: ignore

        if ns.name == "all":
            self._cmd.perror(f"[!] Invalid operation on specified group")
            return

        if ns.name not in inv.groups.keys():
            self._cmd.perror(f"[!] Invalid group name: {ns.name}")
            return

        group: InventoryGroup = inv.groups[ns.name]

        if ns.group_var not in group.group_vars.keys():
            self._cmd.perror(f"[!] Invalid group var: {ns.group_var}")
            return

        old_value = group.group_vars[ns.group_var]
        del group.group_vars[ns.group_var]
        if isinstance(old_value, TaggedScalar):
            old_value = vault.load(old_value)

        self._cmd.poutput(f"[+] {ns.group_var}:")
        self._cmd.poutput(f"    old: {old_value}")
        self._cmd._inv_has_changed = True  # type: ignore[attr-defined]

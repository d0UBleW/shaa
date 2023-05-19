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
    SimpleTable as BorderedTable,
    Column,
    HorizontalAlignment,
)
from cmd2.exceptions import CommandSetRegistrationError
from dataclasses import asdict
import pprint
import re
from typing import List, Text, Tuple, Dict
from utils.inventory import (
    list_inventory,
    Inventory,
    InventoryNode,
    InventoryGroup
)
from utils.parser import (
    inventory_node_parser,
    inventory_group_parser,
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
            data_list.append([node.name,
                              group_name,
                              f"{node.user}@{node.ip_address}"])

        columns: List[Column] = [
            Column("Name", width=16),
            Column("Group", width=16),
            Column("Connection Info", width=32),
        ]
        bt = BorderedTable(columns)
        tbl = bt.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to("node", "info", info_parser)
    def inv_node_info(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory

        columns: List[Column] = [
            Column("Key", width=16),
            Column("Value", width=64),
        ]
        bt = BorderedTable(columns)

        for node in inv.groups[ns.node_group].nodes.values():
            if re.match(ns.pattern, node.name):
                data_list = list(asdict(node).items())
                data_list[-1] = (data_list[-1][0],
                                 pprint.pformat(dict(data_list[-1][-1]),
                                                sort_dicts=False))
                tbl = bt.generate_table(data_list, row_spacing=0)
                self._cmd.poutput(f"\n{tbl}\n")


@with_default_category("inventory group")
class inventory_group_cmd(CommandSet):

    @with_argparser(inventory_group_parser)
    def do_group(self, ns: argparse.Namespace):
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

    @as_subcommand_to("group", "create", create_parser)
    def inv_group_create(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        group = InventoryGroup(ns.name)
        if inv.add_group(group) == 0:
            self._cmd.poutput("[+] Group has been created successfully")
        else:
            self._cmd.poutput("[!] Specified group name already existed")
            self._cmd.poutput("[!] Creation aborted!")

    @as_subcommand_to("group", "delete", delete_parser)
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

    @as_subcommand_to("group", "list", list_parser)
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
        bt = BorderedTable(columns)
        tbl = bt.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to("group", "info", info_parser)
    def inv_group_info(self, ns: argparse.Namespace):
        inv: Inventory = self._cmd._inventory
        columns: List[Column] = [
            Column("Key", width=16),
            Column("Value", width=64),
        ]
        bt = BorderedTable(columns)
        for group in inv.groups.values():
            if re.match(ns.pattern, group.name):
                data_list = list(asdict(group).items())
                data_list[1] = (data_list[1][0],
                                pprint.pformat(dict(data_list[1][1]),
                                               sort_dicts=False))
                data_list[-1] = (data_list[-1][0],
                                 pprint.pformat(dict(data_list[-1][-1]),
                                                sort_dicts=False))
                tbl = bt.generate_table(data_list, row_spacing=1)
                self._cmd.poutput(f"\n{tbl}\n")

from __future__ import annotations

import argparse
from typing import Dict, List, Optional, Text

from cmd2 import (Cmd2ArgumentParser, CommandSet,  # type: ignore[import]
                  CompletionError, CompletionItem, as_subcommand_to,
                  with_argparser, with_default_category)
from cmd2.table_creator import Column, SimpleTable  # type: ignore[import]
from ruamel.yaml.comments import TaggedScalar

from shaa_shell.utils import exception
from shaa_shell.utils.inventory import Inventory, InventoryGroup, InventoryNode
from shaa_shell.utils.parser import role_util_parser
from shaa_shell.utils.role import Role
from shaa_shell.utils.vault import vault


@with_default_category("util")
class util_cmd(CommandSet):
    @with_argparser(role_util_parser)
    def do_util(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("util")


@with_default_category("util")
class util_action_cmd(CommandSet):
    def _choices_util_action_title(self) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        data = self._cmd._util.list_action_and_details()  # type: ignore
        return [CompletionItem(act, task["title"]) for act, task in data]

    def _choices_util_action_enable(self) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        data = self._cmd._util.list_action_and_details()  # type: ignore
        cmp = [CompletionItem(act, task["title"]) for act, task in data]
        cmp.append(CompletionItem("all", "Everything"))
        return cmp

    def util_action_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        role_util: Optional[Role] = self._cmd._util  # type: ignore

        if role_util is None:
            self._cmd.perror("[!] No util preset is loaded")
            return

        data = role_util.list_action_and_details()  # type: ignore
        columns = [
            Column("Action", width=24),
            Column("Enabled", width=8),
            Column("Title", width=80),
        ]
        st = SimpleTable(columns)
        data_list = []
        for act, task in data:
            enabled = role_util.get_enabled(act)
            if ns.status == "all":
                data_list.append([act, enabled, task["title"]])
                continue
            if ns.status == "enabled" and enabled:
                data_list.append([act, enabled, task["title"]])
                continue
            if ns.status == "disabled" and not enabled:
                data_list.append([act, enabled, task["title"]])

        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    def util_action_enable(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            return

        valid_action = [
            "all",
        ]

        for arg_act in ns.action:
            if arg_act not in valid_action:
                if not role_util.is_valid_action(arg_act):
                    self._cmd.perror("[!] Invalid action")
                    return

            if arg_act == "all":
                for act in role_util.actions.keys():
                    role_util.set_enabled(act, True)
                    if ns.verbose:
                        self._cmd.poutput(f"[+] {act} enabled successfully")
            else:
                role_util.set_enabled(arg_act, True)
                if ns.verbose:
                    self._cmd.poutput(f"[+] {arg_act} enabled successfully")
        self._cmd._util_has_changed = True  # type: ignore[attr-defined]
        self._cmd.poutput("[+] Enabled successfully")

    def util_action_disable(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            return

        for arg_act in ns.action:
            if arg_act != "all" and not role_util.is_valid_action(arg_act):
                self._cmd.perror(f"[!] Invalid action: {arg_act}")
                return

            if arg_act == "all":
                for act in role_util.actions.keys():
                    role_util.set_enabled(act, False)
                    if ns.verbose:
                        self._cmd.poutput(f"[+] {act} disabled successfully")
            else:
                role_util.set_enabled(arg_act, False)
                if ns.verbose:
                    self._cmd.poutput(f"[+] {act} disabled successfully")
        self._cmd._util_has_changed = True  # type: ignore[attr-defined]
        self._cmd.poutput("[+] Disabled successfully")

    def util_action_info(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        role_util: Optional[Role] = self._cmd._util  # type: ignore

        if role_util is None:
            return

        if not role_util.is_valid_action(ns.action):
            self._cmd.perror("[!] Invalid action")
            return

        columns = [
            Column("Key", width=16),
            Column("Value", width=128),
        ]
        st = SimpleTable(columns)
        task = role_util.actions[ns.action]
        data_list = []
        for key, value in task.items():
            if key == "vars":
                continue
            data_list.append([key, value])

        data_list.append(["enabled", role_util.get_enabled(ns.action)])

        tbl = st.generate_table(data_list,
                                row_spacing=0,
                                include_header=False)
        self._cmd.poutput(f"{tbl}\n")
        if "vars" in task.keys() and task["vars"] is not None:
            vars_columns = [
                Column("Key", width=24),
                Column("Description", width=56),
                Column("Default", width=40),
                Column("Value", width=40),
            ]
            vars_st = SimpleTable(vars_columns)
            vars_data_list = []
            for var_key, var in task["vars"].items():
                detail = f"{var['description']}"

                # add description for range type variable
                if var["value_type"] == "range":
                    if var["range_start"] is not None:
                        detail += f"Possible min value: {var['range_start']}\n"
                    if var["range_end"] is not None:
                        detail += f"Possible max value: {var['range_end']}\n"
                if "choice" in var["value_type"]:
                    detail += f"Possible value:\n"
                    detail += "\n".join(
                        list(map(lambda v: f"- {v}", var["valid"])))

                default_val = var["default"]
                # format list type default variable
                if isinstance(default_val, list):
                    if isinstance(default_val[0], str):
                        default_val = "\n".join(
                            list(map(lambda v: f"- {v}", var["default"])))

                user_val = role_util.get_var(ns.action, var_key)
                # format list type variable
                if isinstance(user_val, list):
                    if isinstance(user_val[0], str):
                        user_val = "\n".join(
                            list(map(lambda v: f"- {v}", var["value"])))

                # format sensitive type variable
                if isinstance(user_val, TaggedScalar):
                    user_val = vault.load(user_val)

                if default_val is None:
                    default_val = ""
                if user_val is None:
                    user_val = ""
                vars_data_list.append([
                    var_key,
                    detail,
                    default_val,
                    user_val,
                ])

            vars_tbl = vars_st.generate_table(vars_data_list)
            self._cmd.poutput(f"Settable variables:\n\n{vars_tbl}\n")

    action_parser = Cmd2ArgumentParser()

    action_subparser = action_parser.add_subparsers(
        title="subcommand", help="subcommand for util action")

    @as_subcommand_to("util", "action", action_parser,
                      help="action subcommand")
    def util_action(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        func = getattr(ns, "func", None)
        if func is not None:
            func(self, ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("util action")

    list_parser = action_subparser.add_parser(
        "list", help="list available actions")
    list_parser.add_argument(
        "--status",
        nargs="?",
        choices=["enabled", "disabled", "all"],
        default="all",
        help="filter actions based on their status"
    )
    list_parser.set_defaults(func=util_action_list)

    enable_parser = action_subparser.add_parser(
        "enable",
        help="enable action")
    enable_parser.add_argument("-v",
                               "--verbose",
                               action="store_true",
                               help="verbose output")
    enable_parser.add_argument(
        "action",
        nargs="+",
        choices_provider=_choices_util_action_enable,
        descriptive_header="Title",
        help="action to be enabled (use `all` for everything)")
    enable_parser.set_defaults(func=util_action_enable)

    disable_parser = action_subparser.add_parser(
        "disable",
        help="disable action")
    disable_parser.add_argument("-v",
                                "--verbose",
                                action="store_true",
                                help="verbose output")
    disable_parser.add_argument(
        "action",
        nargs="+",
        choices_provider=_choices_util_action_enable,
        descriptive_header="Title",
        help="action to be disabled (use `all` for everything)")
    disable_parser.set_defaults(func=util_action_disable)

    info_parser = action_subparser.add_parser(
        "info", help="info action")
    info_parser.add_argument("action",
                             choices_provider=_choices_util_action_title,
                             descriptive_header="Title",
                             help="action whose details to be displayed")
    info_parser.set_defaults(func=util_action_info)


@with_default_category("util")
class util_set_cmd(CommandSet):
    def _choices_group_name(self) -> List[Text]:
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            raise CompletionError(
                "[!] No inventory is loaded, unable to provide completion")
        return list(inv.groups.keys())

    def _choices_node_name(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        if self._cmd is None:
            return []
        inv: Inventory = self._cmd._inventory  # type: ignore[attr-defined]
        group = "ungrouped"
        if "group_name" in arg_tokens:
            group = arg_tokens["group_name"][0]
        nodes = list(map(lambda n: n[0].name, inv.list_node(groups=[group])))
        return nodes

    def _choices_util_action_w_vars_and_details(self) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        data = self._cmd._util.list_action_w_vars_and_details()  # type: ignore
        return [CompletionItem(act, task["title"]) for act, task in data]

    def _choices_util_option_key(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            return []

        action = None
        if "action" in arg_tokens:
            action = arg_tokens["action"][0]

        if action is None:
            raise CompletionError(
                "[!] Please specify an action first with `--action`")

        if not role_util.has_settable_vars(action):
            raise CompletionError(f"[!] {action} has no settable variable")

        try:
            task_vars = role_util.actions[action]["vars"]
        except KeyError:
            raise CompletionError(f"[!] Invalid action: {action}")

        cmp: List[CompletionItem] = []
        for var_key, var in task_vars.items():
            detail = f"{var['description']}"
            cmp.append(CompletionItem(var_key, detail))
        return cmp

    def _choices_util_option_value(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        if self._cmd is None:
            return []
        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            return []

        action = None
        if "action" in arg_tokens:
            action = arg_tokens["action"][0]

        if action is None:
            return []

        option_key = None
        if "option_key" in arg_tokens:
            option_key = arg_tokens["option_key"][0]

        if option_key is None:
            return []

        task_vars = role_util.actions[action]["vars"]
        for var_key, var in task_vars.items():
            if var_key != option_key:
                continue
            if var["value_type"] == "choice":
                return var["valid"]
            if var["value_type"] == "list_choice":
                return var["valid"]
            if var["value_type"] == "bool":
                return ["True", "False"]
        return []

    set_parser = Cmd2ArgumentParser()
    set_parser.add_argument(
        "-a",
        "--action",
        dest="action",
        choices_provider=_choices_util_action_w_vars_and_details,
        help="""narrow down to specific action with settable vars for \
better tab completion"""
    )
    set_parser.add_argument("option_key",
                            choices_provider=_choices_util_option_key,
                            help="name of option to be set")
    set_parser.add_argument("option_value",
                            nargs="+",
                            choices_provider=_choices_util_option_value,
                            help="new option value")
    set_parser.add_argument("-g",
                            "--group-name",
                            nargs="?",
                            choices_provider=_choices_group_name,
                            help="apply setting to specified group name")
    set_parser.add_argument("-n",
                            "--node-name",
                            nargs="?",
                            choices_provider=_choices_node_name,
                            help="apply setting to specified node name")

    unset_parser = Cmd2ArgumentParser()
    unset_parser.add_argument(
        "-a",
        "--action",
        dest="action",
        choices_provider=_choices_util_action_w_vars_and_details,
        help="""narrow down to specific action with settable vars for \
better tab completion"""
    )
    unset_parser.add_argument("option_key",
                              choices_provider=_choices_util_option_key,
                              help="name of option to be set")
    unset_parser.add_argument("-g",
                              "--group-name",
                              nargs="?",
                              choices_provider=_choices_group_name,
                              help="unset setting from specified group name")
    unset_parser.add_argument("-n",
                              "--node-name",
                              nargs="?",
                              choices_provider=_choices_node_name,
                              help="apply setting to specified node name")

    @as_subcommand_to("util", "set", set_parser,
                      help="set subcommand")
    def util_set(self: CommandSet, ns: argparse.Namespace):
        """
        If an option accepts a list of value, then every args separated by
        whitespaces after option_key would be considered as the list value
        """
        if self._cmd is None:
            return
        role_util: Optional[Role] = self._cmd._util  # type: ignore
        action = ns.action
        opt_key = ns.option_key
        opt_val = ns.option_value
        if role_util is None:
            self._cmd.perror("[!] util object is None")
            return
        if not role_util.is_valid_action(action):
            self._cmd.perror("[!] Invalid action")
            return
        if not role_util.has_settable_vars(action):
            self._cmd.perror(f"[!] {action} has no settable variable")
            return
        if not role_util.is_valid_option_key(action, opt_key):
            self._cmd.perror("[!] Invalid option key")
            return
        try:
            opt_val = role_util.parse_option_val(action, opt_key, opt_val)
        except exception.ShaaVariableError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        val = opt_val

        if ns.node_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.perror("[!] No inventory is loaded")
                self._cmd.perror("[!] Unable to set variable")
                return
            gname = ns.group_name
            nname = ns.node_name
            if gname is None:
                gname = "ungrouped"
            nodes: Dict[Text, InventoryNode] = inv.groups[gname].nodes
            if nname not in nodes.keys():
                self._cmd.perror("[!] Node name does not exist")
                return
            node = nodes[nname]
            old_value = None
            if opt_key in node.host_vars:
                old_value = node.host_vars[opt_key]
            node.host_vars[opt_key] = val
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            if isinstance(val, TaggedScalar):
                val = vault.load(val)
            if old_value is None:
                old_value = ""
            if val is None:
                val = ""
            self._cmd.poutput(f"[+] Node: {nname} ({gname})")
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    new: {val}")
            return
        elif ns.group_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.perror("[!] No inventory is loaded")
                self._cmd.perror("[!] Unable to set variable")
                return
            gname = ns.group_name
            if gname not in inv.groups:
                self._cmd.perror(f"[!] Group name not found: {gname}")
                return
            if gname == "ungrouped":
                self._cmd.perror(f"[!] {gname} is not settable")
                return
            group: InventoryGroup = inv.groups[gname]
            old_value = None
            if opt_key in group.group_vars:
                old_value = group.group_vars[opt_key]
            group.group_vars[opt_key] = val
            self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            if isinstance(val, TaggedScalar):
                val = vault.load(val)
            if old_value is None:
                old_value = ""
            if val is None:
                val = ""
            self._cmd.poutput(f"[+] Group: {gname}")
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    new: {val}")
            return
        else:
            old_value = role_util.get_var(action, opt_key)
            role_util.set_var(action, opt_key, val)
            self._cmd._util_has_changed = True  # type: ignore[attr-defined]
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            if isinstance(val, TaggedScalar):
                val = vault.load(val)
            if old_value is None:
                old_value = ""
            if val is None:
                val = ""
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    new: {val}")
            return

    @as_subcommand_to("util", "unset", unset_parser,
                      help="set subcommand")
    def util_unset(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        role_util: Optional[Role] = self._cmd._util  # type: ignore
        action = ns.action
        opt_key = ns.option_key
        if role_util is None:
            self._cmd.perror("[!] util object is None")
            return
        if not role_util.is_valid_action(action):
            self._cmd.perror("[!] Invalid action")
            return
        if not role_util.has_settable_vars(action):
            self._cmd.perror(f"[!] {action} has no unsettable variable")
            return
        if not role_util.is_valid_option_key(action, opt_key):
            self._cmd.perror("[!] Invalid option key")
            return

        option = role_util.actions[action]["vars"][opt_key]

        if ns.node_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.perror("[!] No inventory is loaded")
                self._cmd.perror("[!] Unable to set variable")
                return
            gname = ns.group_name
            nname = ns.node_name
            if gname is None:
                gname = "ungrouped"
            nodes: Dict[Text, InventoryNode] = inv.groups[gname].nodes
            if nname not in nodes.keys():
                self._cmd.perror("[!] Node name does not exist")
                return
            self._cmd.poutput(f"[+] Node: {nname} ({gname})")
            node = nodes[nname]
            old_value = None
            if opt_key in node.host_vars:
                old_value = node.host_vars[opt_key]
                del node.host_vars[opt_key]
                self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
            else:
                self._cmd.perror("[!] Option key not found")
                return
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            default = option["default"]
            if isinstance(default, TaggedScalar):
                default = vault.load(default)
            if old_value is None:
                old_value = ""
            if default is None:
                default = ""
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    default: {default}")
            return
        elif ns.group_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.perror(
                    "[!] No inventory is loaded")
                self._cmd.perror(
                    "[!] Unable to unset variable on this group name")
                return
            gname = ns.group_name
            if gname not in inv.groups:
                self._cmd.perror(f"[!] Group name not found: {gname}")
                return
            if gname == "ungrouped":
                self._cmd.perror(f"[!] {gname} is not unsettable")
                return
            group: InventoryGroup = inv.groups[gname]
            self._cmd.poutput(f"[+] Group: {gname}")
            if opt_key in group.group_vars:
                old_value = group.group_vars[opt_key]
                del group.group_vars[opt_key]
                self._cmd._inv_has_changed = True  # type: ignore
            else:
                self._cmd.perror("[!] Option key not found")
                return
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            default = option["default"]
            if isinstance(default, TaggedScalar):
                default = vault.load(default)
            if old_value is None:
                old_value = ""
            if default is None:
                default = ""
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    default: {default}")
            return
        else:
            old_value = role_util.get_var(action, opt_key)
            role_util.set_var(action, opt_key, None)
            self._cmd._util_has_changed = True  # type: ignore[attr-defined]

            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            default = option["default"]
            if isinstance(default, TaggedScalar):
                default = vault.load(default)
            if old_value is None:
                old_value = ""
            if default is None:
                default = ""
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    default: {default}")
            return


@with_default_category("util")
class util_search_cmd(CommandSet):
    search_parser = Cmd2ArgumentParser()
    search_parser.add_argument("-i",
                               "--ignore-case",
                               dest="ignore_case",
                               action="store_true",
                               help="case insensitive")
    search_parser.add_argument("pattern",
                               help="pattern in regex format to be searched")

    @as_subcommand_to("util", "search", search_parser,
                      help="search subcommand")
    def util_search(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            self._cmd.perror("[!] No util preset is loaded")
            return

        pattern = ns.pattern
        if ns.ignore_case:
            pattern = f"(?i){pattern}"
        data = role_util.list_action_and_details(search_query=pattern)
        columns = [
            Column("Action", width=24),
            Column("Enabled", width=8),
            Column("Title", width=80),
        ]
        st = SimpleTable(columns)
        data_list = []
        for act, task in data:
            enabled = role_util.get_enabled(act)
            data_list.append([act, enabled, task["title"]])

        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

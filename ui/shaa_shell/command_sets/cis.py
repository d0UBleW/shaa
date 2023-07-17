from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional, Text

from cmd2 import (Cmd2ArgumentParser, CommandSet,  # type: ignore[import]
                  CompletionError, CompletionItem, as_subcommand_to,
                  with_argparser, with_default_category)
from cmd2.table_creator import Column, SimpleTable  # type: ignore[import]
from ruamel.yaml.comments import TaggedScalar

from shaa_shell.utils import exception
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.inventory import Inventory, InventoryGroup, InventoryNode
from shaa_shell.utils.parser import cis_parser
from shaa_shell.utils.vault import vault


def filter_section_level(section_id: Text, data: List[Any]) -> List[Any]:
    def _filter(s, lvl):
        return s.count(".") == lvl and s.startswith(section_id)

    level = section_id.count(".")
    filtered = list(filter(lambda s: _filter(s[0], level), data))
    if len(filtered) == 1:
        deeper = list(filter(lambda s: _filter(s[0], level + 1), data))
        if len(deeper) > 0:
            return deeper
    return filtered


@with_default_category("cis")
class cis_cmd(CommandSet):
    @with_argparser(cis_parser)
    def do_cis(self: CommandSet, ns: argparse.Namespace):
        """
        Manage CIS preset settings
        """
        if self._cmd is None:
            return
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("cis")


@with_default_category("cis")
class cis_section_cmd(CommandSet):
    def _choices_cis_section_title(
        self,
        arg_tokens: Dict[Text, List[Text]],
    ) -> List[CompletionItem]:
        """
        Provide completion on section id while showing its title
        """
        if self._cmd is None:
            return []

        section_id = ""
        if "section_id" in arg_tokens:
            section_id = arg_tokens["section_id"][0]

        data = self._cmd._cis.list_section_and_details()  # type: ignore

        if "incremental" in arg_tokens:
            data = filter_section_level(section_id, data)

        return [CompletionItem(s_id, s["title"]) for s_id, s in data]

    def _choices_cis_section_enable(self) -> List[CompletionItem]:
        """
        Provide completion on available options for enabling CIS sections
        """
        if self._cmd is None:
            return []
        data = self._cmd._cis.list_section_and_details()  # type: ignore
        cmp = [CompletionItem(s_id, s["title"]) for s_id, s in data]
        cmp.append(CompletionItem("all", "Everything"))
        cmp.append(CompletionItem("level_1_server", "Level 1 Server profile"))
        cmp.append(CompletionItem("level_2_server", "Level 2 Server profile"))
        cmp.append(
            CompletionItem(
                "level_1_workstation",
                "Level 1 Workstation profile"))
        cmp.append(
            CompletionItem(
                "level_2_workstation",
                "Level 2 Workstation profile"))
        return cmp

    def _choices_cis_section_disable(self) -> List[CompletionItem]:
        """
        Provide completion on available options for disabling CIS sections
        """
        if self._cmd is None:
            return []
        data = self._cmd._cis.list_section_and_details()  # type: ignore
        cmp = [CompletionItem(s_id, s["title"]) for s_id, s in data]
        cmp.append(CompletionItem("all", "Everything"))
        return cmp

    def cis_section_list(self: CommandSet, ns: argparse.Namespace):
        """
        List CIS sections with its status and title
        """
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]

        if cis is None:
            self._cmd.perror("[!] No CIS preset is loaded")
            return

        data = cis.list_section_and_details(ns.section_id)
        columns = [
            Column("Section ID", width=10),
            Column("Enabled", width=8),
            Column("Title", width=96),
        ]
        st = SimpleTable(columns)
        data_list = []
        for s_id, s in data:
            enabled = cis.get_enabled(s_id)
            if ns.status == "all":
                data_list.append([s_id, enabled, s["title"]])
                continue
            if ns.status == "enabled" and enabled:
                data_list.append([s_id, enabled, s["title"]])
                continue
            if ns.status == "disabled" and not enabled:
                data_list.append([s_id, enabled, s["title"]])

        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    def cis_section_enable(self: CommandSet, ns: argparse.Namespace):
        """
        Handles CIS section enabling
        """
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            self._cmd.perror("[!] No CIS preset is loaded")
            return

        special_id = [
            "all",
            "level_1_server",
            "level_2_server",
            "level_1_workstation",
            "level_2_workstation",
        ]

        for arg_s_id in ns.section_id:
            # Validate passed arguments
            if arg_s_id not in special_id:
                if not cis.is_valid_section_id(arg_s_id):
                    self._cmd.perror(f"[!] Invalid section id: {arg_s_id}")
                    return

            """
            Loop through all available section id and enable its corresponding
            subsections
            """
            for s_id in cis.sections.keys():
                is_sub = CIS.is_subsection(arg_s_id, s_id)
                """
                1.2.3 is subsection of 1.2
                1.2 is also subection of 1.2
                """
                if not is_sub and arg_s_id not in special_id:
                    continue
                # Handle special arguments
                if arg_s_id.startswith("level_"):
                    section = cis.sections[s_id]
                    if "profile" not in section.keys():
                        continue
                    s_profile = arg_s_id.replace("_", " ").title()
                    if s_profile not in section["profile"]:
                        continue
                    cis.set_enabled(s_id, True)
                    if ns.verbose:
                        self._cmd.pfeedback(f"[+] {s_id} enabled successfully")
                else:
                    # Handle `all` and valid subsection
                    cis.set_enabled(s_id, True)
                    if ns.verbose:
                        self._cmd.pfeedback(f"[+] {s_id} enabled successfully")
        self._cmd._cis_has_changed = True  # type: ignore[attr-defined]
        self._cmd.pfeedback("[+] Enabled successfully")

    def cis_section_disable(self: CommandSet, ns: argparse.Namespace):
        """
        Handles CIS section enabling
        """
        if self._cmd is None:
            return
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            return

        for arg_s_id in ns.section_id:
            if arg_s_id != "all" and not cis.is_valid_section_id(arg_s_id):
                self._cmd.perror(f"[!] Invalid section id: {arg_s_id}")
                return

            for s_id in cis.sections.keys():
                if CIS.is_subsection(arg_s_id, s_id) or arg_s_id == "all":
                    cis.set_enabled(s_id, False)
                    if ns.verbose:
                        self._cmd.pfeedback(
                            f"[+] {s_id} disabled successfully")
        self._cmd._cis_has_changed = True  # type: ignore[attr-defined]
        self._cmd.pfeedback("[+] Disabled successfully")

    def cis_section_info(self: CommandSet, ns: argparse.Namespace):
        """
        Function to show section details
        """
        if self._cmd is None:
            return
        cis: CIS = self._cmd._cis  # type: ignore[attr-defined]
        if not cis.is_valid_section_id(ns.section_id):
            self._cmd.perror("[!] Invalid section id")
            return

        columns = [
            Column("Key", width=16),
            Column("Value", width=128),
        ]
        st = SimpleTable(columns)
        section = cis.sections[ns.section_id]
        data_list = []
        for key, value in section.items():
            if key == "vars":
                continue
            data_list.append([key, value])

        data_list.append(["enabled", cis.get_enabled(ns.section_id)])

        tbl = st.generate_table(data_list,
                                row_spacing=0,
                                include_header=False)
        self._cmd.poutput(f"{tbl}\n")
        if "vars" in section.keys() and section["vars"] is not None:
            vars_columns = [
                Column("Key", width=24),
                Column("Description", width=56),
                Column("Default", width=40),
                Column("Value", width=40),
            ]
            vars_st = SimpleTable(vars_columns)
            vars_data_list = []
            for var_key, var in section["vars"].items():
                detail = f"{var['description']}"
                if var["value_type"] == "range" and "aide_" not in var_key:
                    if var["range_start"] is not None:
                        detail += f"Possible min value: {var['range_start']}\n"
                    if var["range_end"] is not None:
                        detail += f"Possible max value: {var['range_end']}\n"
                if "choice" in var["value_type"]:
                    detail += f"Possible value:\n"
                    detail += "\n".join(
                        list(map(lambda v: f"- {v}", var["valid"])))
                default_val = var["default"]
                if isinstance(default_val, list):
                    if isinstance(default_val[0], str):
                        default_val = "\n".join(
                            list(map(lambda v: f"- {v}", var["default"])))
                user_val = cis.get_var(ns.section_id, var_key)
                if isinstance(user_val, list):
                    if isinstance(user_val[0], str):
                        user_val = "\n".join(
                            list(map(lambda v: f"- {v}", user_val)))
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

    section_parser = Cmd2ArgumentParser()

    section_subparser = section_parser.add_subparsers(
        title="subcommand", help="subcommand for cis section")

    @as_subcommand_to("cis", "section", section_parser,
                      help="section subcommand")
    def cis_section(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        func = getattr(ns, "func", None)
        if func is not None:
            func(self, ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("cis section")

    list_parser = section_subparser.add_parser(
        "list", help="list available section ids")
    list_parser.add_argument("-i",
                             "--incremental",
                             action="store_true",
                             help="incremental tab completion")
    list_parser.add_argument(
        "--status",
        nargs="?",
        choices=["enabled", "disabled", "all"],
        default="all",
        help="filter sections based on their status"
    )
    list_parser.add_argument(
        "section_id",
        nargs="?",
        choices_provider=_choices_cis_section_title,
        help="""if specified, it would list out corresponding subsections \
(e.g., 1, 2.1, 3.3.1)"""
    )
    list_parser.set_defaults(func=cis_section_list)

    enable_parser = section_subparser.add_parser(
        "enable",
        help="""enable section id (behave recursively if specified section \
has subsections)""")
    enable_parser.add_argument("-v",
                               "--verbose",
                               action="store_true",
                               help="verbose output")
    enable_parser.add_argument(
        "section_id",
        nargs="+",
        choices_provider=_choices_cis_section_enable,
        descriptive_header="Title",
        help="section id to be enabled (use `all` for everything)")
    enable_parser.set_defaults(func=cis_section_enable)

    disable_parser = section_subparser.add_parser(
        "disable",
        help="""disable section id (behave recursively if specified section \
has subsections)""")
    disable_parser.add_argument("-v",
                                "--verbose",
                                action="store_true",
                                help="verbose output")
    disable_parser.add_argument(
        "section_id",
        nargs="+",
        choices_provider=_choices_cis_section_disable,
        descriptive_header="Title",
        help="section id to be disabled (use `all` for everything)")
    disable_parser.set_defaults(func=cis_section_disable)

    info_parser = section_subparser.add_parser(
        "info", help="info section id")
    info_parser.add_argument("-i",
                             "--incremental",
                             action="store_true",
                             help="incremental tab completion")
    info_parser.add_argument("section_id",
                             choices_provider=_choices_cis_section_title,
                             descriptive_header="Title",
                             help="section id whose details to be displayed")
    info_parser.set_defaults(func=cis_section_info)


@with_default_category("cis")
class cis_set_cmd(CommandSet):
    def _choices_group_name(self) -> List[Text]:
        """
        Provide completion on available group name based on loaded inventory
        """
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            raise CompletionError(
                "[!] No inventory is loaded, unable to provide completion")
        return list(inv.groups.keys())

    def _choices_node_name(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        """
        Provide completion on available node name based on loaded inventory
        and specified group name
        """
        if self._cmd is None:
            return []
        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is None:
            raise CompletionError(
                "[!] No inventory is loaded, unable to provide completion")
        group = "all"
        if "group_name" in arg_tokens:
            group = arg_tokens["group_name"][0]
        nodes = list(map(lambda n: n[0].name, inv.list_node(groups=[group])))
        return nodes

    def _choices_cis_section_unit_and_title(self) -> List[CompletionItem]:
        """
        Provide completion on sections with settable variables
        """
        if self._cmd is None:
            return []
        data = self._cmd._cis.list_section_unit_and_details()  # type: ignore
        return [CompletionItem(s_id, s["title"]) for s_id, s in data]

    def _choices_cis_option_key(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[CompletionItem]:
        """
        Provide completion on settable variables based on specified section id
        """
        if self._cmd is None:
            return []
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            return []

        section_id = None
        if "section_id" in arg_tokens:
            section_id = arg_tokens["section_id"][0]

        if section_id is None:
            raise CompletionError(
                "[!] Please specify a section id first with `-s`")

        if section_id not in cis.sections.keys():
            raise CompletionError(f"[!] Invalid section: {section_id}")

        if not cis.has_settable_vars(section_id):
            raise CompletionError(f"[!] {section_id} has no settable variable")

        section_vars = cis.sections[section_id]["vars"]
        cmp: List[CompletionItem] = []
        for var_key, var in section_vars.items():
            detail = f"{var['description']}"
            cmp.append(CompletionItem(var_key, detail))
        return cmp

    def _choices_cis_option_value(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        """
        Provide completion on appropriate variable value where applicable
        """
        if self._cmd is None:
            return []
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            return []

        section_id = None
        if "section_id" in arg_tokens:
            section_id = arg_tokens["section_id"][0]

        if section_id is None:
            raise CompletionError(
                "[!] Please specify a section id first with `-s`")

        option_key = None
        if "option_key" in arg_tokens:
            option_key = arg_tokens["option_key"][0]

        if option_key is None:
            return []

        if section_id not in cis.sections.keys():
            raise CompletionError(f"[!] Invalid section: {section_id}")

        if not cis.has_settable_vars(section_id):
            raise CompletionError(f"[!] {section_id} has no settable variable")

        section_vars = cis.sections[section_id]["vars"]
        if option_key not in section_vars.keys():
            raise CompletionError(f"[!] Invalid option key: {option_key}")

        var = section_vars[option_key]
        if var["value_type"] == "choice":
            return var["valid"]
        if var["value_type"] == "list_choice":
            return var["valid"]
        if var["value_type"] == "bool":
            return ["True", "False"]
        return []

    set_parser = Cmd2ArgumentParser()
    set_parser.add_argument(
        "-s",
        "--section-id",
        dest="section_id",
        choices_provider=_choices_cis_section_unit_and_title,
        help="""narrow down to specific section id with settable vars for \
better tab completion"""
    )
    set_parser.add_argument("option_key",
                            choices_provider=_choices_cis_option_key,
                            help="name of option to be set")
    set_parser.add_argument("option_value",
                            nargs="+",
                            choices_provider=_choices_cis_option_value,
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
        "-s",
        "--section-id",
        dest="section_id",
        choices_provider=_choices_cis_section_unit_and_title,
        help="""narrow down to specific section id with settable vars for \
better tab completion"""
    )
    unset_parser.add_argument("option_key",
                              choices_provider=_choices_cis_option_key,
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

    @as_subcommand_to("cis", "set", set_parser,
                      help="set subcommand")
    def cis_set(self: CommandSet, ns: argparse.Namespace):
        """
        If an option accepts a list of value, then every args separated by
        whitespaces after option_key would be considered as the list value
        """
        if self._cmd is None:
            return
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        s_id = ns.section_id
        opt_key = ns.option_key
        opt_val = ns.option_value
        if cis is None:
            self._cmd.perror("[!] cis object is None")
            return
        if not cis.is_valid_section_id(s_id):
            self._cmd.perror("[!] Invalid section id")
            return
        if not cis.has_settable_vars(s_id):
            self._cmd.perror(f"[!] {s_id} has no settable variable")
            return
        if not cis.is_valid_option_key(s_id, opt_key):
            self._cmd.perror("[!] Invalid option key")
            return
        try:
            opt_val = cis.parse_option_val(s_id, opt_key, opt_val)
        except exception.ShaaVariableError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        val = opt_val

        # node-level setting
        if ns.node_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.perror("[!] No inventory is loaded")
                self._cmd.perror("[!] Unable to set variable")
                return
            gname = ns.group_name
            nname = ns.node_name
            if gname is None:
                gname = "all"
            if gname not in inv.groups.keys():
                self._cmd.perror("[!] Group name does not exist")
                return
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
            self._cmd.pfeedback(f"[+] Node: {nname} ({gname})")
            self._cmd.pfeedback(f"[+] {opt_key}:")
            self._cmd.pfeedback(f"    old: {old_value}")
            self._cmd.pfeedback(f"    new: {val}")
            return
        # group-level setting
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
            if gname == "all":
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
            self._cmd.pfeedback(f"[+] Group: {gname}")
            self._cmd.pfeedback(f"[+] {opt_key}:")
            self._cmd.pfeedback(f"    old: {old_value}")
            self._cmd.pfeedback(f"    new: {val}")
            return
        # global-level setting
        else:
            old_value = cis.get_var(s_id, opt_key)
            cis.set_var(s_id, opt_key, val)
            self._cmd._cis_has_changed = True  # type: ignore[attr-defined]
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            if isinstance(val, TaggedScalar):
                val = vault.load(val)
            if old_value is None:
                old_value = ""
            if val is None:
                val = ""
            self._cmd.pfeedback(f"[+] {opt_key}:")
            self._cmd.pfeedback(f"    old: {old_value}")
            self._cmd.pfeedback(f"    new: {val}")
            return

    @as_subcommand_to("cis", "unset", unset_parser,
                      help="set subcommand")
    def cis_unset(self: CommandSet, ns: argparse.Namespace):
        """
        Set a variable key back to its default value
        """
        if self._cmd is None:
            return
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        s_id = ns.section_id
        opt_key = ns.option_key
        if cis is None:
            self._cmd.perror("[!] cis object is None")
            return
        if not cis.is_valid_section_id(s_id):
            self._cmd.perror("[!] Invalid section id")
            return
        if not cis.has_settable_vars(s_id):
            self._cmd.perror(f"[!] {s_id} has no unsettable variable")
            return
        if not cis.is_valid_option_key(s_id, opt_key):
            self._cmd.perror("[!] Invalid option key")
            return

        option = cis.sections[s_id]["vars"][opt_key]

        # node-level setting
        if ns.node_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.perror("[!] No inventory is loaded")
                self._cmd.perror("[!] Unable to set variable")
                return
            gname = ns.group_name
            nname = ns.node_name
            if gname is None:
                gname = "all"
            nodes: Dict[Text, InventoryNode] = inv.groups[gname].nodes
            if nname not in nodes.keys():
                self._cmd.perror("[!] Node name does not exist")
                return
            self._cmd.pfeedback(f"[+] Node: {nname} ({gname})")
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
            self._cmd.pfeedback(f"[+] {opt_key}:")
            self._cmd.pfeedback(f"    old: {old_value}")
            self._cmd.pfeedback(f"    default: {default}")
            return
        # group-level setting
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
            if gname == "all":
                self._cmd.perror(f"[!] {gname} is not unsettable")
                return
            group: InventoryGroup = inv.groups[gname]
            self._cmd.pfeedback(f"[+] Group: {gname}")
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
            self._cmd.pfeedback(f"[+] {opt_key}:")
            self._cmd.pfeedback(f"    old: {old_value}")
            self._cmd.pfeedback(f"    default: {default}")
            return
        # global-level setting
        else:
            old_value = cis.get_var(s_id, opt_key)
            cis.set_var(s_id, opt_key, None)
            self._cmd._cis_has_changed = True  # type: ignore[attr-defined]

            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            default = option["default"]
            if isinstance(default, TaggedScalar):
                default = vault.load(default)
            if old_value is None:
                old_value = ""
            if default is None:
                default = ""
            self._cmd.pfeedback(f"[+] {opt_key}:")
            self._cmd.pfeedback(f"    old: {old_value}")
            self._cmd.pfeedback(f"    default: {default}")
            return


@with_default_category("cis")
class cis_search_cmd(CommandSet):
    search_parser = Cmd2ArgumentParser()
    search_parser.add_argument("-i",
                               "--ignore-case",
                               dest="ignore_case",
                               action="store_true",
                               help="case insensitive")
    search_parser.add_argument("pattern",
                               help="pattern in regex format to be searched")

    @as_subcommand_to("cis", "search", search_parser,
                      help="search subcommand")
    def cis_search(self: CommandSet, ns: argparse.Namespace):
        """
        Search through CIS section title
        """
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore
        if cis is None:
            self._cmd.perror("[!] No CIS preset is loaded")
            return

        pattern = ns.pattern
        if ns.ignore_case:
            pattern = f"(?i){pattern}"
        data = cis.list_section_and_details(search_query=pattern)
        columns = [
            Column("Section ID", width=10),
            Column("Enabled", width=8),
            Column("Title", width=96),
        ]
        st = SimpleTable(columns)
        data_list = []
        for s_id, s in data:
            enabled = cis.get_enabled(s_id)
            data_list.append([s_id, enabled, s["title"]])

        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

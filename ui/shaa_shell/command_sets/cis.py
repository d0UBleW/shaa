from __future__ import annotations

import argparse
from cmd2 import (  # type: ignore[import]
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
    with_argparser,
    CompletionItem,
    CompletionError,
)
from cmd2.table_creator import SimpleTable, Column  # type: ignore[import]
from shaa_shell.utils.vault import vault
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.parser import cis_parser
from shaa_shell.utils.inventory import Inventory, InventoryGroup, InventoryNode
from typing import List, Text, Dict, Optional
from ruamel.yaml.comments import TaggedScalar


@with_default_category("cis")
class cis_cmd(CommandSet):
    @with_argparser(cis_parser)
    def do_cis(self: CommandSet, ns: argparse.Namespace):
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
    def _choices_cis_section_title(self) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        data = self._cmd._cis.list_section_and_details()  # type: ignore
        return [CompletionItem(s_id, s["title"]) for s_id, s in data]

    def _choices_cis_section_enable(self) -> List[CompletionItem]:
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
        if self._cmd is None:
            return []
        data = self._cmd._cis.list_section_and_details()  # type: ignore
        cmp = [CompletionItem(s_id, s["title"]) for s_id, s in data]
        cmp.append(CompletionItem("all", "Everything"))
        return cmp

    def cis_section_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]

        if cis is None:
            self._cmd.poutput("[!] No CIS preset is loaded")
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
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            self._cmd.poutput("[!] No CIS preset is loaded")
            return

        valid_s_id = [
            "all",
            "level_1_server",
            "level_2_server",
            "level_1_workstation",
            "level_2_workstation",
        ]

        for arg_s_id in ns.section_id:
            if arg_s_id not in valid_s_id:
                if not cis.is_valid_section_id(arg_s_id):
                    self._cmd.poutput("[!] Invalid section id")
                    return

            for s_id in cis.sections.keys():
                is_sub = CIS.is_subsection(arg_s_id, s_id)
                if not is_sub and arg_s_id not in valid_s_id:
                    continue
                if arg_s_id.startswith("level_"):
                    section = cis.sections[s_id]
                    if "profile" not in section.keys():
                        continue
                    s_profile = arg_s_id.replace("_", " ").title()
                    if s_profile not in section["profile"]:
                        continue
                    cis.set_enabled(s_id, True)
                    if ns.verbose:
                        self._cmd.poutput(f"[+] {s_id} enabled successfully")
                else:
                    cis.set_enabled(s_id, True)
                    if ns.verbose:
                        self._cmd.poutput(f"[+] {s_id} enabled successfully")
        self._cmd._cis_has_changed = True  # type: ignore[attr-defined]
        self._cmd.poutput("[+] Enabled successfully")

    def cis_section_disable(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            return

        for arg_s_id in ns.section_id:
            if arg_s_id != "all" and not cis.is_valid_section_id(arg_s_id):
                self._cmd.poutput(f"[!] Invalid section id: {arg_s_id}")
                return

            for s_id in cis.sections.keys():
                if CIS.is_subsection(arg_s_id, s_id) or arg_s_id == "all":
                    cis.set_enabled(s_id, False)
                    if ns.verbose:
                        self._cmd.poutput(f"[+] {s_id} disabled successfully")
        self._cmd._cis_has_changed = True  # type: ignore[attr-defined]
        self._cmd.poutput("[+] Disabled successfully")

    def cis_section_info(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        cis: CIS = self._cmd._cis  # type: ignore[attr-defined]
        if not cis.is_valid_section_id(ns.section_id):
            self._cmd.poutput("[!] Invalid section id")
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
                detail = f"{var['description']}\n"
                if var["value_type"] == "range" and "aide_" not in var_key:
                    if var["range_start"] is not None:
                        detail += f"Possible min value: {var['range_start']}\n"
                    if var["range_end"] is not None:
                        detail += f"Possible max value: {var['range_end']}\n"
                default_val = var["default"]
                if isinstance(default_val, list):
                    if isinstance(default_val[0], str):
                        default_val = "\n".join(
                            list(map(lambda v: f"- {v}", var["default"])))
                user_val = cis.get_var(ns.section_id, var_key)
                if isinstance(user_val, list):
                    if isinstance(user_val[0], str):
                        user_val = "\n".join(
                            list(map(lambda v: f"- {v}", var["value"])))
                if isinstance(user_val, TaggedScalar):
                    user_val = vault.load(user_val)
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
    info_parser.add_argument("section_id",
                             choices_provider=_choices_cis_section_title,
                             descriptive_header="Title",
                             help="section id whose details to be displayed")
    info_parser.set_defaults(func=cis_section_info)


@with_default_category("cis")
class cis_set_cmd(CommandSet):
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

    def _choices_cis_section_unit_and_title(self) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        data = self._cmd._cis.list_section_unit_and_details()  # type: ignore
        return [CompletionItem(s_id, s["title"]) for s_id, s in data]

    def _choices_cis_option_key(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            return []

        section_id = None
        if "section_id" in arg_tokens:
            section_id = arg_tokens["section_id"][0]

        if section_id is None:
            return []

        if not cis.has_settable_vars(section_id):
            raise CompletionError(f"[!] {section_id} has no settable variable")

        try:
            section_vars = cis.sections[section_id]["vars"]
        except KeyError:
            raise CompletionError(f"[!] Invalid section: {section_id}")

        cmp: List[CompletionItem] = []
        for var_key, var in section_vars.items():
            detail = f"{var['description']}"
            cmp.append(CompletionItem(var_key, detail))
        return cmp

    def _choices_cis_option_value(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        if self._cmd is None:
            return []
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            return []

        section_id = None
        if "section_id" in arg_tokens:
            section_id = arg_tokens["section_id"][0]

        if section_id is None:
            return []

        option_key = None
        if "option_key" in arg_tokens:
            option_key = arg_tokens["option_key"][0]

        if option_key is None:
            return []

        section_vars = cis.sections[section_id]["vars"]
        for var_key, var in section_vars.items():
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
            self._cmd.poutput("[!] cis object is None")
            return
        if not cis.is_valid_section_id(s_id):
            self._cmd.poutput("[!] Invalid section id")
            return
        if not cis.has_settable_vars(s_id):
            self._cmd.poutput(f"[!] {s_id} has no settable variable")
            return
        if not cis.is_valid_option_key(s_id, opt_key):
            self._cmd.poutput("[!] Invalid option key")
            return
        opt_val = cis.parse_option_val(s_id, opt_key, opt_val)
        if opt_val is None:
            self._cmd.poutput("[!] Invalid option value")
            return

        val = opt_val

        if ns.node_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.poutput("[!] No inventory is loaded")
                self._cmd.poutput("[!] Unable to set variable")
                return
            gname = ns.group_name
            nname = ns.node_name
            if gname is None:
                gname = "ungrouped"
            nodes: Dict[Text, InventoryNode] = inv.groups[gname].nodes
            if nname not in nodes.keys():
                self._cmd.poutput("[!] Node name does not exist")
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
            self._cmd.poutput(f"[+] Node: {nname} ({gname})")
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    new: {val}")
            return
        elif ns.group_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.poutput("[!] No inventory is loaded")
                self._cmd.poutput("[!] Unable to set variable")
                return
            gname = ns.group_name
            if gname not in inv.groups:
                self._cmd.poutput(f"[!] Group name not found: {gname}")
                return
            if gname == "ungrouped":
                self._cmd.poutput(f"[!] {gname} is not settable")
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
            self._cmd.poutput(f"[+] Group: {gname}")
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    new: {val}")
            return
        else:
            old_value = cis.get_var(s_id, opt_key)
            cis.set_var(s_id, opt_key, val)
            self._cmd._cis_has_changed = True  # type: ignore[attr-defined]
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            if isinstance(val, TaggedScalar):
                val = vault.load(val)
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    new: {val}")
            return

    @as_subcommand_to("cis", "unset", unset_parser,
                      help="set subcommand")
    def cis_unset(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        s_id = ns.section_id
        opt_key = ns.option_key
        if cis is None:
            self._cmd.poutput("[!] cis object is None")
            return
        if not cis.is_valid_section_id(s_id):
            self._cmd.poutput("[!] Invalid section id")
            return
        if not cis.has_settable_vars(s_id):
            self._cmd.poutput(f"[!] {s_id} has no unsettable variable")
            return
        if not cis.is_valid_option_key(s_id, opt_key):
            self._cmd.poutput("[!] Invalid option key")
            return

        option = cis.sections[s_id]["vars"][opt_key]

        if ns.node_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.poutput("[!] No inventory is loaded")
                self._cmd.poutput("[!] Unable to set variable")
                return
            gname = ns.group_name
            nname = ns.node_name
            if gname is None:
                gname = "ungrouped"
            nodes: Dict[Text, InventoryNode] = inv.groups[gname].nodes
            if nname not in nodes.keys():
                self._cmd.poutput("[!] Node name does not exist")
                return
            self._cmd.poutput(f"[+] Node: {nname} ({gname})")
            node = nodes[nname]
            old_value = None
            if opt_key in node.host_vars:
                old_value = node.host_vars[opt_key]
                del node.host_vars[opt_key]
                self._cmd._inv_has_changed = True  # type: ignore[attr-defined]
            else:
                self._cmd.poutput("[!] Option key not found")
                return
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            default = option["default"]
            if isinstance(default, TaggedScalar):
                default = vault.load(default)
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    default: {default}")
            return
        elif ns.group_name is not None:
            inv: Inventory = self._cmd._inventory  # type: ignore
            if inv is None:
                self._cmd.poutput(
                    "[!] No inventory is loaded")
                self._cmd.poutput(
                    "[!] Unable to unset variable on this group name")
                return
            gname = ns.group_name
            if gname not in inv.groups:
                self._cmd.poutput(f"[!] Group name not found: {gname}")
                return
            if gname == "ungrouped":
                self._cmd.poutput(f"[!] {gname} is not unsettable")
                return
            group: InventoryGroup = inv.groups[gname]
            self._cmd.poutput(f"[+] Group: {gname}")
            if opt_key in group.group_vars:
                old_value = group.group_vars[opt_key]
                del group.group_vars[opt_key]
                self._cmd._inv_has_changed = True  # type: ignore
            else:
                self._cmd.poutput("[!] Option key not found")
                return
            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            default = option["default"]
            if isinstance(default, TaggedScalar):
                default = vault.load(default)
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    default: {default}")
            return
        else:
            old_value = cis.get_var(s_id, opt_key)
            default_val = option["default"]
            cis.set_var(s_id, opt_key, default_val)
            self._cmd._cis_has_changed = True  # type: ignore[attr-defined]

            if isinstance(old_value, TaggedScalar):
                old_value = vault.load(old_value)
            default = option["default"]
            if isinstance(default, TaggedScalar):
                default = vault.load(default)
            self._cmd.poutput(f"[+] {opt_key}:")
            self._cmd.poutput(f"    old: {old_value}")
            self._cmd.poutput(f"    default: {default}")
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
        if self._cmd is None:
            return
        pattern = ns.pattern
        if ns.ignore_case:
            pattern = f"(?i){pattern}"
        data = self._cmd._cis.list_section_and_details(search_query=pattern)  # type: ignore  # noqa: E501
        columns = [
            Column("Section ID", width=10),
            Column("Enabled", width=8),
            Column("Title", width=96),
        ]
        st = SimpleTable(columns)
        data_list = []
        for s_id, s in data:
            data_list.append([s_id, s["enabled"], s["title"]])

        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

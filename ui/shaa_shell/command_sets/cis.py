from __future__ import annotations

import argparse
from cmd2 import (  # type: ignore[import]
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
    with_argparser,
    CompletionItem,
)
from cmd2.table_creator import SimpleTable, Column  # type: ignore[import]
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.parser import cis_parser
from typing import List, Text, Dict, Optional


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

    def cis_section_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        data = self._cmd._cis.list_section_and_details(  # type: ignore
            ns.section_id)
        columns = [
            Column("Section ID", width=10),
            Column("Enabled", width=8),
            Column("Title", width=96),
        ]
        st = SimpleTable(columns)
        data_list = []
        for s_id, s in data:
            if ns.status == "all":
                data_list.append([s_id, s["enabled"], s["title"]])
                continue
            if ns.status == "enabled" and s["enabled"]:
                data_list.append([s_id, s["enabled"], s["title"]])
                continue
            if ns.status == "disabled" and not s["enabled"]:
                data_list.append([s_id, s["enabled"], s["title"]])

        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    def cis_section_enable(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            return

        arg_s_id = ns.section_id

        if arg_s_id != "all" and not cis.is_valid_section_id(arg_s_id):
            self._cmd.poutput("[!] Invalid section id")
            return

        for s_id in cis.sections.keys():
            if CIS.is_subsection(arg_s_id, s_id) or arg_s_id == "all":
                cis.sections[s_id]["enabled"] = True
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

        arg_s_id = ns.section_id

        if arg_s_id != "all" and not cis.is_valid_section_id(arg_s_id):
            self._cmd.poutput("[!] Invalid section id")
            return

        for s_id in cis.sections.keys():
            if CIS.is_subsection(arg_s_id, s_id) or arg_s_id == "all":
                cis.sections[s_id]["enabled"] = False
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
            if key == "enabled":
                value = bool(value)
            data_list.append([key, value])
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
                user_val = var["value"]
                if isinstance(user_val, list):
                    if isinstance(user_val[0], str):
                        user_val = "\n".join(
                            list(map(lambda v: f"- {v}", var["value"])))
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
        choices_provider=_choices_cis_section_title,
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
        choices_provider=_choices_cis_section_title,
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
    def _choices_cis_section_unit_and_title(self) -> List[CompletionItem]:
        if self._cmd is None:
            return []
        data = self._cmd._cis.list_section_and_details()  # type: ignore
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
        if not cis.is_valid_option_key(s_id, opt_key):
            self._cmd.poutput("[!] Invalid option key")
            return
        if not cis.is_valid_option_val(s_id, opt_key, opt_val):
            self._cmd.poutput("[!] Invalid option value")
            return
        option = cis.sections[s_id]["vars"][opt_key]
        if option["value_type"] != "list_choice":
            val = opt_val[0]
        else:
            val = list(set(opt_val))
        old_value = option["value"]
        option["value"] = val
        self._cmd.poutput(f"[+] {opt_key}:")
        self._cmd.poutput(f"    old: {old_value}")
        self._cmd.poutput(f"    new: {val}")
        self._cmd._cis_has_changed = True  # type: ignore[attr-defined]

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
        if not cis.is_valid_option_key(s_id, opt_key):
            self._cmd.poutput("[!] Invalid option key")
            return
        option = cis.sections[s_id]["vars"][opt_key]
        old_value = option["value"]
        default_val = option["default"]
        option["value"] = default_val
        self._cmd.poutput(f"[+] {opt_key}:")
        self._cmd.poutput(f"    old: {old_value}")
        self._cmd.poutput(f"    new: {option['value']}")
        self._cmd._cis_has_changed = True  # type: ignore[attr-defined]


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

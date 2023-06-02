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
            if not s["enabled"]:
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
                Column("Key", width=32),
                Column("Value", width=32),
                Column("Default", width=32),
                Column("Description", width=64),
            ]
            vars_st = SimpleTable(vars_columns)
            vars_data_list = []
            for var_key, var_value in section["vars"].items():
                vars_data_list.append([
                    var_key,
                    var_value["value"],
                    var_value["default"],
                    var_value["description"],
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

    def _choices_cis_option(
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

        section_vars = cis.sections[section_id]["vars"]
        return section_vars.keys()

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
                            choices_provider=_choices_cis_option,
                            help="name of option to be set")
    set_parser.add_argument("option_value",
                            help="new option value")

    @as_subcommand_to("cis", "set", set_parser,
                      help="set subcommand")
    def cis_set(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            self._cmd.poutput("[!] cis object is non")
            return
        if not cis.is_valid_section_id(ns.section_id):
            self._cmd.poutput("[!] Invalid section id")
            return
        if not cis.is_valid_option(ns.section_id, ns.option_key):
            self._cmd.poutput("[!] Invalid option key")
            return
        option = cis.sections[ns.section_id]["vars"][ns.option_key]
        old_value = option["value"]
        option["value"] = ns.option_value
        self._cmd.poutput(f"[+] {ns.option_key}:")
        self._cmd.poutput(f"    old: {old_value}")
        self._cmd.poutput(f"    new: {ns.option_value}")
        self._cmd._cis_has_changed = True  # type: ignore[attr-defined]


@with_default_category("cis")
class cis_search_cmd(CommandSet):
    search_parser = Cmd2ArgumentParser()
    search_parser.add_argument("pattern",
                               help="pattern in regex format to be searched")

    @as_subcommand_to("cis", "search", search_parser,
                      help="search subcommand")
    def cis_search(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.poutput(f"search {ns.pattern}")

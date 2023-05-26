#!/usr/bin/env python3

import argparse
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
    with_argparser,
)
from cmd2.table_creator import SimpleTable, Column
from utils.cis import CIS
from utils.parser import cis_parser
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
    def _choices_cis_section(self) -> List[Text]:
        if self._cmd is None:
            return []
        return self._cmd._cis.list_section()  # type: ignore[attr-defined]

    def cis_section_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.poutput("list")

    def cis_section_enable(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.poutput(f"enable {ns.section_id}")

    def cis_section_disable(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.poutput(f"disable {ns.section_id}")

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
        "section_id",
        nargs="?",
        help="""if specified, it would list out corresponding subsections \
(e.g., 1, 2.1, 3.3.1)"""
    )
    list_parser.set_defaults(func=cis_section_list)

    enable_parser = section_subparser.add_parser(
        "enable", help="enable section id")
    enable_parser.add_argument("section_id",
                               choices_provider=_choices_cis_section,
                               help="section id to be enabled")
    enable_parser.set_defaults(func=cis_section_enable)

    disable_parser = section_subparser.add_parser(
        "disable", help="disable section id")
    disable_parser.add_argument("section_id",
                                choices_provider=_choices_cis_section,
                                help="section id to be disabled")
    disable_parser.set_defaults(func=cis_section_disable)

    info_parser = section_subparser.add_parser(
        "info", help="info section id")
    info_parser.add_argument("section_id",
                             choices_provider=_choices_cis_section,
                             help="section id whose details to be displayed")
    info_parser.set_defaults(func=cis_section_info)


@with_default_category("cis")
class cis_set_cmd(CommandSet):
    def _choices_cis_section(self: CommandSet) -> List[Text]:
        if self._cmd is None:
            return []
        return self._cmd._cis.list_section()  # type: ignore[attr-defined]

    def _choices_cis_section_unit(self: CommandSet) -> List[Text]:
        if self._cmd is None:
            return []
        return self._cmd._cis.list_section_unit()  # type: ignore[attr-defined]

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
        choices_provider=_choices_cis_section_unit,
        help="narrow down to specific section id for better tab completion"
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

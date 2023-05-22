#!/usr/bin/env python3

import argparse
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
)
from utils import cis
from typing import List, Text


@with_default_category("cis")
class cis_section_cmd(CommandSet):
    def _choices_cis_section(self) -> List[Text]:
        return cis.list_section()

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
        self._cmd.poutput(f"info {ns.section_id}")

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
    set_parser = Cmd2ArgumentParser()
    set_parser.add_argument("option_key",
                            help="name of option to be set")
    set_parser.add_argument("option_value",
                            help="new option value")

    @as_subcommand_to("cis", "set", set_parser,
                      help="set subcommand")
    def cis_set(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.poutput(f"set {ns.option_key} {ns.option_value}")


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

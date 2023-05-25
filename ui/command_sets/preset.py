#!/usr/bin/env python3

import argparse
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
)
from cmd2.exceptions import CommandSetRegistrationError
from typing import List, Text, Optional
from utils import preset
from utils.cis import CIS


@with_default_category("preset")
class preset_cis_cmd(CommandSet):
    def _choices_preset_cis(self) -> List[Text]:
        return preset.list_preset("cis")

    def preset_cis_load(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        cis: Optional[CIS] = CIS.load(ns.name)

        if cis is None:
            return

        self._cmd._cis = cis  # type: ignore[attr-defined]
        try:
            self._cmd.register_command_set(
                self._cmd._cis_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] cis module loaded")
            self._cmd.poutput("[*] check `help cis` for usage information")

            self._cmd.register_command_set(
                self._cmd._cis_section_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] cis section module loaded")
            self._cmd.poutput(
                "[*] check `help cis section` for usage information")

            self._cmd.register_command_set(
                self._cmd._cis_set_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] cis set module loaded")
            self._cmd.poutput("[*] check `help cis set` for usage information")

            self._cmd.register_command_set(
                self._cmd._cis_search_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] cis search module loaded")
            self._cmd.poutput(
                "[*] check `help cis search` for usage information")

        except CommandSetRegistrationError:
            return

    pre_cis_parser = Cmd2ArgumentParser()
    pre_cis_subparser = pre_cis_parser.add_subparsers(
        title="subcommand", help="subcommand for preset cis")

    @as_subcommand_to("preset", "cis", pre_cis_parser,
                      help="cis subcommand")
    def preset_cis(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        func = getattr(ns, "func", None)
        if func is not None:
            func(self, ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("preset cis")

    load_parser = pre_cis_subparser.add_parser("load", help="load CIS preset")
    load_parser.add_argument("name",
                             choices_provider=_choices_preset_cis,
                             help="name of CIS preset")
    load_parser.set_defaults(func=preset_cis_load)

#!/usr/bin/env python3

import argparse
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
)
from cmd2.table_creator import SimpleTable, Column
from cmd2.exceptions import CommandSetRegistrationError
from typing import List, Text, Optional
from utils.cis import CIS


@with_default_category("preset")
class preset_cis_cmd(CommandSet):
    def _choices_preset_cis(self) -> List[Text]:
        return CIS.list_preset()

    def preset_cis_list(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        data_list = []
        for pre in CIS.list_preset(ns.pattern):
            data_list.append([pre])

        columns = [
            Column("Name", width=32),
        ]
        st = SimpleTable(columns)
        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    def preset_cis_create(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        cis: Optional[CIS] = CIS.create(ns.name)
        if cis is None:
            warning_text = "[!] Invalid name or specified CIS preset name"
            warning_text += "already existed"
            self._cmd.poutput(warning_text)
            return
        self._cmd._cis = cis  # type: ignore[attr-defined]
        return self.preset_cis_load(argparse.Namespace(), cis)

    def preset_cis_save(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            self._cmd.poutput("[!] Currently, there is no CIS preset loaded")
            return
        if not cis.save(ns.name):
            self._cmd.poutput("[!] Invalid CIS preset name")
            return
        self._cmd._cis_has_changed = False  # type: ignore[attr-defined]
        self._cmd.poutput("[+] CIS preset has been saved")

    def preset_cis_unload(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.check_if_cis_changed()  # type: ignore[attr-defined]
        self._cmd._cis = None  # type: ignore[attr-defined]

        self._cmd.unregister_command_set(
            self._cmd._cis_section_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis section module loaded")

        self._cmd.unregister_command_set(
            self._cmd._cis_set_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis set module loaded")

        self._cmd.unregister_command_set(
            self._cmd._cis_search_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis search module loaded")

        self._cmd.unregister_command_set(
            self._cmd._cis_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis module unloaded")

    def preset_cis_load(self, ns: argparse.Namespace,
                        cis: Optional[CIS] = None):
        if self._cmd is None:
            return

        self._cmd.check_if_cis_changed()  # type: ignore[attr-defined]

        if cis is None:
            cis = CIS.load(ns.name)
            self._cmd._cis = cis  # type: ignore[attr-defined]

        if cis is None:
            return

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

    unload_parser = pre_cis_subparser.add_parser("unload",
                                                 help="unload CIS preset")
    unload_parser.set_defaults(func=preset_cis_unload)

    create_parser = pre_cis_subparser.add_parser("create",
                                                 help="create CIS preset")
    create_parser.add_argument("name", help="name of inventory")
    create_parser.set_defaults(func=preset_cis_create)

    save_parser = pre_cis_subparser.add_parser("save", help="save CIS preset")
    save_parser.add_argument("name",
                             nargs="?",
                             help="name of CIS preset")
    save_parser.set_defaults(func=preset_cis_save)

    list_parser = pre_cis_subparser.add_parser(
        "list", help="list available CIS preset")
    list_parser.add_argument("pattern",
                             nargs="?",
                             default=".*",
                             help="preset name regex pattern")
    list_parser.set_defaults(func=preset_cis_list)

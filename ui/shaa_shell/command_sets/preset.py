from __future__ import annotations

import argparse
from typing import List, Optional, Text

from cmd2 import (Cmd2ArgumentParser, CommandSet, as_subcommand_to,
                  with_default_category)
from cmd2.exceptions import CommandSetRegistrationError
from cmd2.table_creator import Column, SimpleTable

from shaa_shell.utils import exception
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.preset import list_preset
from shaa_shell.utils.profile import Profile
from shaa_shell.utils.role import Role


@with_default_category("preset")
class preset_sec_tools_cmd(CommandSet):
    def _choices_preset_sec_tools(self) -> List[Text]:
        return list_preset("sec_tools")

    def preset_sec_tools_list(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        data_list = []
        for pre in list_preset("sec_tools", ns.pattern):
            data_list.append([pre])

        columns = [
            Column("Name", width=32),
        ]

        st = SimpleTable(columns)
        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    def preset_sec_tools_create(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        try:
            role_sec_tools: Optional[Role] = Role.create("sec_tools", ns.name)
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._sec_tools = role_sec_tools  # type: ignore[attr-defined]
        return self.preset_sec_tools_load(argparse.Namespace(), role_sec_tools)

    def preset_sec_tools_save(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_sec_tools: Optional[Role] = self._cmd._sec_tools  # type: ignore
        if role_sec_tools is None:
            self._cmd.perror(
                "[!] Currently, there is no sec_tools preset loaded")
            return
        try:
            if not role_sec_tools.save(ns.name):
                self._cmd.perror("[!] Unable to save")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd._sec_tools_has_changed = False  # type: ignore[attr-defined]
        self._cmd.poutput("[+] sec_tools preset has been saved")

    def preset_sec_tools_rename(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_sec_tools: Optional[Role] = self._cmd._sec_tools  # type: ignore
        if role_sec_tools is None:
            self._cmd.perror(
                "[!] Currently, there is no sec_tools preset loaded")
            return
        old_name = role_sec_tools.name
        try:
            if not role_sec_tools.rename(ns.name):
                self._cmd.perror("[!] Unable to rename")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd._sec_tools_has_changed = False  # type: ignore[attr-defined]
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is not None:
            profile.presets["sec_tools"] = role_sec_tools.name
            self._cmd._profile_has_changed = True  # type: ignore[attr-defined]

        self._cmd.poutput("[+] sec_tools preset has been renamed")
        self._cmd.poutput(f"    old: {old_name}")
        self._cmd.poutput(f"    new: {role_sec_tools.name}")

    def preset_sec_tools_delete(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_sec_tools: Optional[Role] = self._cmd._sec_tools  # type: ignore
        if role_sec_tools is None:
            self._cmd.perror(
                "[!] Currently, there is no sec_tools preset loaded")
            return
        role_sec_tools.delete()
        self._cmd.poutput("[+] sec_tools preset has been deleted successfully")
        self._cmd._sec_tools_has_changed = False  # type: ignore[attr-defined]
        self.preset_sec_tools_unload(None)

    def preset_sec_tools_unload(self, _):
        if self._cmd is None:
            return
        self._cmd.check_if_sec_tools_changed()  # type: ignore[attr-defined]
        self._cmd._sec_tools = None  # type: ignore[attr-defined]

        self._cmd.unregister_command_set(
            self._cmd._sec_tools_action_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] sec_tools action module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._sec_tools_set_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] sec_tools set module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._sec_tools_search_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] sec_tools search module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._sec_tools_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] sec_tools module unloaded")
        self._cmd._sec_tools_has_changed = False  # type: ignore[attr-defined]

    def preset_sec_tools_load(self, ns: argparse.Namespace,
                              role_sec_tools: Optional[Role] = None):
        if self._cmd is None:
            return

        self._cmd.check_if_sec_tools_changed()  # type: ignore[attr-defined]

        if role_sec_tools is not None:
            self._cmd._sec_tools_has_changed = True  # type: ignore
        else:
            self._cmd._sec_tools_has_changed = False  # type: ignore

        if role_sec_tools is None:
            try:
                role_sec_tools = Role.load("sec_tools", ns.name)
            except exception.ShaaNameError as ex:
                self._cmd.perror(f"[!] {ex}")
                return
            self._cmd._sec_tools = role_sec_tools  # type: ignore[attr-defined]

        if role_sec_tools is None:
            return

        try:
            self._cmd.register_command_set(
                self._cmd._sec_tools_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] sec_tools module loaded")
            self._cmd.poutput(
                "[*] check `help sec_tools` for usage information")

            self._cmd.register_command_set(
                self._cmd._sec_tools_action_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] sec_tools action module loaded")
            self._cmd.poutput(
                "[*] check `help sec_tools action` for usage information")

            self._cmd.register_command_set(
                self._cmd._sec_tools_set_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] sec_tools set module loaded")
            self._cmd.poutput(
                "[*] check `help sec_tools set` for usage information")

            self._cmd.register_command_set(
                self._cmd._sec_tools_search_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] sec_tools search module loaded")
            self._cmd.poutput(
                "[*] check `help sec_tools search` for usage information")

        except CommandSetRegistrationError:
            return

    pre_sec_tools_parser = Cmd2ArgumentParser()
    pre_sec_tools_subparser = pre_sec_tools_parser.add_subparsers(
        title="subcommand", help="subcommand for preset sec_tools")

    @as_subcommand_to("preset", "sec_tools", pre_sec_tools_parser,
                      help="sec_tools subcommand")
    def preset_sec_tools(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        func = getattr(ns, "func", None)
        if func is not None:
            func(self, ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("preset sec_tools")

    load_parser = pre_sec_tools_subparser.add_parser(
        "load", help="load sec_tools preset")
    load_parser.add_argument("name",
                             choices_provider=_choices_preset_sec_tools,
                             help="name of sec_tools preset")
    load_parser.set_defaults(func=preset_sec_tools_load)

    unload_parser = pre_sec_tools_subparser.add_parser(
        "unload", help="unload sec_tools preset")
    unload_parser.set_defaults(func=preset_sec_tools_unload)

    create_parser = pre_sec_tools_subparser.add_parser(
        "create", help="create sec_tools preset")
    create_parser.add_argument("name", help="name of sec_tools preset")
    create_parser.set_defaults(func=preset_sec_tools_create)

    save_parser = pre_sec_tools_subparser.add_parser(
        "save", help="save sec_tools preset")
    save_parser.add_argument("name",
                             nargs="?",
                             help="name of sec_tools preset")
    save_parser.set_defaults(func=preset_sec_tools_save)

    list_parser = pre_sec_tools_subparser.add_parser(
        "list", help="list available sec_tools preset")
    list_parser.add_argument("pattern",
                             nargs="?",
                             default=".*",
                             help="preset name regex pattern")
    list_parser.set_defaults(func=preset_sec_tools_list)

    delete_parser = pre_sec_tools_subparser.add_parser(
        "delete", help="delete sec_tools preset")
    delete_parser.set_defaults(func=preset_sec_tools_delete)

    rename_parser = pre_sec_tools_subparser.add_parser(
        "rename", help="""rename sec_tools preset (save current changes \
automatically)""")
    rename_parser.add_argument("name",
                               help="new name of sec_tools preset")
    rename_parser.set_defaults(func=preset_sec_tools_rename)


@with_default_category("preset")
class preset_oscap_cmd(CommandSet):
    def _choices_preset_oscap(self) -> List[Text]:
        return list_preset("oscap")

    def preset_oscap_list(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        data_list = []
        for pre in list_preset("oscap", ns.pattern):
            data_list.append([pre])

        columns = [
            Column("Name", width=32),
        ]

        st = SimpleTable(columns)
        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    def preset_oscap_create(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        try:
            role_oscap: Optional[Role] = Role.create("oscap", ns.name)
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._oscap = role_oscap  # type: ignore[attr-defined]
        return self.preset_oscap_load(argparse.Namespace(), role_oscap)

    def preset_oscap_save(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_oscap: Optional[Role] = self._cmd._oscap  # type: ignore
        if role_oscap is None:
            self._cmd.perror("[!] Currently, there is no oscap preset loaded")
            return
        try:
            if not role_oscap.save(ns.name):
                self._cmd.perror("[!] Unable to save")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd._oscap_has_changed = False  # type: ignore[attr-defined]
        self._cmd.poutput("[+] oscap preset has been saved")

    def preset_oscap_rename(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_oscap: Optional[Role] = self._cmd._oscap  # type: ignore
        if role_oscap is None:
            self._cmd.perror("[!] Currently, there is no oscap preset loaded")
            return
        old_name = role_oscap.name
        try:
            if not role_oscap.rename(ns.name):
                self._cmd.perror("[!] Unable to rename")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd._oscap_has_changed = False  # type: ignore[attr-defined]
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is not None:
            profile.presets["oscap"] = role_oscap.name
            self._cmd._profile_has_changed = True  # type: ignore[attr-defined]

        self._cmd.poutput("[+] oscap preset has been renamed")
        self._cmd.poutput(f"    old: {old_name}")
        self._cmd.poutput(f"    new: {role_oscap.name}")

    def preset_oscap_delete(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_oscap: Optional[Role] = self._cmd._oscap  # type: ignore
        if role_oscap is None:
            self._cmd.perror("[!] Currently, there is no oscap preset loaded")
            return
        role_oscap.delete()
        self._cmd.poutput("[+] oscap preset has been deleted successfully")
        self._cmd._oscap_has_changed = False  # type: ignore[attr-defined]
        self.preset_oscap_unload(None)

    def preset_oscap_unload(self, _):
        if self._cmd is None:
            return
        self._cmd.check_if_oscap_changed()  # type: ignore[attr-defined]
        self._cmd._oscap = None  # type: ignore[attr-defined]

        self._cmd.unregister_command_set(
            self._cmd._oscap_action_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] oscap action module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._oscap_set_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] oscap set module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._oscap_search_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] oscap search module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._oscap_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] oscap module unloaded")
        self._cmd._oscap_has_changed = False  # type: ignore[attr-defined]

    def preset_oscap_load(self, ns: argparse.Namespace,
                          role_oscap: Optional[Role] = None):
        if self._cmd is None:
            return

        self._cmd.check_if_oscap_changed()  # type: ignore[attr-defined]

        if role_oscap is not None:
            self._cmd._oscap_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd._oscap_has_changed = False  # type: ignore[attr-defined]

        if role_oscap is None:
            try:
                role_oscap = Role.load("oscap", ns.name)
            except exception.ShaaNameError as ex:
                self._cmd.perror(f"[!] {ex}")
                return
            self._cmd._oscap = role_oscap  # type: ignore[attr-defined]

        if role_oscap is None:
            return

        try:
            self._cmd.register_command_set(
                self._cmd._oscap_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] oscap module loaded")
            self._cmd.poutput("[*] check `help oscap` for usage information")

            self._cmd.register_command_set(
                self._cmd._oscap_action_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] oscap action module loaded")
            self._cmd.poutput(
                "[*] check `help oscap action` for usage information")

            self._cmd.register_command_set(
                self._cmd._oscap_set_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] oscap set module loaded")
            self._cmd.poutput(
                "[*] check `help oscap set` for usage information")

            self._cmd.register_command_set(
                self._cmd._oscap_search_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] oscap search module loaded")
            self._cmd.poutput(
                "[*] check `help oscap search` for usage information")

        except CommandSetRegistrationError:
            return

    pre_oscap_parser = Cmd2ArgumentParser()
    pre_oscap_subparser = pre_oscap_parser.add_subparsers(
        title="subcommand", help="subcommand for preset oscap")

    @as_subcommand_to("preset", "oscap", pre_oscap_parser,
                      help="oscap subcommand")
    def preset_oscap(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        func = getattr(ns, "func", None)
        if func is not None:
            func(self, ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("preset oscap")

    load_parser = pre_oscap_subparser.add_parser(
        "load", help="load oscap preset")
    load_parser.add_argument("name",
                             choices_provider=_choices_preset_oscap,
                             help="name of oscap preset")
    load_parser.set_defaults(func=preset_oscap_load)

    unload_parser = pre_oscap_subparser.add_parser("unload",
                                                   help="unload oscap preset")
    unload_parser.set_defaults(func=preset_oscap_unload)

    create_parser = pre_oscap_subparser.add_parser("create",
                                                   help="create oscap preset")
    create_parser.add_argument("name", help="name of oscap preset")
    create_parser.set_defaults(func=preset_oscap_create)

    save_parser = pre_oscap_subparser.add_parser(
        "save", help="save oscap preset")
    save_parser.add_argument("name",
                             nargs="?",
                             help="name of oscap preset")
    save_parser.set_defaults(func=preset_oscap_save)

    list_parser = pre_oscap_subparser.add_parser(
        "list", help="list available oscap preset")
    list_parser.add_argument("pattern",
                             nargs="?",
                             default=".*",
                             help="preset name regex pattern")
    list_parser.set_defaults(func=preset_oscap_list)

    delete_parser = pre_oscap_subparser.add_parser(
        "delete", help="delete oscap preset")
    delete_parser.set_defaults(func=preset_oscap_delete)

    rename_parser = pre_oscap_subparser.add_parser(
        "rename", help="""rename oscap preset (save current changes \
automatically)""")
    rename_parser.add_argument("name",
                               help="new name of oscap preset")
    rename_parser.set_defaults(func=preset_oscap_rename)


@with_default_category("preset")
class preset_util_cmd(CommandSet):
    def _choices_preset_util(self) -> List[Text]:
        return list_preset("util")

    def preset_util_list(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        data_list = []
        for pre in list_preset("util", ns.pattern):
            data_list.append([pre])

        columns = [
            Column("Name", width=32),
        ]

        st = SimpleTable(columns)
        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    def preset_util_create(self, ns: argparse.Namespace):
        if self._cmd is None:
            return
        try:
            role_util: Optional[Role] = Role.create("util", ns.name)
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._util = role_util  # type: ignore[attr-defined]
        return self.preset_util_load(argparse.Namespace(), role_util)

    def preset_util_save(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            self._cmd.perror("[!] Currently, there is no util preset loaded")
            return
        try:
            if not role_util.save(ns.name):
                self._cmd.perror("[!] Unable to save")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._util_has_changed = False  # type: ignore[attr-defined]
        self._cmd.poutput("[+] util preset has been saved")

    def preset_util_rename(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            self._cmd.perror("[!] Currently, there is no util preset loaded")
            return
        old_name = role_util.name
        try:
            if not role_util.rename(ns.name):
                self._cmd.perror("[!] Unable to rename")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd._util_has_changed = False  # type: ignore[attr-defined]
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is not None:
            profile.presets["util"] = role_util.name
            self._cmd._profile_has_changed = True  # type: ignore[attr-defined]

        self._cmd.poutput("[+] util preset has been renamed")
        self._cmd.poutput(f"    old: {old_name}")
        self._cmd.poutput(f"    new: {role_util.name}")

    def preset_util_delete(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is None:
            self._cmd.perror("[!] Currently, there is no util preset loaded")
            return
        role_util.delete()
        self._cmd.poutput("[+] util preset has been deleted successfully")
        self._cmd._util_has_changed = False  # type: ignore[attr-defined]
        self.preset_util_unload(None)

    def preset_util_unload(self, _):
        if self._cmd is None:
            return
        self._cmd.check_if_util_changed()  # type: ignore[attr-defined]
        self._cmd._util = None  # type: ignore[attr-defined]

        self._cmd.unregister_command_set(
            self._cmd._util_action_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] util action module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._util_set_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] util set module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._util_search_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] util search module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._util_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] util module unloaded")
        self._cmd._util_has_changed = False  # type: ignore[attr-defined]

    def preset_util_load(self, ns: argparse.Namespace,
                         role_util: Optional[Role] = None):
        if self._cmd is None:
            return

        self._cmd.check_if_util_changed()  # type: ignore[attr-defined]

        if role_util is not None:
            self._cmd._util_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd._util_has_changed = False  # type: ignore[attr-defined]

        if role_util is None:
            try:
                role_util = Role.load("util", ns.name)
            except exception.ShaaNameError as ex:
                self._cmd.perror(f"[!] {ex}")
                return
            self._cmd._util = role_util  # type: ignore[attr-defined]

        if role_util is None:
            return

        try:
            self._cmd.register_command_set(
                self._cmd._util_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] util module loaded")
            self._cmd.poutput("[*] check `help util` for usage information")

            self._cmd.register_command_set(
                self._cmd._util_action_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] util action module loaded")
            self._cmd.poutput(
                "[*] check `help util action` for usage information")

            self._cmd.register_command_set(
                self._cmd._util_set_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] util set module loaded")
            self._cmd.poutput(
                "[*] check `help util set` for usage information")

            self._cmd.register_command_set(
                self._cmd._util_search_cmd  # type: ignore[attr-defined]
            )
            self._cmd.poutput("[*] util search module loaded")
            self._cmd.poutput(
                "[*] check `help util search` for usage information")

        except CommandSetRegistrationError:
            return

    pre_util_parser = Cmd2ArgumentParser()
    pre_util_subparser = pre_util_parser.add_subparsers(
        title="subcommand", help="subcommand for preset util")

    @as_subcommand_to("preset", "util", pre_util_parser,
                      help="util subcommand")
    def preset_util(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        func = getattr(ns, "func", None)
        if func is not None:
            func(self, ns)
        else:
            self._cmd.poutput("No subcommand was provided")
            self._cmd.do_help("preset util")

    load_parser = pre_util_subparser.add_parser(
        "load", help="load util preset")
    load_parser.add_argument("name",
                             choices_provider=_choices_preset_util,
                             help="name of util preset")
    load_parser.set_defaults(func=preset_util_load)

    unload_parser = pre_util_subparser.add_parser("unload",
                                                  help="unload util preset")
    unload_parser.set_defaults(func=preset_util_unload)

    create_parser = pre_util_subparser.add_parser("create",
                                                  help="create util preset")
    create_parser.add_argument("name", help="name of util preset")
    create_parser.set_defaults(func=preset_util_create)

    save_parser = pre_util_subparser.add_parser(
        "save", help="save util preset")
    save_parser.add_argument("name",
                             nargs="?",
                             help="name of util preset")
    save_parser.set_defaults(func=preset_util_save)

    list_parser = pre_util_subparser.add_parser(
        "list", help="list available util preset")
    list_parser.add_argument("pattern",
                             nargs="?",
                             default=".*",
                             help="preset name regex pattern")
    list_parser.set_defaults(func=preset_util_list)

    delete_parser = pre_util_subparser.add_parser(
        "delete", help="delete util preset")
    delete_parser.set_defaults(func=preset_util_delete)

    rename_parser = pre_util_subparser.add_parser(
        "rename", help="""rename util preset (save current changes \
automatically)""")
    rename_parser.add_argument("name",
                               help="new name of util preset")
    rename_parser.set_defaults(func=preset_util_rename)


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
        try:
            cis: Optional[CIS] = CIS.create(ns.name)
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._cis = cis  # type: ignore[attr-defined]
        return self.preset_cis_load(argparse.Namespace(), cis)

    def preset_cis_save(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            self._cmd.perror("[!] Currently, there is no CIS preset loaded")
            return
        try:
            if not cis.save(ns.name):
                self._cmd.perror("[!] Unable to save")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd._cis_has_changed = False  # type: ignore[attr-defined]
        self._cmd.poutput("[+] CIS preset has been saved")

    def preset_cis_rename(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            self._cmd.perror("[!] Currently, there is no CIS preset loaded")
            return
        old_name = cis.name
        try:
            if not cis.rename(ns.name):
                self._cmd.perror("[!] Unable to rename")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd._cis_has_changed = False  # type: ignore[attr-defined]
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is not None:
            profile.presets["cis"] = cis.name
            self._cmd._profile_has_changed = True  # type: ignore[attr-defined]

        self._cmd.poutput("[+] CIS preset has been renamed")
        self._cmd.poutput(f"    old: {old_name}")
        self._cmd.poutput(f"    new: {cis.name}")

    def preset_cis_delete(self, ns: argparse.Namespace):
        if self._cmd is None:
            return

        cis: Optional[CIS] = self._cmd._cis  # type: ignore[attr-defined]
        if cis is None:
            self._cmd.perror("[!] Currently, there is no CIS preset loaded")
            return
        cis.delete()
        self._cmd.poutput("[+] CIS preset has been deleted successfully")
        self._cmd._cis_has_changed = False  # type: ignore[attr-defined]
        self.preset_cis_unload(None)

    def preset_cis_unload(self, _):
        if self._cmd is None:
            return
        self._cmd.check_if_cis_changed()  # type: ignore[attr-defined]
        self._cmd._cis = None  # type: ignore[attr-defined]

        self._cmd.unregister_command_set(
            self._cmd._cis_section_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis section module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._cis_set_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis set module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._cis_search_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis search module unloaded")

        self._cmd.unregister_command_set(
            self._cmd._cis_cmd  # type: ignore[attr-defined]
        )
        self._cmd.poutput("[*] cis module unloaded")
        self._cmd._cis_has_changed = False  # type: ignore[attr-defined]

    def preset_cis_load(self, ns: argparse.Namespace,
                        cis: Optional[CIS] = None):
        if self._cmd is None:
            return

        self._cmd.check_if_cis_changed()  # type: ignore[attr-defined]

        if cis is not None:
            self._cmd._cis_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd._cis_has_changed = False  # type: ignore[attr-defined]

        if cis is None:
            try:
                cis = CIS.load(ns.name)
            except exception.ShaaNameError as ex:
                self._cmd.perror(f"[!] {ex}")
                return
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
    create_parser.add_argument("name", help="name of CIS preset")
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

    delete_parser = pre_cis_subparser.add_parser(
        "delete", help="delete CIS preset")
    delete_parser.set_defaults(func=preset_cis_delete)

    rename_parser = pre_cis_subparser.add_parser(
        "rename", help="""rename CIS preset (save current changes \
automatically)""")
    rename_parser.add_argument("name",
                               help="new name of CIS preset")
    rename_parser.set_defaults(func=preset_cis_rename)

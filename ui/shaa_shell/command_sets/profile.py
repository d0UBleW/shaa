from __future__ import annotations

import argparse
from typing import Dict, List, Optional, Text

from cmd2 import (Cmd2ArgumentParser, CommandSet,  # type: ignore[import]
                  CompletionError, as_subcommand_to, with_default_category)
from cmd2.table_creator import Column, SimpleTable  # type: ignore[import]

from shaa_shell.utils import exception
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.inventory import Inventory
from shaa_shell.utils.preset import PRESETS, list_preset
from shaa_shell.utils.profile import Profile
from shaa_shell.utils.role import Role


@with_default_category("profile")
class profile_subcmd(CommandSet):
    def _choices_profile_name(self) -> List[Text]:
        return Profile.list_profile()

    def _choices_config_name(
        self: CommandSet,
        arg_tokens: Dict[Text, List[Text]]
    ) -> List[Text]:
        if self._cmd is None:
            return []

        if "config" not in arg_tokens:
            return []

        config = arg_tokens["config"][0]
        if config == "inventory":
            return Inventory.list_inventory()

        if config in PRESETS:
            return list_preset(config)

        raise CompletionError(
            f"[!] Invalid config name: {config}"
        )

    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument("name", help="name of profile")

    delete_parser = Cmd2ArgumentParser()
    delete_parser.add_argument("name",
                               choices_provider=_choices_profile_name,
                               nargs="?",
                               help="name of profile")

    save_parser = Cmd2ArgumentParser()
    save_parser.add_argument("name",
                             nargs="?",
                             help="(save as) name of profile")

    rename_parser = Cmd2ArgumentParser()
    rename_parser.add_argument("name",
                               help="new name of profile")

    list_parser = Cmd2ArgumentParser()
    list_parser.add_argument("pattern", nargs="?", default=".*",
                             help="name pattern in regex to be searched")

    load_parser = Cmd2ArgumentParser()
    load_parser.add_argument("name",
                             choices_provider=_choices_profile_name,
                             help="name of profile")

    unload_parser = Cmd2ArgumentParser()

    set_parser = Cmd2ArgumentParser()
    set_parser.add_argument("config",
                            choices=["inventory"] + PRESETS,
                            help="config selection")
    set_parser.add_argument("name",
                            choices_provider=_choices_config_name,
                            help="name of specified config")

    unset_parser = Cmd2ArgumentParser()
    unset_parser.add_argument("config",
                              choices=["inventory"] + PRESETS,
                              help="config selection")

    info_parser = Cmd2ArgumentParser()

    @as_subcommand_to("profile", "info", info_parser,
                      help="show current profile info")
    def profile_info(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.perror("[!] No profile is loaded")
            return

        columns = [
            Column("Key", width=16),
            Column("Sep", width=1),
            Column("Value", width=64),
        ]

        st = SimpleTable(columns)
        data_list = []
        data_list.append(["profile name", ":", profile.name])
        inv_name = profile.inv_name
        if inv_name is None:
            inv_name = ""

        data_list.append(["inventory", ":", inv_name])

        for key, val in profile.presets.items():
            if val is None:
                val = ""

            data_list.append([key, ":", val])

        tbl = st.generate_table(data_list, row_spacing=0, include_header=False)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to("profile", "create", create_parser,
                      aliases=["add"],
                      help="create profile")
    def profile_create(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        self._cmd.check_if_profile_changed()  # type: ignore[attr-defined]
        try:
            profile = Profile.create(ns.name)
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._profile_has_changed = False  # type: ignore[attr-defined]
        self._cmd._profile = profile  # type: ignore

        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        if inv is not None:
            profile.inv_name = inv.name

        cis: Optional[CIS] = self._cmd._cis  # type: ignore
        if cis is not None:
            profile.presets["cis"] = cis.name

        role_util: Optional[Role] = self._cmd._util  # type: ignore
        if role_util is not None:
            profile.presets["util"] = role_util.name

        role_oscap: Optional[Role] = self._cmd._oscap  # type: ignore
        if role_oscap is not None:
            profile.presets["oscap"] = role_oscap.name

        role_sec_tools: Optional[Role] = self._cmd._sec_tools  # type: ignore
        if role_sec_tools is not None:
            profile.presets["sec_tools"] = role_sec_tools.name

        return self.profile_load(None, profile)  # type: ignore

    @as_subcommand_to("profile", "load", load_parser,
                      help="load profile")
    def profile_load(self: CommandSet,
                     ns: argparse.Namespace,
                     profile: Optional[Profile] = None):
        if self._cmd is None:
            return

        self._cmd.check_if_profile_changed()  # type: ignore

        if profile is not None:
            self._cmd._profile_has_changed = True  # type: ignore[attr-defined]
        else:
            self._cmd._profile_has_changed = False  # type: ignore

        arg_profile = profile
        if profile is None:
            try:
                profile = Profile.load(ns.name)
            except exception.ShaaNameError as ex:
                self._cmd.perror(f"[!] {ex}")
                return

        if arg_profile is None:
            self._cmd.do_unload("")  # type: ignore

        self._cmd._profile = profile  # type: ignore

        _profile: Profile = self._cmd._profile  # type: ignore
        inv_name = _profile.inv_name
        if inv_name is not None and arg_profile is None:
            self._cmd.do_inventory(f"load {inv_name}")  # type: ignore

        for pre_key, pre_val in _profile.presets.items():
            if arg_profile is not None:
                break
            if pre_val is None:
                continue
            self._cmd.do_preset(f"{pre_key} load {pre_val}")  # type: ignore

    @as_subcommand_to("profile", "unload", unload_parser,
                      help="unload profile")
    def profile_unload(self: CommandSet, _):
        if self._cmd is None:
            return
        self._cmd.check_if_profile_changed()  # type: ignore[attr-defined]
        self._cmd._profile = None  # type: ignore[attr-defined]
        self._cmd._profile_has_changed = False  # type: ignore

    @as_subcommand_to("profile", "list", list_parser,
                      aliases=["ls"],
                      help="list available profile")
    def profile_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        columns = [
            Column("Name", width=32),
            Column("Inventory", width=32),
            Column("Presets", width=48),
        ]

        st = SimpleTable(columns)

        data_list = []
        for profile_name in Profile.list_profile(ns.pattern):
            try:
                profile: Profile = Profile.load(profile_name)
            except exception.ShaaNameError as ex:
                self._cmd.perror(f"[!] {ex}")
                return
            presets = []
            for preset_name, preset in profile.presets.items():
                if preset is None:
                    preset = ""
                presets.append(f"{preset_name}: {preset}")
            inv_name = profile.inv_name
            if inv_name is None:
                inv_name = ""
            data_list.append([profile_name,
                              inv_name,
                              "\n".join(presets)])

        tbl = st.generate_table(data_list, row_spacing=1)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to("profile", "save", save_parser,
                      help="save profile")
    def profile_save(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.perror("[!] Currently, there is no profile loaded")
            return
        try:
            if not profile.save(ns.name):
                self._cmd.perror("[!] Unable to save")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        if ns.name is None:
            self._cmd._profile_has_changed = False  # type: ignore
        self._cmd.pfeedback("[+] Profile has been saved")

    @as_subcommand_to("profile", "rename", rename_parser,
                      help="""rename profile name (save current changes \
automatically)""")
    def profile_rename(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.perror("[!] Currently, there is no profile loaded")
            return
        old_name = profile.name
        try:
            if not profile.rename(ns.name):
                self._cmd.perror("[!] Unable to rename")
                return
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return
        self._cmd._profile_has_changed = False  # type: ignore
        self._cmd.pfeedback("[+] Profile has been renamed")
        self._cmd.pfeedback(f"    old: {old_name}")
        self._cmd.pfeedback(f"    new: {profile.name}")

    @as_subcommand_to("profile", "delete", delete_parser,
                      aliases=["del", "rm"],
                      help="delete current profile")
    def profile_delete(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        profile_name = ns.name
        if profile_name is None:
            profile: Optional[Profile] = self._cmd._profile  # type: ignore
            if profile is None:
                err_msg = "[!] Unable to delete as no profile is loaded\n"
                err_msg += "    Provide a profile name instead"
                self._cmd.perror(err_msg)
                return
            profile_name = profile.name

        if (_ := self._cmd.read_input(
                "[+] Are you sure [y/N]? ")) != "y":
            self._cmd.perror("[!] Deletion aborted")
            return

        try:
            Profile.delete(profile_name)
        except exception.ShaaNameError as ex:
            self._cmd.perror(f"[!] {ex}")
            return

        self._cmd.pfeedback("[+] Profile has been deleted successfully")
        if ns.name is None:
            self._cmd._profile_has_changed = False  # type: ignore
            self.profile_unload(None)  # type: ignore[attr-defined]

    @as_subcommand_to("profile", "unset", unset_parser,
                      help="unset profile config")
    def profile_unset(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.perror("[!] Currently, there is no profile loaded")
            return

        old_name = None
        if ns.config == "inventory":
            old_name = profile.inv_name
            profile.inv_name = None
            self._cmd.do_inventory("unload")  # type: ignore
        else:
            if ns.config not in PRESETS:
                self._cmd.perror(f"[!] Invalid preset: {ns.config}")
                return
            old_name = profile.presets[ns.config]
            profile.presets[ns.config] = None
            self._cmd.do_preset(f"{ns.config} unload")  # type: ignore

        self._cmd.poutput(f"\n[+] {ns.config} unset successfully")
        self._cmd._profile_has_changed = True  # type: ignore

        if old_name is None:
            old_name = ""

        self._cmd.poutput(f"    old: {old_name}")

    @as_subcommand_to("profile", "set", set_parser,
                      help="set profile config")
    def profile_set(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.perror("[!] Currently, there is no profile loaded")
            return

        old_name = None
        if ns.config == "inventory":
            if ns.name not in Inventory.list_inventory():
                self._cmd.perror(
                    f"[!] Inventory name does not exist: {ns.name}")
                return
            old_name = profile.inv_name
            profile.inv_name = ns.name
            self._cmd.do_inventory(f"load {ns.name}")  # type: ignore
            self._cmd.poutput("\n[+] Inventory set successfully")
        else:
            if ns.config not in PRESETS:
                self._cmd.perror(f"[!] Invalid preset: {ns.config}")
                return
            preset = ns.config
            if ns.name not in list_preset(preset):
                self._cmd.perror(f"[!] {preset} preset name does not exist")
                return
            if preset in profile.presets.keys():
                old_name = profile.presets[preset]
            profile.presets[preset] = ns.name
            self._cmd.do_preset(f"{preset} load {ns.name}")  # type: ignore
            self._cmd.poutput(f"\n[+] {preset} preset set successfully")

        if old_name is None:
            old_name = ""

        self._cmd.poutput(f"    old: {old_name}")
        self._cmd.poutput(f"    new: {ns.name}")
        self._cmd._profile_has_changed = True  # type: ignore

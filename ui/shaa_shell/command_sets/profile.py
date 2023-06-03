from __future__ import annotations

import argparse
from typing import List, Text, Optional, Dict
from cmd2 import (  # type: ignore[import]
    Cmd2ArgumentParser,
    CommandSet,
    with_default_category,
    as_subcommand_to,
)
from cmd2.table_creator import (  # type: ignore[import]
    SimpleTable,
    Column,
)
from shaa_shell.utils.profile import Profile
from shaa_shell.utils.inventory import Inventory
from shaa_shell.utils.preset import list_preset
from shaa_shell.utils.cis import CIS


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

        return list_preset(config)

    create_parser = Cmd2ArgumentParser()
    create_parser.add_argument("name", help="name of profile")

    delete_parser = Cmd2ArgumentParser()

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
                            choices=["inventory", "cis", "oscap", "extra"],
                            help="config selection")
    set_parser.add_argument("name",
                            choices_provider=_choices_config_name,
                            help="name of specified config")

    unset_parser = Cmd2ArgumentParser()
    unset_parser.add_argument("config",
                              choices=["inventory", "cis", "oscap", "extra"],
                              help="config selection")

    @as_subcommand_to("profile", "create", create_parser,
                      aliases=["add"],
                      help="create profile")
    def profile_create(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        profile = Profile.create(ns.name)
        if profile is None:
            warning_text = "[!] Invalid name or specified profile name"
            warning_text += "already existed"
            self._cmd.poutput(warning_text)
            return
        self._cmd._profile = profile  # type: ignore

        inv: Optional[Inventory] = self._cmd._inventory  # type: ignore
        cis: Optional[CIS] = self._cmd._cis  # type: ignore
        if inv is not None:
            profile.inv_name = inv.name
        if cis is not None:
            profile.presets["cis"] = cis.name

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

        arg_profile = profile
        if profile is None:
            profile = Profile.load(ns.name)
            self._cmd._profile = profile  # type: ignore

        if profile is None:
            return

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
        self._cmd.check_if_profile_changed()  # type: ignore
        self._cmd._profile = None  # type: ignore

    @as_subcommand_to("profile", "list", list_parser,
                      aliases=["ls"],
                      help="list available profile")
    def profile_list(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        columns = [
            Column("Name", width=32),
        ]

        st = SimpleTable(columns)

        data_list = []
        for profile in Profile.list_profile(ns.pattern):
            data_list.append([profile])

        tbl = st.generate_table(data_list, row_spacing=0)
        self._cmd.poutput(f"\n{tbl}\n")

    @as_subcommand_to("profile", "save", save_parser,
                      help="save profile")
    def profile_save(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.poutput("[!] Currently, there is no profile loaded")
            return
        if not profile.save(ns.name):
            self._cmd.poutput("[!] Invalid profile name")
            return

        self._cmd._profile_has_changed = False  # type: ignore
        self._cmd.poutput("[+] Profile has been saved")

    @as_subcommand_to("profile", "rename", rename_parser,
                      help="rename profile name")
    def profile_rename(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return
        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.poutput("[!] Currently, there is no profile loaded")
            return
        old_name = profile.name
        if not profile.rename(ns.name):
            self._cmd.poutput("[!] Invalid profile name")
            return
        self._cmd.poutput("[+] Profile has been renamed")
        self._cmd.poutput(f"    old: {old_name}")
        self._cmd.poutput(f"    new: {profile.name}")

    @as_subcommand_to("profile", "delete", delete_parser,
                      aliases=["del", "rm"],
                      help="delete current profile")
    def profile_delete(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.poutput("[!] Currently, there is no profile loaded")
            return
        profile.delete()
        self._cmd.poutput("[+] Profile has been deleted successfully")

    @as_subcommand_to("profile", "unset", unset_parser,
                      help="unset profile config")
    def profile_unset(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.poutput("[!] Currently, there is no profile loaded")
            return

        if ns.config == "inventory":
            profile.inv_name = None
            self._cmd.do_inventory("unload")  # type: ignore
        else:
            profile.presets[ns.config] = None
            self._cmd.do_preset(f"{ns.config} unload")  # type: ignore

        self._cmd.poutput(f"[+] {ns.config} unset successfully")

    @as_subcommand_to("profile", "set", set_parser,
                      help="set profile config")
    def profile_set(self: CommandSet, ns: argparse.Namespace):
        if self._cmd is None:
            return

        profile: Optional[Profile] = self._cmd._profile  # type: ignore
        if profile is None:
            self._cmd.poutput("[!] Currently, there is no profile loaded")
            return

        old_name = None
        if ns.config == "inventory":
            if ns.name not in Inventory.list_inventory():
                self._cmd.poutput("[!] Inventory name does not exist")
                return
            old_name = profile.inv_name
            profile.inv_name = ns.name
            self._cmd.do_inventory(f"load {ns.name}")  # type: ignore
            self._cmd.poutput("\n[+] Inventory set successfully")
        elif ns.config == "cis":
            if ns.name not in list_preset("cis"):
                self._cmd.poutput("[!] CIS preset name does not exist")
                return
            if "cis" in profile.presets.keys():
                old_name = profile.presets["cis"]
            profile.presets["cis"] = ns.name
            self._cmd.do_preset(f"cis load {ns.name}")  # type: ignore
            self._cmd.poutput("\n[+] CIS preset set successfully")
        elif ns.config == "oscap":
            if ns.name not in list_preset("oscap"):
                self._cmd.poutput("[!] OSCAP preset name does not exist")
                return
            if "oscap" in profile.presets.keys():
                old_name = profile.presets["oscap"]
            profile.presets["oscap"] = ns.name
            self._cmd.do_preset(f"oscap load {ns.name}")  # type: ignore
            self._cmd.poutput("\n[+] OSCAP preset set successfully")
        elif ns.config == "extra":
            if ns.name not in list_preset("extra"):
                self._cmd.poutput("[!] Extra preset name does not exist")
                return
            if "extra" in profile.presets.keys():
                old_name = profile.presets["extra"]
            profile.presets["extra"] = ns.name
            self._cmd.do_preset(f"extra load {ns.name}")  # type: ignore
            self._cmd.poutput("\n[+] Extra preset set successfully")

        if old_name is None:
            old_name = ""

        self._cmd.poutput(f"    old: {old_name}")
        self._cmd.poutput(f"    new: {ns.name}")
        self._cmd._profile_has_changed = True  # type: ignore
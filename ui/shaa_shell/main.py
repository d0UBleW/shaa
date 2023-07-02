import argparse
import cmd2
from typing import Optional, List

from shaa_shell.command_sets import (
    inventory as inv_cs,
    inventory_node as inv_node_cs,
    inventory_group as inv_group_cs,
    cis as cis_cs,
    role_util as util_cs,
    preset as pre_cs,
    profile as pro_cs,
    oscap as oscap_cs,
    sec_tools as sec_tools_cs,
)
from shaa_shell.utils.parser import (
    inventory_parser,
    preset_parser,
    profile_parser,
    play_parser,
    clear_parser,
    config_parser,
    unload_parser,
)
from shaa_shell.utils.inventory import Inventory
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.role import Role
from shaa_shell.utils.profile import Profile
from shaa_shell.utils import play
from shaa_shell.utils import exception
from shaa_shell.utils.path import USER_DATA_PATH

STARTUP_SCRIPT = USER_DATA_PATH.joinpath("shaashrc")
HIST_FILE = USER_DATA_PATH.joinpath("shaash_hist")


class ShaaShell(cmd2.Cmd):
    _inventory: Optional[Inventory] = None
    _inv_has_changed: bool = False

    _cis: Optional[CIS] = None
    _cis_has_changed: bool = False

    _util: Optional[Role] = None
    _util_has_changed: bool = False

    _oscap: Optional[Role] = None
    _oscap_has_changed: bool = False

    _sec_tools: Optional[Role] = None
    _sec_tools_has_changed: bool = False

    _profile: Optional[Profile] = None
    _profile_has_changed: bool = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            persistent_history_file=HIST_FILE,
            startup_script=STARTUP_SCRIPT,
            silence_startup_script=True,
            auto_load_commands=False,
            **kwargs,
        )
        self.prompt = "shaa> "
        self.continuation_prompt = "... "
        self.default_category = "general"

        self._inventory_node_cmd = inv_node_cs.inventory_node_cmd()
        self._inventory_node_subcmd = inv_node_cs.inventory_node_subcmd()
        self._inventory_group_cmd = inv_group_cs.inventory_group_cmd()
        self._inventory_group_subcmd = inv_group_cs.inventory_group_subcmd()

        self._cis_cmd = cis_cs.cis_cmd()
        self._cis_section_cmd = cis_cs.cis_section_cmd()
        self._cis_set_cmd = cis_cs.cis_set_cmd()
        self._cis_search_cmd = cis_cs.cis_search_cmd()

        self._util_cmd = util_cs.util_cmd()
        self._util_action_cmd = util_cs.util_action_cmd()
        self._util_set_cmd = util_cs.util_set_cmd()
        self._util_search_cmd = util_cs.util_search_cmd()

        self._oscap_cmd = oscap_cs.oscap_cmd()
        self._oscap_action_cmd = oscap_cs.oscap_action_cmd()
        self._oscap_set_cmd = oscap_cs.oscap_set_cmd()
        self._oscap_search_cmd = oscap_cs.oscap_search_cmd()

        self._sec_tools_cmd = sec_tools_cs.sec_tools_cmd()
        self._sec_tools_action_cmd = sec_tools_cs.sec_tools_action_cmd()
        self._sec_tools_set_cmd = sec_tools_cs.sec_tools_set_cmd()
        self._sec_tools_search_cmd = sec_tools_cs.sec_tools_search_cmd()

        self.register_postloop_hook(self.check_if_inv_changed)
        self.register_postloop_hook(self.check_if_cis_changed)
        self.register_postloop_hook(self.check_if_util_changed)
        self.register_postloop_hook(self.check_if_oscap_changed)
        self.register_postloop_hook(self.check_if_sec_tools_changed)
        self.register_postloop_hook(self.check_if_profile_changed)

    def _set_prompt(self):
        inv_prompt = ""
        if self._inventory is not None:
            inv_prompt = f"[inv: {self._inventory.name}] "

        cis_prompt = ""
        if self._cis is not None:
            cis_prompt = f"[cis: {self._cis.name}] "

        util_prompt = ""
        if self._util is not None:
            util_prompt = f"[util: {self._util.name}] "

        oscap_prompt = ""
        if self._oscap is not None:
            oscap_prompt = f"[oscap: {self._oscap.name}] "

        sec_tools_prompt = ""
        if self._sec_tools is not None:
            sec_tools_prompt = f"[sec_tools: {self._sec_tools.name}] "

        profile_prompt = ""
        if self._profile is not None:
            profile_prompt = f"[pro: {self._profile.name}] "

        self.prompt = "\n"
        self.prompt += f"{profile_prompt}"
        self.prompt += f"{inv_prompt}"
        self.prompt += f"{cis_prompt}"
        self.prompt += f"{util_prompt}"
        self.prompt += f"{sec_tools_prompt}"
        self.prompt += f"{oscap_prompt}"
        self.prompt += "\nshaa> "

    def postcmd(self, stop, statement):
        self._set_prompt()
        return stop

    @cmd2.with_argparser(inventory_parser)
    @cmd2.with_category('inventory')
    def do_inventory(self, ns: argparse.Namespace):
        """
        Manage inventory
        """
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self.poutput("No subcommand was provided")
            self.do_help('inventory')

    @cmd2.with_argparser(preset_parser)
    @cmd2.with_category("preset")
    def do_preset(self, ns: argparse.Namespace):
        """
        Manage preset
        """
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self.poutput("No subcommand was provided")
            self.do_help("preset")

    @cmd2.with_argparser(profile_parser)
    @cmd2.with_category("profile")
    def do_profile(self, ns: argparse.Namespace):
        """
        Manage profile
        """
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self.poutput("No subcommand was provided")
            self.do_help("profile")

    @cmd2.with_argparser(unload_parser)
    @cmd2.with_category("general")
    def do_unload(self, ns: argparse.Namespace):
        """
        Unload inventory, all presets, and profile
        """
        if self._inventory is not None:
            self.do_inventory("unload")
        if self._cis is not None:
            self.do_preset("cis unload")
        if self._oscap is not None:
            self.do_preset("oscap unload")
        if self._util is not None:
            self.do_preset("util unload")
        if self._sec_tools is not None:
            self.do_preset("sec_tools unload")
        if self._profile is not None:
            self.check_if_profile_changed()
            self._profile = None

    def _choices_targets(self) -> List[cmd2.CompletionItem]:
        if self._inventory is None:
            raise cmd2.CompletionError("[!] No inventory is loaded")
        groups = self._inventory.groups
        targets: List[cmd2.CompletionItem] = []
        for group in groups.keys():
            if group == "ungrouped":
                continue
            targets.append(cmd2.CompletionItem(group, "group"))
        for group in groups.keys():
            targets += list(map(lambda n: cmd2.CompletionItem(n, "node"),
                                groups[group].nodes.keys()))
        return targets

    play_parser.add_argument(
        "-t",
        "--target",
        nargs="*",
        default=["all"],
        help="specify list of playbook target node name or group name",
        choices_provider=_choices_targets,
    )

    @cmd2.with_argparser(play_parser)
    @cmd2.with_category("play")
    def do_play(self, ns: argparse.Namespace):
        """
        Start hardening based on current loaded profile
        If no profile is loaded, current inventory and presets are used instead

        Note: only saved inventory and presets data are used, unsaved changes
        are ignored
        """
        inv = self._inventory
        if inv is None:
            self.perror("[!] No inventory is loaded, aborting!")
            return

        self.check_if_inv_changed()

        if ns.target != ["all"]:
            valid_targets = list(inv.groups.keys())
            for group in inv.groups.keys():
                valid_targets += inv.groups[group].nodes.keys()

            for target in ns.target:
                if target not in valid_targets:
                    self.perror(f"[!] Invalid target: {target}")
                    self.perror(f"    Available targets: {valid_targets}")
                    return

        cis = self._cis
        role_util = self._util
        oscap = self._oscap
        sec_tools = self._sec_tools

        # Handle case when play is fired without a profile loaded
        profile = self._profile
        if profile is None:
            profile = Profile(name="_shaa_unnamed_profile")
            profile.inv_name = inv.name
            if cis is not None:
                profile.presets["cis"] = cis.name
            if role_util is not None:
                profile.presets["util"] = role_util.name
            if oscap is not None:
                profile.presets["oscap"] = oscap.name
            if sec_tools is not None:
                profile.presets["sec_tools"] = sec_tools.name

        if len(ns.preset) == 0 or ("cis" in ns.preset and cis is not None):
            self.check_if_cis_changed()
        if len(ns.preset) == 0 or (
                "util" in ns.preset and role_util is not None):
            self.check_if_util_changed()
        if len(ns.preset) == 0 or (
                "oscap" in ns.preset and oscap is not None):
            self.check_if_oscap_changed()
        if len(ns.preset) == 0 or (
                "sec_tools" in ns.preset and sec_tools is not None):
            self.check_if_sec_tools_changed()

        self.poutput("[+] Generating playbook ...")
        try:
            gen_pb = play.generate_playbook(profile,
                                            ns.preset,
                                            targets=ns.target)
        except exception.ShaaNameError as ex:
            self.perror(f"[!] {ex}")
            return
        except exception.ShaaInventoryError as ex:
            self.perror(f"[!] {ex}")
            return
        if gen_pb is not None and not gen_pb:
            self.perror("[!] Error in generating playbook")
            self.perror("    Inventory data is empty, try to save it first")
            self.perror("    or make sure it is set on current profile")
            return
        if gen_pb is None:
            return
        self.poutput("[+] Done")
        self.poutput("[+] Generating tags ...")
        try:
            tags = play.generate_tags(profile, ns.preset)
        except exception.ShaaNameError as ex:
            self.perror(f"[!] {ex}")
            return
        self.poutput("[+] Done")
        self.poutput("[+] Running playbook ...")
        try:
            play.run_playbook(
                profile.name,
                tags=tags,
                verbose=ns.verbose,
                color=ns.color)
        except exception.ShaaVaultError as ex:
            self.perror(f"[!] {ex}")
            return

    @cmd2.with_argparser(clear_parser)
    @cmd2.with_category("general")
    def do_clear(self, ns: argparse.Namespace):
        """
        Clear screen
        """
        self.do_shell("clear -x")

    @cmd2.with_argparser(config_parser)
    @cmd2.with_category("general")
    def do_config(self, ns: argparse.Namespace):
        """
        Configure startup script
        """
        self.do_edit(STARTUP_SCRIPT)

    def check_if_inv_changed(self) -> None:
        if self._inv_has_changed:
            prompt = "[*] There are unsaved changes on current inventory.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._inventory is not None:
                    if not self._inventory.save():
                        return
                    self.poutput("[+] Changes have been saved successfully")
                    self._inv_has_changed = False

    def check_if_cis_changed(self) -> None:
        if self._cis_has_changed:
            prompt = "[*] There are unsaved changes on current CIS preset.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._cis is not None:
                    if not self._cis.save():
                        return
                    self.poutput("[+] Changes have been saved successfully")
                    self._cis_has_changed = False

    def check_if_util_changed(self) -> None:
        if self._util_has_changed:
            prompt = "[*] There are unsaved changes on current util preset.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._util is not None:
                    if not self._util.save():
                        return
                    self.poutput("[+] Changes have been saved successfully")
                    self._util_has_changed = False

    def check_if_oscap_changed(self) -> None:
        if self._oscap_has_changed:
            prompt = "[*] There are unsaved changes on current oscap preset.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._oscap is not None:
                    if not self._oscap.save():
                        return
                    self.poutput("[+] Changes have been saved successfully")
                    self._oscap_has_changed = False

    def check_if_sec_tools_changed(self) -> None:
        if self._sec_tools_has_changed:
            prompt = "[*] There are unsaved changes on current sec_tools "
            prompt += "preset.\n[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._sec_tools is not None:
                    if not self._sec_tools.save():
                        return
                    self.poutput("[+] Changes have been saved successfully")
                    self._sec_tools_has_changed = False

    def check_if_profile_changed(self) -> None:
        if self._profile_has_changed:
            prompt = "[*] There are unsaved changes on current profile.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._profile is not None:
                    if not self._profile.save():
                        return
                    self.poutput("[+] Changes have been saved successfully")
                    self._profile_has_changed = False


def main():
    shaa_shell = ShaaShell(command_sets=[
        inv_cs.inventory_subcmd(),
        pre_cs.preset_cis_cmd(),
        pre_cs.preset_util_cmd(),
        pre_cs.preset_oscap_cmd(),
        pre_cs.preset_sec_tools_cmd(),
        pro_cs.profile_subcmd(),
    ])
    shaa_shell.disable_command(
        "run_pyscript",
        message_to_print=f"{cmd2.COMMAND_NAME} is currently disabled"
    )
    shaa_shell.cmdloop()


if __name__ == "__main__":
    main()

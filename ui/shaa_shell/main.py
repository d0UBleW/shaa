import argparse
import cmd2
from typing import Optional

from shaa_shell.command_sets import (
    inventory as inv_cs,
    inventory_node as inv_node_cs,
    inventory_group as inv_group_cs,
    cis as cis_cs,
    role_util as util_cs,
    preset as pre_cs,
    profile as pro_cs,
)
from shaa_shell.utils.parser import (
    inventory_parser,
    preset_parser,
    profile_parser,
    play_parser,
    clear_parser,
)
from shaa_shell.utils.inventory import Inventory
from shaa_shell.utils.cis import CIS
from shaa_shell.utils.role import Role
from shaa_shell.utils.profile import Profile
from shaa_shell.utils import play


class ShaaShell(cmd2.Cmd):
    _inventory: Optional[Inventory] = None
    _inv_has_changed: bool = False

    _cis: Optional[CIS] = None
    _cis_has_changed: bool = False

    _util: Optional[Role] = None
    _util_has_changed: bool = False

    _profile: Optional[Profile] = None
    _profile_has_changed: bool = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            persistent_history_file='~/.shaa_shell_hist',
            startup_script='~/.shaa_shell_rc',
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
        self.register_postloop_hook(self.check_if_inv_changed)
        self.register_postloop_hook(self.check_if_cis_changed)
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

        profile_prompt = ""
        if self._profile is not None:
            profile_prompt = f"[pro: {self._profile.name}] "

        self.prompt = "\n"
        self.prompt += f"{profile_prompt}"
        self.prompt += f"{inv_prompt}"
        self.prompt += f"{cis_prompt}"
        self.prompt += f"{util_prompt}"
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
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self.poutput("No subcommand was provided")
            self.do_help("preset")

    @cmd2.with_argparser(profile_parser)
    @cmd2.with_category("profile")
    def do_profile(self, ns: argparse.Namespace):
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self.poutput("No subcommand was provided")
            self.do_help("profile")

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
            self.poutput("[!] No inventory is loaded, aborting!")
            return

        # TODO: check if at least one preset is set
        cis = self._cis
        if cis is None:
            self.poutput("[!] No CIS preset is loaded, aborting!")
            return

        profile = self._profile
        if profile is None:
            profile = Profile(name="_shaa_unnamed_profile")
            profile.inv_name = inv.name
            profile.presets["cis"] = cis.name

        self.check_if_inv_changed()
        if len(ns.preset) == 0 or "cis" in ns.preset:
            self.check_if_cis_changed()

        self.poutput("[+] Generating playbook ...")
        gen_pb = play.generate_playbook(profile, ns.preset)
        if gen_pb is not None and not gen_pb:
            self.poutput("[!] Error in generating playbook")
            self.poutput("    Inventory data is empty, try to save it first")
            return
        if gen_pb is None:
            return
        self.poutput("[+] Done")
        self.poutput("[+] Generating tags ...")
        tags = play.generate_cis_tags(profile, ns.preset)
        self.poutput("[+] Done")
        self.poutput("[+] Running playbook ...")
        play.run_playbook(
            profile.name,
            tags=tags,
            verbose=ns.verbose,
            color=ns.color)

    @cmd2.with_argparser(clear_parser)
    @cmd2.with_category("general")
    def do_clear(self, ns: argparse.Namespace):
        """
        Clear screen
        """
        self.do_shell("clear -x")

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
        pro_cs.profile_subcmd(),
    ])
    shaa_shell.disable_command(
        "run_pyscript",
        message_to_print=f"{cmd2.COMMAND_NAME} is currently disabled"
    )
    shaa_shell.cmdloop()


if __name__ == "__main__":
    main()

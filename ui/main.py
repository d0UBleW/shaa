#!/usr/bin/env python3

import argparse
import cmd2  # type: ignore[import]
from command_sets import (
    inventory as inv_cs,
    inventory_node as inv_node_cs,
    inventory_group as inv_group_cs,
    cis as cis_cs,
    preset as pre_cs,
)
from typing import Optional
from utils.parser import (
    inventory_parser,
    preset_parser,
)
from utils.inventory import Inventory
from utils.cis import CIS


class ShaaShell(cmd2.Cmd):
    _inventory: Optional[Inventory] = None
    _inv_has_changed: bool = False

    _cis: Optional[CIS] = None
    _cis_has_changed: bool = False

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            persistent_history_file='.shaa_shell_hist',
            startup_script='.shaa_shell_rc',
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
        self.register_postloop_hook(self.check_if_inv_changed)
        self.register_postloop_hook(self.check_if_cis_changed)

    def _set_prompt(self):
        inv_prompt = ""
        if self._inventory is not None:
            inv_prompt = f"[inv: {self._inventory.name}] "

        cis_prompt = ""
        if self._cis is not None:
            cis_prompt = f"[cis: {self._cis.name}] "

        self.prompt = f"\n{inv_prompt}{cis_prompt}\nshaa> "

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

    def check_if_inv_changed(self) -> None:
        if self._inv_has_changed:
            prompt = "[*] There are unsaved changes on current inventory.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._inventory is not None:
                    self._inventory.save()
                    self.poutput("[+] Changes have been saved successfully")
            self._inv_has_changed = False

    def check_if_cis_changed(self) -> None:
        if self._cis_has_changed:
            prompt = "[*] There are unsaved changes on current CIS preset.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._cis is not None:
                    self._cis.save()
                    self.poutput("[+] Changes have been saved successfully")
            self._inv_has_changed = False


def main():
    shaa_shell = ShaaShell(command_sets=[
        inv_cs.inventory_subcmd(),
        pre_cs.preset_cis_cmd(),
    ])
    shaa_shell.disable_command(
        "run_pyscript",
        message_to_print=f"{cmd2.COMMAND_NAME} is currently disabled"
    )
    shaa_shell.cmdloop()


if __name__ == "__main__":
    main()

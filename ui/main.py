#!/usr/bin/env python3

import argparse
import cmd2  # type: ignore[import]
from command_sets import (
    inventory as inv_cs,
    inventory_node as inv_node_cs,
    inventory_group as inv_group_cs,
    cis as cis_cs,
)
from typing import Optional
from utils.parser import (
    inventory_parser,
    cis_parser,
)
from utils.inventory import Inventory


class ShaaShell(cmd2.Cmd):
    _inventory: Optional[Inventory] = None
    _inv_has_changed: bool = False

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
        # self._cis_section_cmd = cis_cs.cis_section_cmd()
        self.register_postloop_hook(self.check_if_inv_changed)

    def _set_prompt(self):
        if self._inventory is not None:
            self.prompt = f"\n[I: {self._inventory.name}]\nshaa> "
            return
        self.prompt = "shaa> "

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

    @cmd2.with_argparser(cis_parser)
    @cmd2.with_category("cis")
    def do_cis(self, ns: argparse.Namespace):
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self.poutput("No subcommand was provided")
            self.do_help("cis")

    def check_if_inv_changed(self) -> None:
        if self._inv_has_changed:
            prompt = "[*] There are unsaved changes on current inventory.\n"
            prompt += "[+] Do you want to save? [Y/n] "
            if (_ := self.read_input(prompt).lower()) != "n":
                if self._inventory is not None:
                    self._inventory.save()
                    self.poutput("[+] Changes have been saved successfully")
            self._inv_has_changed = False


def main():
    shaa_shell = ShaaShell(command_sets=[
        inv_cs.inventory_subcmd(),
        cis_cs.cis_section_cmd(),
        cis_cs.cis_set_cmd(),
        cis_cs.cis_search_cmd(),
    ])
    shaa_shell.disable_command(
        "run_pyscript",
        message_to_print=f"{cmd2.COMMAND_NAME} is currently disabled"
    )
    shaa_shell.cmdloop()


if __name__ == "__main__":
    main()

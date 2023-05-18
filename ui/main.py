#!/usr/bin/env python3

import argparse
import cmd2
from command_sets.inventory import inventory_CS
from typing import Optional
from utils.parser import inventory_parser
from utils.inventory import Inventory


class ShaaShell(cmd2.Cmd):
    _inventory: Optional[Inventory] = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            persistent_history_file='.shaa_shell_hist',
            startup_script='.shaa_shell_alias',
            silence_startup_script=True,
            auto_load_commands=False,
            **kwargs,
        )
        self.prompt = "shaa> "
        self.continuation_prompt = "... "
        self.default_category = "general"

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
        handler = ns.cmd2_handler.get()
        if handler is not None:
            handler(ns)
        else:
            self.poutput("No subcommand was provided")
            self.do_help('inventory')


def main():
    shaa_shell = ShaaShell(command_sets=[inventory_CS()])
    shaa_shell.disable_command(
        "run_pyscript",
        message_to_print=f"{cmd2.COMMAND_NAME} is currently disabled"
    )
    shaa_shell.cmdloop()


if __name__ == "__main__":
    main()

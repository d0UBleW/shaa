#!/usr/bin/env python3

from typing import List, Text
from utils.inventory import list_inventory
from cmd2 import (
    Cmd2ArgumentParser,
    CommandSet,
    Statement,
    with_argparser,
    with_default_category,
)


@with_default_category("profile")
class profile_CS(CommandSet):

    def do_create(self, arg: Statement) -> None:
        self._cmd.poutput("create: TODO")
        return

    def do_delete(self, arg: Statement) -> None:
        self._cmd.poutput("delete: TODO")
        return

    def _inventory_list_provider(self) -> List[Text]:
        return list_inventory()

    inventory_parser = Cmd2ArgumentParser()
    inventory_parser.add_argument("name",
                                  choices_provider=_inventory_list_provider,
                                  help="Inventory name to be loaded")

    @with_argparser(inventory_parser)
    def do_use(self, arg: Statement) -> None:
        self._cmd.poutput("use: TODO")
        return

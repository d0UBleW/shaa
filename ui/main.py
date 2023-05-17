#!/usr/bin/env python3

from typing import Text, List
import cmd
from utils import inventory

load_completions = [
    "inventory",
    "profile",
    "preset",
]


class ShaaShell(cmd.Cmd):
    section = None
    profile = None
    inventory = None

    @property
    def prompt(self):
        section_prompt = ""
        if self.section:
            section_prompt = f"[{self.section}] "

        inventory_prompt = ""
        if self.inventory:
            inventory_prompt = f"[I: {self.inventory.name}] "

        return f"\n{section_prompt}{inventory_prompt}\n(shaa) > "

    def do_load(self, args: Text):
        context, _, subargs = args.partition(' ')
        if context == "inventory":
            self.inventory = inventory.Inventory.load(subargs)
            return
        raise Exception("TODO: Not yet implemented")

    def complete_load(self, text, line, begidx, endidx) -> List[Text]:
        if begidx == 5:
            return list(filter(lambda s: s.startswith(text), load_completions))

        context = line.split()[1]
        if context == "inventory":
            inventories = inventory.list_inventory()
            with open('/run/shm/abcd', 'w') as f:
                f.write(f"{line} {begidx} {endidx}\n")
                f.write(f"{' '.join(inventories)}\n")

            return list(filter(lambda s: s.startswith(text), inventories))

        return []

    def do_section(self, args):
        self.section = args

    def do_foobar(self, args: Text):
        print("Foo Bar")

    def do_back(self, args):
        self.section = None

    def do_options(self, args):
        """
        show available options for chosen section
        """
        assert False, "TODO: Not yet implemented"

    def do_quit(self, args):
        quit()

    def do_exit(self, args):
        quit()

    def do_EOF(self, args):
        print("\n\nDo you really want to exit ([y]/n)? ", end="")
        try:
            if (_ := input()) == "n":
                print()
                return
        except EOFError:
            print()
            pass
        self.do_quit(args)

    def default(self, args):
        if args is None:
            print(" ^C")
        else:
            print(f"*** Unknown syntax: {args}")

    def help_foobar(self):
        print("Help for foobar")

    def help_quit(self):
        print("Quit")

    def help_exit(self):
        print("Exit")

    def complete_section(self, text, line, begidx, endidx) -> List[Text]:
        return list(filter(lambda s: s.startswith(text), sections))


sections = [
    "1.1.1.1",
    "1.1.1.2",
    "1.1.2",
    "2.1",
    "3.1"
]

if __name__ == "__main__":
    print("Welcome to SHAA shell. Type help or ? to list commands.")
    shell = ShaaShell()
    while True:
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            shell.default(None)

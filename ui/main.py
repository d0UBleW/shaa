#!/usr/bin/env python3

from typing import Text
import cmd
from utils import utils
import re


class ShaaShell(cmd.Cmd):
    section = None
    profile = None

    @property
    def prompt(self):
        prompt_str = ""
        if self.section:
            prompt_str = f"[{self.section}] "
        return f"(shaa) {prompt_str}> "

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

    def complete_section(self, text, line, begidx, endidx):
        return list(filter(lambda s: s.startswith(text), sections))


sections = [
    "1.1.1.1",
    "1.1.1.2",
    "1.1.2",
    "2.1",
    "3.1"
]

if __name__ == "__main__":
    """ utils.foo() """
    print("Welcome to SHAA shell. Type help or ? to list commands.\n")
    shell = ShaaShell()
    while True:
        try:
            shell.cmdloop()
        except KeyboardInterrupt:
            shell.default(None)

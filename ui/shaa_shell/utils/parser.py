from __future__ import annotations

from cmd2 import Cmd2ArgumentParser
from shaa_shell.utils.preset import PRESETS


def _choices_presets(_):
    return PRESETS


clear_parser = Cmd2ArgumentParser()

config_parser = Cmd2ArgumentParser()

inventory_parser = Cmd2ArgumentParser()
inventory_parser.add_subparsers(title="action", help="action on inventory")

inventory_node_parser = Cmd2ArgumentParser()
inventory_node_parser.add_subparsers(title="action",
                                     help="action on inventory node")

inventory_group_parser = Cmd2ArgumentParser()
inventory_group_parser.add_subparsers(title="action",
                                      help="action on inventory group")

preset_parser = Cmd2ArgumentParser()
preset_parser.add_subparsers(title="action",
                             help="action on preset")

cis_parser = Cmd2ArgumentParser()
cis_parser.add_subparsers(title="subcommands",
                          help="subcommand for cis module")

role_util_parser = Cmd2ArgumentParser()
role_util_parser.add_subparsers(title="subcommands",
                                help="subcommand for util module")

oscap_parser = Cmd2ArgumentParser()
oscap_parser.add_subparsers(title="subcommands",
                            help="subcommand for oscap module")

sec_tools_parser = Cmd2ArgumentParser()
sec_tools_parser.add_subparsers(title="subcommands",
                                help="subcommand for sec_tools module")

profile_parser = Cmd2ArgumentParser()
profile_parser.add_subparsers(title="subcommands",
                              help="subcommand for profile module")

play_parser = Cmd2ArgumentParser()
play_parser.add_argument("-v",
                         "--verbose",
                         action="store_true",
                         help="print disabled section tasks")
play_parser.add_argument("-c",
                         "--color",
                         action="store_true",
                         help="enable colorized output")
play_parser.add_argument("preset",
                         nargs="*",
                         choices_provider=_choices_presets,
                         help="preset(s) to be played, default to all")

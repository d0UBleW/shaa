from __future__ import annotations

from cmd2 import Cmd2ArgumentParser

clear_parser = Cmd2ArgumentParser()

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

profile_parser = Cmd2ArgumentParser()
profile_parser.add_subparsers(title="subcommands",
                              help="subcommand for profile module")

#!/usr/bin/env python3

from cmd2 import Cmd2ArgumentParser

inventory_parser = Cmd2ArgumentParser()
inventory_parser.add_subparsers(title="action", help="action on inventory")

inventory_node_parser = Cmd2ArgumentParser()
inventory_node_parser.add_subparsers(title="action",
                                     help="action on inventory node")

inventory_group_parser = Cmd2ArgumentParser()
inventory_group_parser.add_subparsers(title="action",
                                      help="action on inventory group")

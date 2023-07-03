from __future__ import annotations

from typing import Any, List, Optional, Text


class ShaaVaultError(Exception):
    pass


class ShaaInventoryError(Exception):
    pass


class InvalidGroupOp(ShaaInventoryError):
    def __init__(self, name: Text, message: Optional[Text] = None):
        self.message = f"Action is not valid for group `{name}`"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class GroupNameNotFound(ShaaInventoryError):
    def __init__(self, name: Text, message: Optional[Text] = None):
        self.message = f"Invalid group, name not found: {name}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class GroupNameExist(ShaaInventoryError):
    def __init__(self, name: Text, message: Optional[Text] = None):
        self.message = f"Specified group name already exists: {name}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class NodeNameNotFound(ShaaInventoryError):
    def __init__(self, name: Text, message: Optional[Text] = None):
        self.message = f"Invalid node, name not found: {name}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class NodeNameExist(ShaaInventoryError):
    def __init__(self, name: Text, message: Optional[Text] = None):
        self.message = f"Specified node name already exists: {name}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class ShaaVariableError(Exception):
    pass


class ValueNotInChoice(ShaaVariableError):
    def __init__(self,
                 val: Any,
                 allowed: List[Text],
                 message: Optional[Text] = None):
        self.message = f"Invalid value, not in allowed choices: {val}\n"
        self.message += f"    Allowed: {', '.join(allowed)}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class ValueNotNumber(ShaaVariableError):
    def __init__(self, val: Any, message: Optional[Text] = None):
        self.message = f"Invalid value, number is expected: {val}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class ValueIsLower(ShaaVariableError):
    def __init__(self, val: int, bound: int, message: Optional[Text] = None):
        self.message = f"Supplied value is lower than allowed value: {val}\n"
        self.message += f"    Min: {bound}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class ValueIsHigher(ShaaVariableError):
    def __init__(self, val: int, bound: int, message: Optional[Text] = None):
        self.message = f"Supplied value is higher than allowed value: {val}\n"
        self.message += f"    Max: {bound}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class ShaaNameError(Exception):
    pass


class InvalidFile(ShaaNameError):
    def __init__(self, ctx: Text, arg: Text, message: Optional[Text] = None):
        self.message = f"Invalid {ctx} file: missing `{arg}` key"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class InvalidName(ShaaNameError):
    def __init__(self, ctx: Text, name: Text, message: Optional[Text] = None):
        self.message = f"Invalid {ctx} name: {name}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class NameExist(ShaaNameError):
    def __init__(self, ctx: Text, name: Text, message: Optional[Text] = None):
        self.message = f"Specified {ctx} name already exists: {name}"
        if message is not None:
            self.message = message

        super().__init__(self.message)


class NameNotFound(ShaaNameError):
    def __init__(self, ctx: Text, name: Text, message: Optional[Text] = None):
        self.message = f"{ctx} name not found: {name}"
        if message is not None:
            self.message = message

        super().__init__(self.message)

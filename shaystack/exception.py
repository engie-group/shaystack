"""
Specific exceptions for Haystack API
"""


class HaystackException(Exception):
    """
    Exception when the haystack protocol have a problem.

    Parameters:
        msg: The error message
    """

    def __init__(self, msg: str):  # pylint: disable=useless-super-delegation
        # Call the base class constructor with the parameters it needs
        super().__init__(msg)

    @property
    def msg(self) -> str:
        return self.args[0]

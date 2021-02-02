class HaystackException(Exception):
    def __init__(self, msg):
        # Call the base class constructor with the parameters it needs
        super().__init__(msg)

    @property
    def msg(self) -> str:
        return self.args[0]

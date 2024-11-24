class CPrecisionTimer:
    def __init__(self, precision: str = ...) -> None:
        """__init__(self, precision: str = 'us') -> None"""
    def DelayBlock(self, duration: int, allow_sleep: bool = ...) -> None:
        """DelayBlock(self, duration: int, allow_sleep: bool = False) -> None

        Delays for the requested period of time without releasing GIL"""
    def DelayNoblock(self, duration: int, allow_sleep: bool = ...) -> None:
        """DelayNoblock(self, duration: int, allow_sleep: bool = False) -> None

        Delays for the requested period of time while releasing GIL"""
    def Elapsed(self) -> int:
        """Elapsed(self) -> int

        Reports the elapsed time since the last reset() method call or class instantiation (whichever happened last)."""
    def GetPrecision(self) -> str:
        """GetPrecision(self) -> str

        Returns the current precision of the timer."""
    def Reset(self) -> None:
        """Reset(self) -> None

        Resets the reference point of the class to the current time."""
    def SetPrecision(self, precision: str) -> None:
        """SetPrecision(self, precision: str) -> None

        Sets the class precision to new units."""

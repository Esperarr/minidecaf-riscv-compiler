from typing import List
from utils.label.funclabel import FuncLabel
from utils.tac.temp import Temp

"""
SubroutineInfo: collect some info when selecting instr which will be used in SubroutineEmitter
"""


class SubroutineInfo:
    def __init__(self, funcLabel: FuncLabel, numArgs: int, args_temp: List[Temp]) -> None:
        self.funcLabel = funcLabel
        self.numArgs = numArgs
        self.args_temp = args_temp

    def __str__(self) -> str:
        return "funcLabel: {}".format(
            self.funcLabel.name,
        )

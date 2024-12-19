from frontend.symbol.varsymbol import VarSymbol
from utils.label.funclabel import FuncLabel
from utils.tac.temp import Temp

from .tacinstr import TACInstr


class TACFunc:
    def __init__(self, entry: FuncLabel, numArgs: int) -> None:
        self.entry = entry
        self.numArgs = numArgs
        self.instrSeq = []
        self.tempUsed = 0
        self.args_temp=[]
        self.arg_type_info = {}

    def getInstrSeq(self) -> list[TACInstr]:
        return self.instrSeq

    def getUsedTempCount(self) -> int:
        return self.tempUsed

    def add(self, instr: TACInstr) -> None:
        self.instrSeq.append(instr)

    def printTo(self) -> None:
        for instr in self.instrSeq:
            if instr.isLabel():
                print(instr)
            else:
                print("    " + str(instr))
    
    def add_arg(self, arg: VarSymbol) -> None:
        self.args_temp.append(arg.temp)
        self.arg_type_info[arg.name] = arg.type

    def get_args(self) -> list[Temp]:
        return self.args_temp

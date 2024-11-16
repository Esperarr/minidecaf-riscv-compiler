from typing import Optional

from frontend.symbol.symbol import Symbol

from .scope import Scope

class ScopeStack:
    def __init__(self, GlobalScope: Scope) -> None:
        self.scopes: list[Scope] = []# stack of scopes
        self.scopes.append(GlobalScope)
        self.current_scope: Scope = GlobalScope# top
        self.global_scope: Scope = GlobalScope# bottom
        self.loop_num = 0
    def start_loop(self) -> None:
        self.loop_num += 1
    def end_loop(self) -> None:
        self.loop_num -= 1
    def get_loop_num(self) -> int:
        return self.loop_num
    def in_loop(self) -> bool:
        return self.loop_num > 0
    def open(self, scope: Scope) -> None:
        self.scopes.append(scope)
        self.current_scope = scope
    def close(self) -> None:
        if(len(self.scopes)>0):
            self.scopes.pop()
            self.current_scope = self.scopes[-1]
        else:
            raise Exception("ScopeStack is empty")
    def current_scope(self) -> Scope:
        return self.current_scope
    def global_scope(self) -> Scope:
        return self.global_scope
    def lookup_all(self, name: str) -> Optional[Symbol]:
        for scope in reversed(self.scopes):
            symbol = scope.lookup(name)
            if symbol is not None:
                return symbol
        return None
    def lookup_current(self, name: str) -> Optional[Symbol]:
        return self.current_scope.lookup(name)
    def declare(self, symbol: Symbol) -> None:
        self.current_scope.declare(symbol)
    
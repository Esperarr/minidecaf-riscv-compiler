from typing import Protocol, TypeVar, cast

from frontend.ast.node import Node, NullType
from frontend.ast.tree import *
from frontend.ast.visitor import RecursiveVisitor, Visitor
from frontend.scope.globalscope import GlobalScope
from frontend.scope.scope import Scope, ScopeKind
from frontend.scope.scopestack import ScopeStack
from frontend.symbol.funcsymbol import FuncSymbol
from frontend.symbol.symbol import Symbol
from frontend.symbol.varsymbol import VarSymbol
from frontend.type.array import ArrayType
from frontend.type.type import DecafType
from utils.error import *
from utils.riscv import MAX_INT

"""
The namer phase: resolve all symbols defined in the abstract 
syntax tree and store them in symbol tables (i.e. scopes).
"""


class Namer(Visitor[ScopeStack, None]):
    def __init__(self) -> None:
        pass

    # Entry of this phase
    def transform(self, program: Program) -> Program:
        # Global scope. You don't have to consider it until Step 6.
        program.globalScope = GlobalScope
        ctx = ScopeStack(program.globalScope)

        program.accept(self, ctx)
        return program

    def visitProgram(self, program: Program, ctx: ScopeStack) -> None:
        # Check if the 'main' function is missing
        if not program.hasMainFunc():
            raise DecafNoMainFuncError
        
        func_name_list=[]
        for function in program.children:
            function_name=function.ident.value
            if function_name in func_name_list:
                raise DecafDeclConflictError(function_name)
            else:
                func_name_list.append(function.ident.value)
                
        for func in program.functions().values():
            func.accept(self, ctx)

    def visitFunction(self, func: Function, ctx: ScopeStack) -> None:
        func_name=func.ident.value
        func_type=func.ret_t
        func_param_list=func.params
        func_body=func.body
        conflict_symbol=ctx.lookup_all(func_name)
        if conflict_symbol:# func already decleared
            if isinstance(conflict_symbol, FuncSymbol) and conflict_symbol.isFunc():
                if conflict_symbol.type == func_type:# same type
                    if conflict_symbol.defined == True:# func already defined
                        raise DecafDeclConflictError(func_name)
                    else:# func not defined yet
                        if func_body:
                            conflict_symbol.defined = True
                else:# different type
                    raise DecafDeclConflictError(func_name)
        else:# func not decleared yet
            func_symbol = FuncSymbol(func_name, func_type, GlobalScope)
            for param in func_param_list:
                param_type=param.var_type
                func_symbol.addParaType(param_type)
            GlobalScope.declare(func_symbol)
            func.setattr('symbol', func_symbol)
            if func_body:# define func
                func_symbol.defined = True
        ctx.open(Scope(ScopeKind.LOCAL))
        for param in func_param_list:
            param.accept(self, ctx)
        for child in func_body:
            child.accept(self, ctx)
        ctx.close()


    def visitCall(self, call: Call, ctx: ScopeStack) -> None:
        func_symbol=ctx.lookup_all(call.ident.value)
        if not func_symbol or not isinstance(func_symbol, FuncSymbol) or not func_symbol.isFunc or func_symbol.defined == False:
            raise DecafUndefinedFuncError(call.ident.value)
        if not (len(call.argument_list) == func_symbol.parameterNum):
           raise DecafBadFuncCallError
        call.ident.setattr('symbol', func_symbol)
        for arg in call.argument_list:
            arg.accept(self, ctx)

    def visitBlock(self, block: Block, ctx: ScopeStack) -> None:
        ctx.open(Scope(ScopeKind.LOCAL))
        for child in block:
            child.accept(self, ctx)
        ctx.close()

    def visitReturn(self, stmt: Return, ctx: ScopeStack) -> None:
        stmt.expr.accept(self, ctx)

    """
    def visitFor(self, stmt: For, ctx: Scope) -> None:

    1. Open a local scope for stmt.init.
    2. Visit stmt.init, stmt.cond, stmt.update.
    3. Open a loop in ctx (for validity checking of break/continue)
    4. Visit body of the loop.
    5. Close the loop and the local scope.
    """
    def visitFor(self, stmt: For, ctx: ScopeStack) -> None:
        ctx.open(Scope(ScopeKind.LOCAL))
        if stmt.init:
            stmt.init.accept(self, ctx)
        if stmt.cond:
            stmt.cond.accept(self, ctx)
        if stmt.update:
            stmt.update.accept(self, ctx)
        ctx.start_loop()
        stmt.body.accept(self, ctx)
        ctx.end_loop()
        ctx.close()

    def visitIf(self, stmt: If, ctx: ScopeStack) -> None:
        stmt.cond.accept(self, ctx)
        stmt.then.accept(self, ctx)

        # check if the else branch exists
        if not stmt.otherwise is NULL:
            stmt.otherwise.accept(self, ctx)

    def visitWhile(self, stmt: While, ctx: ScopeStack) -> None:
        stmt.cond.accept(self, ctx)
        ctx.start_loop()
        stmt.body.accept(self, ctx)
        ctx.end_loop()

    def visitBreak(self, stmt: Break, ctx: ScopeStack) -> None:
        """
        You need to check if it is currently within the loop.
        To do this, you may need to check 'visitWhile'.

        if not in a loop:
            raise DecafBreakOutsideLoopError()
        """
        if not ctx.in_loop():
            raise DecafBreakOutsideLoopError()
        ctx.end_loop()
        # raise NotImplementedError

    """
    def visitContinue(self, stmt: Continue, ctx: Scope) -> None:
    
    1. Refer to the implementation of visitBreak.
    """
    def visitContinue(self, stmt: Continue, ctx: Scope) -> None:
        if not ctx.in_loop():
            raise DecafContinueOutsideLoopError()

    def visitDeclaration(self, decl: Declaration, ctx: ScopeStack) -> None:
        """
        1. Use ctx.lookup to find if a variable with the same name has been declared.
        2. If not, build a new VarSymbol, and put it into the current scope using ctx.declare.
        3. Set the 'symbol' attribute of decl.
        4. If there is an initial value, visit it.
        """
        symbol=ctx.lookup_current(decl.ident.value) # lookup in current zone
        if symbol is not None:
            raise DecafDeclConflictError(decl.ident.value)
        else:
            symbol=VarSymbol(decl.ident.value,decl.var_t,False)
            ctx.declare(symbol)
            decl.setattr('symbol',symbol)
            if decl.init_expr is not None:
                decl.init_expr.accept(self,ctx)
        # raise NotImplementedError

    def visitParameter(self, param: Parameter, ctx: ScopeStack) -> None:
        """
        1. Use ctx.lookup to find if a variable with the same name has been declared.
        2. If not, build a new VarSymbol, and put it into the current scope using ctx.declare.
        3. Set the 'symbol' attribute of decl.
        """
        symbol=ctx.lookup_current(param.ident.value) # lookup in current zone
        if symbol is not None:
            raise DecafDeclConflictError(param.ident.value)
        else:
            symbol=VarSymbol(param.ident.value,param.var_type,False)
            ctx.declare(symbol)
            param.setattr('symbol',symbol)

    def visitAssignment(self, expr: Assignment, ctx: ScopeStack) -> None:
        """
        1. Refer to the implementation of visitBinary.
        """
        symbol=ctx.lookup_all(expr.lhs.value)# lookup overall
        if symbol is None:
            raise DecafUndefinedVarError(expr.lhs.value)
        else:
            expr.lhs.accept(self,ctx)
            expr.rhs.accept(self,ctx)
        # raise NotImplementedError

    def visitUnary(self, expr: Unary, ctx: ScopeStack) -> None:
        expr.operand.accept(self, ctx)

    def visitBinary(self, expr: Binary, ctx: ScopeStack) -> None:
        expr.lhs.accept(self, ctx)
        expr.rhs.accept(self, ctx)

    def visitCondExpr(self, expr: ConditionExpression, ctx: ScopeStack) -> None:
        """
        1. Refer to the implementation of visitBinary.
        """
        expr.cond.accept(self, ctx)
        expr.then.accept(self, ctx)
        expr.otherwise.accept(self, ctx)
        # raise NotImplementedError

    def visitIdentifier(self, ident: Identifier, ctx: ScopeStack) -> None:
        """
        1. Use ctx.lookup to find the symbol corresponding to ident.
        2. If it has not been declared, raise a DecafUndefinedVarError.
        3. Set the 'symbol' attribute of ident.
        """
        symbol=ctx.lookup_all(ident.value)# lookup overall
        if symbol is None:
            raise DecafUndefinedVarError(ident.value)
        else:
            ident.setattr('symbol',symbol)
        # raise NotImplementedError

    def visitIntLiteral(self, expr: IntLiteral, ctx: ScopeStack) -> None:
        value = expr.value
        if value > MAX_INT:
            raise DecafBadIntValueError(value)

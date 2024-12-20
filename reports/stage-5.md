
### MiniDecaf-Stage5 报告
周轻扬 2022012166 计24

##### 实验内容

1. 词法分析、语义分析
    - 在`frontend/ast/tree.py`中添加`Parameter`和`Call` AST节点的定义
    ```python
        class Parameter(Node):
          """
          AST node that represents a parameters
          """
          def __init__(self, var_type: TypeLiteral, ident: Identifier):
              super().__init__("parameter")
              self.var_type=var_type
              self.ident=ident
          def __getitem__(self, key: int) -> Node:
              return (self.var_type, self.ident)[key]
          def __len__(self) -> int:
              return 2
          def accept(self, v: Visitor[T, U], ctx: T):
              return v.visitParameter(self, ctx)
          
      class Call(Node):
          """
          AST node that represents a call
          """
          def __init__(self, ident: Identifier, argument_list: List[Parameter]):
              super().__init__("call")
              self.ident=ident
              self.argument_list=argument_list
          def __getitem__(self, key: int) -> Node:
              return (self.ident, *self.argument_list)[key]
          def __len__(self) -> int:
              return len(self.argument_list)+1
          def accept(self, v: Visitor[T, U], ctx: T):
              return v.visitCall(self, ctx)
    ```
    并且修改Function节点，为其添加函数参数列表params变量
    ```python
        class Function(Node):
          """
          AST node that represents a function.
          """

          def __init__(
              self,
              ret_t: TypeLiteral,
              ident: Identifier,
              params: List[Parameter],
              body: Block,
          ) -> None:
              super().__init__("function")
              self.ret_t = ret_t
              self.ident = ident
              self.params = params
              self.body = body

          def __getitem__(self, key: int) -> Node:
              return (
                  self.ret_t,
                  self.ident,
                  *self.params,
                  self.body,
              )[key]

          def __len__(self) -> int:
              return 3+len(self.params)

          def accept(self, v: Visitor[T, U], ctx: T):
              return v.visitFunction(self, ctx)
    ```
    - 在`frontend/ast/visitor.py`中添加`visitFor`和`visitContinue`函数
    ```python
         def visitParameter(self, that:Parameter, ctx:T) -> Optional[U]:
            return self.visitOther(that, ctx)
    
        def visitCall(self, that:Call, ctx:T) -> Optional[U]:
            return self.visitOther(that, ctx)

    ```
    - 在`frontend/lexer/lex.py`中添加为处理函数参数列表的符号','
    ```python
        t_Comma = ","
    ```
    - 在`frontend/parser/ply_parser.py`中实现对函数定义、声明、调用的语法分析。
    对于一个程序progeram，可以有多个函数，也可以没有函数，分别在p_program和p_program_empty里处理；对于函数，可以有一个或多个参数，也可以没有参数，分别在p_param_list_single、p_param_list_more、p_param_list_empty里处理。
    ```python
      def p_program_empty(p):
          """
          program : empty
          """
          p[0] = Program()


      def p_program(p):
          """
          program : program function
          """
          if p[2] is not NULL:
              p[1].children.append(p[2])
          p[0] = p[1]

      def p_function_def(p):
          """
          function : type Identifier LParen param_list RParen LBrace block RBrace
          """
          p[0] = Function(p[1], p[2], p[4], p[7])

      def p_function_declear(p):
          """
          function : type Identifier LParen param_list RParen Semi
          """
          p[0] = Function(p[1], p[2], p[4], None)

      def p_function_call(p):
          """
          postfix : Identifier LParen expression_list RParen
          """
          p[0] = Call(p[1], p[3])

      def p_param_list_single(p):
          """
          param_list : param
          """
          p[0] = [p[1]]

      def p_param_list_more(p):
          """
          param_list : param Comma param_list
          """
          p[0] = [p[1]] + p[3]

      def p_param_list_empty(p):
          """
          param_list : empty
          """
          p[0] = []
          
      def p_param(p):
          """
          param : type Identifier
          """
          p[0] = Parameter(p[1], p[2])
    ```
    - 在`frontend/symbol/funcsymbol.py`中为FuncSymbol添加函数是否已经被定义的属性，便于在语义检查阶段进行检查。
    ```python
        class FuncSymbol(Symbol):
          def __init__(self, name: str, type: DecafType, scope: Scope) -> None:
              super().__init__(name, type)
              self.scope = scope
              self.para_type = []
              self.defined = False
    ```
    - 在`frontend/typecheck/namer.py`中，实现visitFunction、visitCall、visitParameter函数。依据实验指导书的逻辑进行检查和处理。
    其中visitFunction函数检查当前scope中是否有同名函数，若存在且类型相同，则若其已经被定义，则报错，否则将其定义为已定义(defined=True)；若存在且类型不同，则报错；若不存在，则将其声明为函数，并添加到当前scope中，若其有函数体，则将其定义为已定义(defined=True)。
    visitCall检查传入参数和函数参数数目是否相同
    visitParameter仿照visitDeclaration实现
    ```python
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
    ```
2. TAC生成
   - 在`utils/tac/tacop.py`的InstrKind中添加CaLL类型`CALL = auto()`
   - 在`utils/tac/tacinstr.py`中添加Call节点定义。
    ```python
        class Call(TACInstr):
          def __init__(self, dst:Temp, func: Label, args: List[Temp]) -> None:
              super().__init__(InstrKind.CALL, [dst], args, func)
              self.dst=dst
              self.func=func
              self.args=args

          def __str__(self) -> str:
              arguments=[str(arg) for arg in self.args]
              return "%s = CALL %s(%s)" % (self.dst, self.label.name, ", ".join(arguments))
          
          def accept(self, v: TACVisitor) -> None:
              v.visitCall(self)

    ```
    - 在`frontend/tacgen/tacgen.py`中，在TACGen实现visitParameter、visitFunction、visitCall函数。
    ```python
        def visitParameter(self, param: Parameter, mv:TACFuncEmitter) -> None:
           symbol= param.getattr("symbol")
           symbol.temp= mv.freshTemp()
           # print("symbol.temp:",symbol.temp)

       def visitFunction(self, func: Function, mv: TACFuncEmitter) -> None:
           for param in func.params:
               param.accept(self, mv)
           func.body.accept(self, mv)
       
       def visitCall(self, call: Call, mv: TACFuncEmitter) -> None:
           dst=mv.freshTemp()
           call.setattr('val', dst) 
           func_name=call.ident.value
           func=FuncLabel(func_name)
           for arg in call.argument_list:
               arg.accept(self, mv)
           mv.visitCall(dst, func, args=[arg.getattr("val") for arg in call.argument_list])
    ```
    并且修改TACGen中的transform函数
    ```python
      def transform(self, program: Program) -> TACProg:
          labelManager = LabelManager()
          tacFuncs = []
          for funcName, astFunc in program.functions().items():
              # in step9, you need to use real parameter count
              emitter = TACFuncEmitter(FuncLabel(funcName), len(astFunc.params), labelManager)
              ...
    ```
    在TACFuncEmitter中，实现visitCall
    ```python
         def visitCall(self, dst:Temp, func: Label, args: List[Temp]) -> None:
           self.func.add(Call(dst, func, args))
    ```
3. 汇编生成
    - 在`utils/riscv.py`中添加`Call`和`FPAdd` 节点的定义，其中FPAdd仿照SPAdd节点实现，用于维护fp
    ```python
        class FPAdd(BackendInstr):
            def __init__(self, offset: int) -> None:
                super().__init__(InstrKind.SEQ, [Riscv.FP], [Riscv.SP], None)
                self.offset = offset

            def __str__(self) -> str:
                assert -2048 <= self.offset <= 2047  # Riscv imm [11:0]
                return "addi " + Riscv.FMT3.format(
                    str(Riscv.FP), str(Riscv.SP), str(self.offset)
                )
            
        class Call(BackendInstr):
            def __init__(self, target: Label) -> None:
                super().__init__(InstrKind.CALL, [], [], target)
                self.target = target

            def __str__(self) -> str:
                return "call " + str(self.target)

    ```
    - 在`backend/riscv/riscvasmemitter.py`RiscvSubroutineEmitter类中修改添加`emitFunc`函数，对ra，fp进行维护
    ```python
        self.printer.printInstr(Riscv.NativeStoreWord(Riscv.RA, Riscv.SP, 4*len(Riscv.CalleeSaved)))
        self.printer.printInstr(Riscv.NativeStoreWord(Riscv.FP, Riscv.SP, 4*len(Riscv.CalleeSaved)+4))
        self.printer.printInstr(Riscv.FPAdd(self.nextLocalOffset))
        ...
        self.printer.printInstr(Riscv.NativeLoadWord(Riscv.RA, Riscv.SP, 4*len(Riscv.CalleeSaved)))
        self.printer.printInstr(Riscv.NativeLoadWord(Riscv.FP, Riscv.SP, 4*len(Riscv.CalleeSaved)+4))
        ...
    ```
    - 在`backend/reg/bruteregalloc.py`中添加对后端寄存器分配的逻辑，涉及CallerSaved寄存器的维护和函数参数寄存器的维护
    ```python
          def accept(self, graph: CFG, info: SubroutineInfo) -> None:
              subEmitter = RiscvSubroutineEmitter(self.emitter, info)
              for i in range(info.numArgs):
                  self.bind(info.args_temp[i],Riscv.ArgRegs[i])
              for bb in graph.iterator():
                  # you need to think more here
                  # maybe we don't need to alloc regs for all the basic blocks
                  if graph.is_unreachable(bb.id):
                      continue
                  if bb.label is not None:
                      subEmitter.emitLabel(bb.label)
                  self.localAlloc(bb, subEmitter)
              subEmitter.emitFunc()
    ```
    ```python
             if isinstance(instr, Riscv.Call):
              for caller_saved_reg in Riscv.CallerSaved:
                  if caller_saved_reg.isUsed():
                      subEmitter.emitStoreToStack(caller_saved_reg)
                      temp = caller_saved_reg.temp
                      if temp is not None:
                          self.unbind(temp)

    ```
##### 思考题
1. 你更倾向采纳哪一种中间表示中的函数调用指令的设计（一整条函数调用 vs 传参和调用分离）？写一些你认为两种设计方案各自的优劣之处。
   
   答：更倾向于第一种方案，即一整条函数调用指令。因为第一种方案将函数调用过程进行封装，使用一条CALL指令实现，更符合函数调用的语义，而第二种方案需要先执行传参指令，再执行函数调用指令，增加了指令数量，降低了效率，可读性也不如第一种方法。
2. 为何 RISC-V 标准调用约定中要引入 callee-saved 和 caller-saved 两类寄存器，而不是要求所有寄存器完全由 caller/callee 中的一方保存？为何保存返回地址的 ra 寄存器是 caller-saved 寄存器？

    答：
    - 如果全部由一方保存，则可能会保存很多实际上不必要的寄存器，保存、恢复、维护寄存器的开销会很大。因此应把寄存器拆分为两类保存，callee-saved寄存器保存函数调用后不再用到的值，而caller-saved寄存器保存函数调用后仍然有效且可能用到的值，如当前返回地址，因此可以减少保存、恢复、维护寄存器的开销，提升效率。
    - 因为在调用函数时，jalr指令会修改ra寄存器，寄存器的值会变成调用的函数的返回地址，而其中存储的当前的返回地址会被覆盖，因此如需要保存当前的返回地址，则需要再进入调用的函数之前进行保存，即caller-saved

##### 参考资料
后端生成汇编的部分代码和张宁远同学进行了讨论
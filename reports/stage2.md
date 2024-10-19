### MiniDecaf-Stage2 报告
周轻扬 2022012166 计24

##### 实验内容
主要增加了变量，实现了变量声明和变量使用（读取、赋值）功能
1. 在语义分析部分的代码中，在`fronted/typecheck/namer.py`中补全了`visitDeclaration`、`visitAssignment`、`visitIdentifier`函数，分别用于处理声明语句、赋值语句、标识符
   - `visitDeclaration`首先在对应Scope中查找是否存在同名变量，若存在则抛出异常，否则新建一个VarSymbol，并添加到当前Scope中，最后使用setattr将symbol赋值给decl的symbol属性，在有init_expr式时继续访问init_expr
        ```python
          def visitDeclaration(self, decl: Declaration, ctx: Scope) -> None:
            """
            1. Use ctx.lookup to find if a variable with the same name has been declared.
            2. If not, build a new VarSymbol, and put it into the current scope using ctx.declare.
            3. Set the 'symbol' attribute of decl.
            4. If there is an initial value, visit it.
            """
             symbol=ctx.lookup(decl.ident.value)
             if symbol is not None:
                 raise DecafDeclConflictError(decl.ident.value)
             else:
                 symbol=VarSymbol(decl.ident.value,decl.var_t,False)
                 ctx.declare(symbol)
                 decl.setattr('symbol',symbol)
                 if decl.init_expr is not None:
                   decl.init_expr.accept(self,ctx)
        ```
    - `visitAssignment`首先在Scope中查找赋值语句左式标识符是否被定义过，若未定义则抛出异常，否则分别访问左式和右式
        ```python
          def visitAssignment(self, expr: Assignment, ctx: Scope) -> None:
            """
            1. Refer to the implementation of visitBinary.
            """
             symbol=ctx.lookup(expr.lhs.value)
             if symbol is None:
                 raise DecafUndefinedVarError(expr.lhs.value)
             else:
                 expr.lhs.accept(self,ctx)
                 expr.rhs.accept(self,ctx)
        ```
    - `visitIdentifier`首先在Scope中查找标识符是否被定义过，若未定义则抛出异常，否则使用setattr将symbol赋值给ident的symbol属性
        ```python
          def visitIdentifier(self, ident: Identifier, ctx: Scope) -> None:
            """
            1. Use ctx.lookup to find the symbol corresponding to ident.
            2. If it has not been declared, raise a DecafUndefinedVarError.
            3. Set the 'symbol' attribute of ident.
            """
            symbol=ctx.lookup(ident.value)
            if symbol is None:
                raise DecafUndefinedVarError(ident.value)
            else:
                ident.setattr('symbol',symbol)
        ```
2. 在生成TAC码部分的代码中，在`fronted/tacgen/tacgen.py`中补全了`visitDeclaration`、`visitAssignment`、`visitIdentifier`函数，分别用于处理声明语句、赋值语句、标识符
    - `visitIdentifier`设置ident的val属性为ident的symbol的temp属性
        ```python
          def visitIdentifier(self, ident: Identifier, mv: TACFuncEmitter) -> None:
            """
            1. Set the 'val' attribute of ident as the temp variable of the 'symbol' attribute of ident.
            """
            ident.setattr("val", ident.getattr("symbol").temp)
        ```
    - `visitDeclaration`中为decl的对应symbol分配一个新temp变量，若有init_expr则继续访问init_expr，计算出其val属性后，使用mv.visitAssignment生成赋值语句，将init_expr对应的temp变量赋值到symbol的temp变量，并在最后设置decl的val属性
        ```python
          def visitDeclaration(self, decl: Declaration, mv: TACFuncEmitter) -> None:
            """
            1. Get the 'symbol' attribute of decl.
            2. Use mv.freshTemp to get a new temp variable for this symbol.
            3. If the declaration has an initial value, use mv.visitAssignment to set it.
            """
            symbol= decl.getattr("symbol")
            symbol.temp= mv.freshTemp()
            if decl.init_expr is not NULL:
                decl.init_expr.accept(self, mv)
                val=mv.visitAssignment(symbol.temp, decl.init_expr.getattr("val"))
                decl.setattr("val", val)
        ```
    - `visitAssignment`访问赋值语句的左式和右式，分别计算出其val属性后，使用mv.visitAssignment生成赋值语句，将左式对应的temp变量赋值为右式对应的temp变量，并在最后设置decl的val属性
        ```python
          def visitAssignment(self, expr: Assignment, mv: TACFuncEmitter) -> None:
            """
            1. Visit the right hand side of expr, and get the temp variable of left hand side.
            2. Use mv.visitAssignment to emit an assignment instruction.
            3. Set the 'val' attribute of expr as the value of assignment instruction.
            """
            expr.rhs.accept(self, mv)
            expr.lhs.accept(self, mv)
            val=mv.visitAssignment(expr.lhs.getattr("val"), expr.rhs.getattr("val"))
            expr.setattr("val", val)
        ```
3. 在生成riscv汇编代码部分的代码中，在`backend/riscv/riscvasmemitter.py`中添加了`visitAssign`函数，对于赋值语句生成Move指令
   ```python
      def visitAssign(self, instr: Assign) -> None:
            self.seq.append(Riscv.Move(instr.dst, instr.src))
   ```

##### 思考题
1. 我们假定当前栈帧的栈顶地址存储在 sp 寄存器中，请写出一段 risc-v 汇编代码，将栈帧空间扩大 16 字节。（提示1：栈帧由高地址向低地址延伸；提示2：risc-v 汇编中 addi reg0, reg1, <立即数> 表示将 reg1 的值加上立即数存储到 reg0 中。）
      答：`addi sp,sp,-16`
2. 有些语言允许在同一个作用域中多次定义同名的变量，例如这是一段合法的 Rust 代码（你不需要精确了解它的含义，大致理解即可）：
   ```rust
      fn main() {
        let a = 0;
        let a = f(a);
        let a = g(a);
      }
   ```
   其中f(a)中的a是上一行的let a = 0;定义的，g(a)中的a是上一行的let a = f(a);。

   如果 MiniDecaf 也允许多次定义同名变量，并规定新的定义会覆盖之前的同名定义，请问在你的实现中，需要对定义变量和查找变量的逻辑做怎样的修改？（提示：如何区分一个作用域中不同位置的变量定义？）
       答：
        在定义变量时，在`visitDeclaration`有init_expr的情况和`visitAssignment`时先访问右式，计算得到相应的symbol之后再进行相应Identifier/左式的赋值，并覆盖先前值，从而可以实现在语义检查、定义变量时，用新的定义覆盖之前的同名定义。并且，`fronted/typecheck/namer.py/visitDeclaration`不检查重复定义的错误，因为rust中可以重复定义同名变量；在查找变量时，逻辑不变。因为新的定义已经覆盖了原先定义，使用`visitIdentifier`查找到的当前Scope中相应的symbol即为当前变量对应的正确symbol。

##### 参考资料
无
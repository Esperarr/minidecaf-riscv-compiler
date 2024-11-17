
### MiniDecaf-Stage4 报告
周轻扬 2022012166 计24

##### 实验内容
1. step7
   - 在语义分析部分代码中，在`frontend/typecheck/namer.py`中添加对于条件表达式分析的代码，实现visitCondExpr。参考visitIf实现。
     ```python
         def visitCondExpr(self, expr: ConditionExpression, ctx: ScopeStack) -> None:
            """
            1. Refer to the implementation of visitBinary.
            """
            expr.cond.accept(self, ctx)
            expr.then.accept(self, ctx)
            expr.otherwise.accept(self, ctx)
     ```
     与visitIf类似，但不需要考虑otherwise为空的情况，
   - 在生成中间TAC部分的代码中，在`frontend/tacgen/tacgen.py`中添加对于条件表达式分析的代码，实现visitCondExpr。参考visitIf实现。
     ```python
        def visitCondExpr(self, expr: ConditionExpression, mv: TACFuncEmitter) -> None:
          """
          1. Refer to the implementation of visitIf and visitBinary.
          """
          expr.cond.accept(self, mv)
          expr_temp = mv.freshTemp()
          skipLabel = mv.freshLabel()
          exitLabel = mv.freshLabel()
          mv.visitCondBranch(
              tacop.CondBranchOp.BEQ, expr.cond.getattr("val"), skipLabel
          )
          expr.then.accept(self, mv)
          mv.visitAssignment(expr_temp, expr.then.getattr("val"))
          mv.visitBranch(exitLabel)
          mv.visitLabel(skipLabel)
          expr.otherwise.accept(self, mv)
          mv.visitAssignment(expr_temp, expr.otherwise.getattr("val"))
          mv.visitLabel(exitLabel)
          expr.setattr("val", expr_temp)
     ```
     与visitIf类似，但不需要考虑otherwise为空的情况，且需要给expr的val赋值为相应then或otherwise的val。
2. step8
   1. 词法分析、语义分析
      - 在`frontend/ast/tree.py`中添加`For`和`Continue` AST节点的定义
        仿照While节点实现For节点
        ```python
           class For(Statement):
             """
             AST node of for statement.
             """

             def __init__(self, init: Expression, cond: Expression, update: Expression, body: Statement) -> None:
                 super().__init__("for")
                 self.init = init
                 self.cond = cond
                 self.update = update
                 self.body = body

             def __getitem__(self, key: int) -> Node:
                 return (self.init, self.cond, self.update, self.body)[key]

             def __len__(self) -> int:
                 return 4

             def accept(self, v: Visitor[T, U], ctx: T):
                 return v.visitFor(self, ctx)
        ```
        仿照Break节点实现Continue节点
        ```python
        class Continue(Statement):
           """
           AST node of continue statement.
           """

           def __init__(self) -> None:
               super().__init__("continue")

           def __getitem__(self, key: int) -> Node:
               raise _index_len_err(key, self)

           def __len__(self) -> int:
               return 0

           def accept(self, v: Visitor[T, U], ctx: T):
               return v.visitContinue(self, ctx)

           def is_leaf(self):
               return True
        ```
      - 在`frontend/ast/visitor.py`中添加`visitFor`和`visitContinue`函数
        ```python
           def visitFor(self, that: For, ctx: T) -> Optional[U]:
              return self.visitOther(that, ctx)
           def visitFor(self, that: For, ctx: T) -> Optional[U]:
              return self.visitOther(that, ctx)
        ```
      - 在`frontend/lexer/lex.py`中添加for和continue保留字
        ```python
           reserved = {
               ...
               "continue": "Continue",
               "for": "For",
           }
        ```
      - 在`frontend/parser/ply_parser.py`中实现对for和continue的语法分析。其中，for语句的init,cond,update部分均可为空。
        ```python
           def p_for(p):
               """
               statement_matched : For LParen init_expression Semi opt_expression Semi opt_expression RParen statement_matched
               statement_unmatched : For LParen init_expression Semi opt_expression Semi opt_expression RParen statement_unmatched
               """
               p[0] = For(p[3], p[5], p[7], p[9])

           def p_for_init_expression(p):
               """
               init_expression : declaration
               init_expression : expression
               init_expression : empty
               """
               p[0] = p[1]
               
           def p_continue(p):
               """
               statement_matched : Continue Semi
               """
               p[0] = Continue()
        ```
      - 在`frontend/scope/scopestack.py`中为ScopeStack增加当前loop层数的属性以及维护该属性的相应逻辑，在进入循环时loop_num+=1，退出循环时loop_num-=1。
        ```python
          class ScopeStack:
           def __init__(self, GlobalScope: Scope) -> None:
               ...
               self.loop_num = 0
           def start_loop(self) -> None:
               self.loop_num += 1
           def end_loop(self) -> None:
               self.loop_num -= 1
           def get_loop_num(self) -> int:
               return self.loop_num
           def in_loop(self) -> bool:
               return self.loop_num > 0
        ```
      - 在`frontend/typecheck/namer.py`中，参考相应注释，实现visitFor、visitWhile、visitBreak、visitContinue函数。利用新增的loop_num属性判断是否需要抛出DecafBreakOutsideLoopError和DecafContinueOutsideLoopError。注意for语句的init,cond,update部分均可为空，因此需要判断其是否为空。
        ```python
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
            def visitWhile(self, stmt: While, ctx: ScopeStack) -> None:
              stmt.cond.accept(self, ctx)
              ctx.start_loop()
              stmt.body.accept(self, ctx)
              ctx.end_loop()
            def visitBreak(self, stmt: Break, ctx: ScopeStack) -> None:
              """
              if not in a loop:
                  raise DecafBreakOutsideLoopError()
              """
              if not ctx.in_loop():
                  raise DecafBreakOutsideLoopError()
              ctx.end_loop()
            def visitContinue(self, stmt: Continue, ctx: Scope) -> None:
              if not ctx.in_loop():
                  raise DecafContinueOutsideLoopError()
        ```
    2. TAC生成
        在`frontend/tacgen/tacgen.py`中，实现visitFor、visitContinue函数。
        参考visitWhile实现visitFor，注意for语句的init,cond,update部分均可为空，因此需要判断其是否为空。
        ```python
            def visitFor(self, stmt: For, mv: TACFuncEmitter) -> None:
              beginLabel = mv.freshLabel()
              loopLabel = mv.freshLabel()
              breakLabel = mv.freshLabel()
              mv.openLoop(breakLabel, loopLabel)
              #init
              if stmt.init:
                  stmt.init.accept(self, mv)
              #_L1
              #begin
              mv.visitLabel(beginLabel)
              if stmt.cond:
                  stmt.cond.accept(self, mv)
                  mv.visitCondBranch(tacop.CondBranchOp.BEQ, stmt.cond.getattr("val"), breakLabel)
              #body
              stmt.body.accept(self, mv)
              #_L2
              #update
              mv.visitLabel(loopLabel)
              if stmt.update:
                  stmt.update.accept(self, mv)
              mv.visitBranch(beginLabel)
              #_L3
              mv.visitLabel(breakLabel)
              mv.closeLoop()
        ```
        参考visitBreak实现visitContinue
        ```python
            def visitContinue(self, stmt: Continue, mv: TACFuncEmitter) -> None:
              mv.visitBranch(mv.getContinueLabel())
        ```

##### 思考题
1. step7
   1. >我们的实验框架里是如何处理悬吊 else 问题的？请简要描述。
      
      答：在`frontend/parser/ply_parser.py`中，将statement分为statement_matched和statement_unmatched两种，定义上下文无关语法如下：
      ```python
      def p_if_else(p):
          """
          statement_matched : If LParen expression RParen statement_matched Else statement_matched
          statement_unmatched : If LParen expression RParen statement_matched Else statement_unmatched
          """
          p[0] = If(p[3], p[5], p[7])

      def p_if(p):
          """
          statement_unmatched : If LParen expression RParen statement
          """
          p[0] = If(p[3], p[5])
      ```
      其中，statement_unmatched还可解析为孤立if语句，从而statement_matched表示if语句已经匹配了else语句，statement_unmatched表示if语句未匹配else语句。从而保证了出现了连续的if-else的语句一定被解析为statement_matched，从而保证else必然与最近的if匹配，避免了悬吊else的问题。
   2. >在实验要求的语义规范中，条件表达式存在短路现象。即
        ```c
           int main() {
                int a = 0;
                int b = 1 ? 1 : (a = 2);
                return a;
            }
        ```
        >会返回 0 而不是 2。如果要求条件表达式不短路，在你的实现中该做何种修改？简述你的思路。
       
       答：由于当前定义的visitCondExpr函数在条件为True时才访问then，在条件为False时才访问else，若不符合相应条件则不会访问相应语句，因此只访问了'1'，而没有访问'a=2'，没有进行赋值，故返回0，产生短路。因此，若要求不短路则可以先访问then和otherwise，在符合相应条件时再进行跳转，继续之后逻辑。即，在`frontend/tacgen/tacgen.py/visitCondExpr`将`expr.then.accept(self, mv)`和`expr.otherwise.accept(self, mv)`提到visitCondExpr函数最前，从而可以先访问'a=2'，对a进行赋值，防止短路现象。
2. step8
    1.  
    >
        将循环语句翻译成 IR 有许多可行的翻译方法，例如 while 循环可以有以下两种翻译方式：

         第一种（即实验指导中的翻译方式）：

         label BEGINLOOP_LABEL：开始下一轮迭代
         cond 的 IR
         beqz BREAK_LABEL：条件不满足就终止循环
         body 的 IR
         label CONTINUE_LABEL：continue 跳到这
         br BEGINLOOP_LABEL：本轮迭代完成
         label BREAK_LABEL：条件不满足，或者 break 语句都会跳到这儿

         第二种：

         cond 的 IR

         beqz BREAK_LABEL：条件不满足就终止循环
         label BEGINLOOP_LABEL：开始下一轮迭代
         body 的 IR
         label CONTINUE_LABEL：continue 跳到这
         cond 的 IR
         bnez BEGINLOOP_LABEL：本轮迭代完成，条件满足时进行下一次迭代
         label BREAK_LABEL：条件不满足，或者 break 语句都会跳到这儿

         从执行的指令的条数这个角度（label 不算做指令，假设循环体至少执行了一次），请评价这两种翻译方式哪一种更好？
      
    答：第二种翻译方式更好。在cond满足时，第一种方式需要执行cond、beqz、br三条额外指令，第二种方式只需要执行cond、bnez两条额外指令，执行时第二种方式执行的除body外的额外指令更少；cond不满足时，第一种方式需要先执行br，跳转至BEGINLOOP_LABEL，再执行cond，判定不满足再执行beqz，跳转至BREAK_LABEL，而第二种方式只需执行cond，判定不满足后执行benz跳转至BREAK_LABEL即可，在终止时第二种方式所需的跳转也更少、执行的指令更少，因此第二种方式更好。
    2. 
    >我们目前的 TAC IR 中条件分支指令采用了单分支目标（标签）的设计，即该指令的操作数中只有一个是标签；如果相应的分支条件不满足，则执行流会继续向下执行。在其它 IR 中存在双目标分支（标签）的条件分支指令，其形式如下：
     br cond, false_target, true_target
    其中cond是一个临时变量，false_target和true_target是标签。其语义为：如果cond的值为0（假），则跳转到false_target处；若cond非0（真），则跳转到true_target处。它与我们的条件分支指令的区别在于执行流总是会跳转到两个标签中的一个。
    你认为中间表示的哪种条件分支指令设计（单目标 vs 双目标）更合理？为什么？（言之有理即可）

   答：我认为双目标更合理。双目标的表达更清晰，能够更直观地表达出条件分支的语义，即根据判断情况不同跳转到不同的标签；而单目标在分支条件不满足时执行流继续向下执行，不够直观。因此双目标更合理，更便于理解和维护。
##### 参考资料
无
# Architecture and Design

## Design goal

The compiler implements the staged MiniDecaf language as a sequence of explicit
IR transformations. Each stage adds language features without hiding the
boundary between source semantics, intermediate representation, and RISC-V code
generation.

## 1. Parsing and semantic resolution

The lexer and parser are built with PLY. Parsing produces a typed AST containing
functions, statements, expressions, identifiers, and literals.

The naming pass walks the AST with a `ScopeStack`:

- entering a block opens a local scope;
- exiting a block closes it;
- declaration lookup checks only the current scope;
- identifier and assignment lookup searches from the innermost scope outward.

The pass attaches `VarSymbol` and `FuncSymbol` objects to AST nodes and reports
undefined names, duplicate declarations, bad calls, and missing `main`
functions.

## 2. Three-address code

AST-to-TAC lowering assigns explicit temporaries to values and labels to control
flow. Representative lowerings include:

- assignments become `Assign` instructions;
- expressions materialize operands in fresh temporaries;
- `if` and loops become conditional and unconditional branches;
- conditional expressions produce a destination temporary for the selected
  branch;
- function calls carry a destination, a function label, and an argument list.

TAC keeps label management separate from the AST and provides a stable input to
data-flow analysis.

## 3. Control-flow and liveness

The backend splits TAC into basic blocks and connects them into a control-flow
graph. A DFS pass marks reachable blocks so register allocation can ignore
unreachable basic blocks.

Liveness analysis tracks the values needed at each program point. The register
allocator uses that information to:

- reuse a register when the previous value is no longer live;
- preserve read values before assigning a destination;
- spill live registers to the stack when no allocatable register is available;
- restrict allocation around calls to respect caller-saved registers.

This is a teaching allocator rather than an optimizing graph-coloring allocator.

## 4. RISC-V lowering

The RISC-V emitter maps each TAC instruction to one or more backend instructions.
Comparison and logical operators may require multiple RV32 instructions. For
example:

- equality is lowered through subtraction and `seqz`;
- inequality uses subtraction and `snez`;
- `<=` and `>=` invert `sgt` or `slt`;
- logical operators normalize operands to boolean values before combining them.

Functions use a stack frame with saved return address and frame pointer. The
prologue reserves local space and saves callee-saved registers; the epilogue
restores registers before `ret`. Function arguments use `a0`-`a7`, and return
values use `a0`.

## 5. Function calls

The function-call stage extends the AST, parser, symbol table, TAC, register
allocator, and emitter together:

- function symbols track parameter types and whether a body has been defined;
- calls validate the function and argument count;
- TAC represents calls as explicit instructions;
- register allocation binds incoming parameters and preserves live
  caller-saved registers;
- the emitter moves arguments into ABI registers and copies the result from
  `a0`.

The resulting implementation supports recursion, including the Fibonacci
example in `example.c`.

## Constraints

The snapshot is intentionally scoped to the MiniDecaf stages represented by the
branches:

- scalar integer values only;
- no arrays, pointers, globals, structs, or floating point;
- no preprocessor;
- no loop or expression optimizer;
- no full RISC-V assembler or runtime, only assembly generation.

These constraints keep the project inspectable as compiler coursework and avoid
claiming capabilities that the final branch does not implement.

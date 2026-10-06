# C-Minus Compiler

A one-pass compiler for the C-Minus programming language, built entirely from scratch in Python. This project translates C-Minus source code into three-address intermediate code capable of being executed by a virtual machine. 

It was developed in three phases: Lexical Analysis, Syntax Analysis (Parsing), and Semantic Analysis & Intermediate Code Generation.

## ⚙️ Features & Architecture

* **Lexical Scanner (`Scanner`):** Tokenizes the input stream using DFA logic. Recognizes keywords, IDs, numbers, symbols, and comments. Implements **Panic Mode** error recovery to discard invalid characters and gracefully resume scanning.
* **Syntax Analyzer (`Parser`):** A Predictive Top-Down LL(1) Parser. It utilizes precomputed FIRST, FOLLOW, and PREDICT sets (stored in `table.py`) to parse the token stream without backtracking. Includes structural Panic Mode recovery using FOLLOW sets as synchronizing tokens.
* **Semantic Analyzer:** Performs static checks during parsing. It detects scoping violations, `void` type misuse, argument count/type mismatches in function calls, invalid `break` statements outside loops, and operand type mismatches.
* **Intermediate Code Generator (`CodeGenerator`):** Generates Three-Address Code (PB - Program Block). 
  * **Dynamic Memory & Recursion:** Implements a dynamic Stack Pointer (SP) and Activation Records (AR) to fully support nested and recursive function calls.
  * **Array Handling:** Calculates pointer offsets for memory-safe array allocation and indexing.
  * **Control Flow:** Resolves nested `if`, `while`, and `switch-case` blocks using a jump stack for precise branch generation.

## 🚀 Usage

1. Place the source code you want to compile inside a file named `input.txt` in the root directory.
2. Run the compiler module:
   ```bash
   python compiler.py

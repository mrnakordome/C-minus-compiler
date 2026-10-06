**Repository Name:** `c-minus-compiler`

**Description:** A complete one-pass compiler for the C-Minus language written in Python, featuring a lexical scanner, an LL(1) predictive parser, and an intermediate code generator with support for arrays and recursive functions.

---

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
   ```
3. The compiler runs in a single pass. It will read `input.txt` and generate several output files documenting the compilation process.

## 📁 Output Files & Examples

The compiler generates the following diagnostic and output files in the root directory:

* **`tokens.txt`**: The sequential list of recognized valid tokens.
  ```text
  1.  (KEYWORD, void) (ID, main) (SYMBOL, () (KEYWORD, void) (SYMBOL, )) (SYMBOL, {)
  2.  (KEYWORD, int) (ID, a) (SYMBOL, =) (NUM, 0) (SYMBOL, ;)
  ```
* **`lexical_errors.txt`**: Logs of unrecognized characters or unclosed comments.
  ```text
  8.  (3d, Invalid number)
  10. (cd!, Invalid input)
  ```
* **`symbol_table.txt`**: The finalized table of identifiers and keywords.
  ```text
  1.  break
  2.  else
  ...
  12. main
  13. a
  ```
* **`parse_tree.txt`**: A visual, text-based representation of the parsed LL(1) syntax tree.
  ```text
  Program
      DeclarationList
          Declaration
              TypeSpecifier
                  int
  ```
* **`syntax_errors.txt`**: Logs of missing or illegal tokens encountered during parsing.
* **`semantic_errors.txt`**: Logs of type mismatches, undeclared variables, and scope violations.
* **`output.txt`**: The final executable Three-Address Code. If semantic errors are present, this file will halt generation to prevent unsafe execution.
  ```text
  0   (JP, 1, , )
  1   (ASSIGN, #2, 100, )
  2   (ASSIGN, #0, 104, )
  3   (EQ, 100, #1, 500)
  ```

## 💻 Language Specifications (C-Minus)

C-Minus is a simplified subset of C. This compiler supports:
* `int` and `void` data types.
* Single-dimensional arrays.
* Global and local variable scoping.
* `if-else`, `while`, `switch-case-default`, and `break` control flows.
* Functions with parameters and return values (including full recursion support).
* Standard arithmetic (`+`, `-`, `*`, `/`) and relational (`<`, `==`) operations.

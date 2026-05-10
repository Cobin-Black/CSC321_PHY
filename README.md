# CSC321_PHY
This is the first part of creating the PHY language for Principle of Programming Languages. This is including Tokenization, Parsing, and making test functions for our program.

PHY is a languge to try and help make physics calculations easier for anyone. Since physics has many different variables and formulas this languge it to help make sure to keep track of everything and calculate for the user.

## Architecture:
<br>Lexer (lexer.py): Converts raw text into a stream of tokens. It uses regular expressions to identify physics-specific literals, such as units (kg, N, meter) and time formats (HH:MM:SS).

Parser (parser.py): A recursive-descent parser that consumes tokens and organizes them into a tree structure based on our formal grammar. It handles operator precedence (multiplication before addition).

AST (ast_nodes.py): Defines the data structures (nodes) for the Abstract Syntax Tree, allowing the program structure to be represented hierarchically.

## Running Lexer/Parser:
 1. In your CML want to navigate where the Project/PHY-Language is at
 2. Once you are there you want to type: py src/phy.py test/valid1.phy
 <br>   Note: (The tests are named valid1-10.phy OR invalid1-5.phy; You can change the test name to whichever you want to try)

## Grammar:
  The grammar for PHY is represented in a way that makes sense with how physics problems are traditionally approached.

   <br> &nbsp;&nbsp;&nbsp; program        ::= header? statement\*
   <br> &nbsp;&nbsp;&nbsp; header         ::= "givens" "{" assignment\* "}"
   <br> &nbsp;&nbsp;&nbsp; statement      ::= assignment | print_stmt
   <br> &nbsp;&nbsp;&nbsp; assignment     ::= ("given" | "let")? type_kw? IDENTIFIER "=" expression ";"
   <br> &nbsp;&nbsp;&nbsp; type_kw        ::= "mass" | "accel" | "velocity" | "length" | "power" | "temp" | "force" | "time" | "energy" | "work"
   <br> &nbsp;&nbsp;&nbsp; print_stmt     ::= "print" expression ";"
   <br> &nbsp;&nbsp;&nbsp; expression     ::= if_expr | comparison
   <br> &nbsp;&nbsp;&nbsp; if_expr        ::= "if" "(" expression ")" "then" expression "else" expression
   <br> &nbsp;&nbsp;&nbsp; comparison     ::= arith_expr (("==" | "!=" | ">" | "<" | ">=" | "<=" | "&&" | "\|\|") arith_expr)\*
   <br> &nbsp;&nbsp;&nbsp; arith_expr     ::= term (("+" | "-") term)\*
   <br> &nbsp;&nbsp;&nbsp; term           ::= factor (("\*" | "/") factor)\*
   <br> &nbsp;&nbsp;&nbsp; factor         ::= if_expr | func_call | (NUMBER | TIME) UNIT? | IDENTIFIER | "(" expression ")"
   <br> &nbsp;&nbsp;&nbsp; func_call      ::= IDENTIFIER "(" (expression ("," expression)\*)? ")"
   <br> &nbsp;&nbsp;&nbsp; UNIT           ::= "kg" | "g" | "N" | "J" | "W" | "meter" | "secs" | "K" | "C" | "F" | "rad" | "k"

   #### Notes:
   - **if-then-else is an expression**, not a statement — it always evaluates to a value and both `then` and `else` branches are required. This follows pure functional programming rules.
   - **Function calls** are built-in only. User-defined functions are not supported.
   - **Pre-loaded constants** (`pi`, `e`, `grav`, `c`, `G`, `h`, `k_b`) are available without declaration.

## How It Should Look:
  ### <br> &nbsp;&nbsp; Valid: <br> &nbsp;&nbsp;&nbsp; <img width="389" height="108" alt="image" src="https://github.com/user-attachments/assets/36342121-e493-4202-8062-64060fba47fd" />
  
  ### <br> &nbsp;&nbsp; Invalid:  &nbsp;&nbsp;&nbsp; <img width="1059" height="52" alt="image" src="https://github.com/user-attachments/assets/f440dd09-eaea-44c8-82af-ac1bcd288b2c" />


## How To Run:
 1. You need to download the project since it is its own language
 2. Once you have it downloaded double click Run_PHY_IDE.bat to start the program
    <br> What Should Come Up: <img width="1199" height="801" alt="image" src="https://github.com/user-attachments/assets/1e2b9d7e-c920-418a-8c8c-088138197e4a" />

## Extra Help:
You can check out the Function Reference Menu that will show you all the built in functions that will help you with solving certain problems
 <br> What Should Come Up: <img width="698" height="572" alt="image" src="https://github.com/user-attachments/assets/9eff0eb6-a5f8-4070-ae6c-c3b9209004a9" />

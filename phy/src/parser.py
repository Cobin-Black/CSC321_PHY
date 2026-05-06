from ast_nodes import (
    Program, AssignmentStatement, PrintStatement,
    BinaryExpression, IntegerLiteral, Identifier, FunctionCall
)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def eat(self, type):
        if self.current().type == type:
            token = self.current()
            self.pos += 1
            return token
        raise SyntaxError(
            f"Expected {type}, got {self.current().type} "
            f"at token {self.pos} ('{self.current().value}')"
        )

    def parse(self):
        statements = []
        if self.current().type == 'GIVENS':
            self.eat('GIVENS')
            self.eat('LBRACE')
            while self.current().type != 'RBRACE':
                statements.append(self.parse_assignment())
            self.eat('RBRACE')
        while self.current().type != 'EOF':
            statements.append(self.parse_statement())
        return Program(statements)

    def parse_statement(self):
        t = self.current().type
        if t == 'PRINT':
            self.eat('PRINT')
            e = self.parse_expr()
            self.eat('SEMICOLON')
            return PrintStatement(e)
        return self.parse_assignment()

    def parse_assignment(self):
        mode = self.eat(self.current().type).value if self.current().type in ('GIVEN', 'LET') else None
        type_kw = self.eat('TYPE_KW').value if self.current().type == 'TYPE_KW' else None

        # Allow unit tokens (g, kg, meter …) to be used as variable names
        if self.current().type in ('IDENTIFIER', 'UNIT'):
            name = self.eat(self.current().type).value
        else:
            self.eat('IDENTIFIER')  # triggers the standard error message

        self.eat('EQUALS')
        expr = self.parse_expr()
        self.eat('SEMICOLON')
        return AssignmentStatement(Identifier(name), expr, mode, type_kw)

    def parse_expr(self):
        node = self.parse_term()
        while self.current().type in ('PLUS', 'MINUS'):
            op = self.eat(self.current().type).value
            node = BinaryExpression(node, op, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current().type in ('STAR', 'SLASH'):
            op = self.eat(self.current().type).value
            node = BinaryExpression(node, op, self.parse_factor())
        return node

    def parse_factor(self):
        token = self.current()

        # Time literal  e.g. 00:05:00
        if token.type == 'TIME_LITERAL':
            return IntegerLiteral(self.eat('TIME_LITERAL').value)

        # Numeric literal with optional unit  e.g. 50kg  or  9.8
        if token.type in ('INT_LITERAL', 'FLOAT_LITERAL'):
            val = self.eat(token.type).value
            unit = None
            if self.current().type == 'UNIT':
                unit = self.eat('UNIT').value
            elif self.current().type == 'IDENTIFIER' and self.current().value in (
                'kg', 'g', 'meter', 'secs', 'N', 'J', 'W', 'k'
            ):
                unit = self.eat('IDENTIFIER').value
            return IntegerLiteral(val, unit)

        # Identifier, unit-as-variable (e.g. `g`), or type-keyword-as-function (e.g. `work(…)`)
        if token.type in ('IDENTIFIER', 'UNIT', 'TYPE_KW'):
            name = self.eat(token.type).value
            if self.current().type == 'LPAREN':
                # Built-in function call:  name(arg1, arg2, ...)
                self.eat('LPAREN')
                args = []
                if self.current().type != 'RPAREN':
                    args.append(self.parse_expr())
                    while self.current().type == 'COMMA':
                        self.eat('COMMA')
                        args.append(self.parse_expr())
                self.eat('RPAREN')
                return FunctionCall(name, args)
            return Identifier(name)

        # Parenthesised sub-expression
        if token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.parse_expr()
            self.eat('RPAREN')
            return node

        raise SyntaxError(
            f"Unexpected token {token.type} ('{token.value}') at token {self.pos}"
        )

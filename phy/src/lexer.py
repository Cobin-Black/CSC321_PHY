
import re

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.rules = [
            ('COMMENT',      r'//.*'),
            ('WHITESPACE',   r'\s+'),
            ('GIVENS',       r'\bgivens\b'),
            ('PRINT',        r'\bprint\b'),
            ('GIVEN',        r'\bgiven\b'),
            ('LET',          r'\blet\b'),
            ('TYPE_KW',      r'\b(mass|accel|velocity|length|power|temp|force|time|energy|work)\b'),
            ('TIME_LITERAL', r'\d{1,2}:\d{2}:\d{2}'),
            ('FLOAT_LITERAL',r'\d+\.\d+'),
            ('INT_LITERAL',  r'\d+'),
            ('GIVENS',       r'\bgivens\b'),
            ('IF',           r'\bif\b'),
            ('PRINT',        r'\bprint\b'),
            ('GIVEN',        r'\bgiven\b'),
            ('LET',          r'\blet\b'),
            ('UNIT', r'\b(kg|g|secs|J|N|meter|k|W|C|F|K|rad)\b'),
            ('IDENTIFIER',   r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('EQEQ',         r'=='),
            ('NOTEQ',        r'!='),
            ('GTE',          r'>='),
            ('LTE',          r'<='),
            ('GT',           r'>'),
            ('LT',           r'<'),
            ('AND',          r'&&'),
            ('OR',           r'\|\|'),
            ('EQUALS',       r'='),
            ('PLUS',         r'\+'),
            ('MINUS',        r'-'),
            ('STAR',         r'\*'),
            ('SLASH',        r'/'),
            ('LPAREN',       r'\('),
            ('RPAREN',       r'\)'),
            ('LBRACE',       r'\{'),
            ('RBRACE',       r'\}'),
            ('COMMA',        r','),
            ('SEMICOLON',    r';'),
        ]

    def tokenize(self):
        tokens = []
        pos = 0
        while pos < len(self.text):
            match = None
            for token_type, pattern in self.rules:
                regex = re.compile(pattern)
                match = regex.match(self.text, pos)
                if match:
                    if token_type not in ('WHITESPACE', 'COMMENT'):
                        tokens.append(Token(token_type, match.group(0)))
                    pos = match.end()
                    break
            if not match:
                raise SyntaxError(f"Illegal character: '{self.text[pos]}'")
        tokens.append(Token('EOF', None))
        return tokens

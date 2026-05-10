
class Node:
    """Base class for all nodes."""
    def __str__(self):
        return self.__class__.__name__

class Program(Node):
    def __init__(self, statements):
        self.statements = statements

class AssignmentStatement(Node):
    def __init__(self, identifier, expression, mode=None, type_kw=None):
        self.identifier = identifier
        self.expression = expression
        self.mode = mode
        self.type_kw = type_kw

class PrintStatement(Node):
    def __init__(self, expression):
        self.expression = expression

class BinaryExpression(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class IntegerLiteral(Node):
    def __init__(self, value, unit=None):
        self.value = value
        self.unit = unit

class Identifier(Node):
    def __init__(self, name):
        self.name = name

class FunctionCall(Node):
    def __init__(self, name, args):
        self.name = name
        self.args = args  # List of expression nodes

class BooleanExpression(Node):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right

class IfStatement(Node):
    def __init__(self, condition, statements):
        self.condition = condition
        self.statements = statements

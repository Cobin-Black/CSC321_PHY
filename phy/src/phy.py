import sys
import math
from ast_nodes import (
    Program, AssignmentStatement, PrintStatement,
    BinaryExpression, IntegerLiteral, Identifier, FunctionCall,
    IfExpression
)
from lexer import Lexer
from parser import Parser

# ─────────────────────────────────────────────
# BUILT-IN FUNCTION REGISTRY
# Each entry: { 'args': int, 'params': [str], 'desc': str, 'fn': callable }
# fn receives a list of {'val': float, 'unit': str} dicts, one per argument.
# ─────────────────────────────────────────────
BUILTIN_FUNCTIONS = {

        # ── Math / Trigonometry ──────────────────────────────────────
    'sin': {
        'args': 1, 'params': ['x'],
        'desc': 'sin(x) — sine, x in radians',
        'fn': lambda a: {'val': math.sin(a[0]['val']), 'unit': None},
    },
    'cos': {
        'args': 1, 'params': ['x'],
        'desc': 'cos(x) — cosine, x in radians',
        'fn': lambda a: {'val': math.cos(a[0]['val']), 'unit': None},
    },
    'tan': {
        'args': 1, 'params': ['x'],
        'desc': 'tan(x) — tangent, x in radians',
        'fn': lambda a: {'val': math.tan(a[0]['val']), 'unit': None},
    },
    'asin': {
        'args': 1, 'params': ['x'],
        'desc': 'asin(x) — inverse sine, returns radians',
        'fn': lambda a: {'val': math.asin(a[0]['val']), 'unit': 'rad'},
    },
    'acos': {
        'args': 1, 'params': ['x'],
        'desc': 'acos(x) — inverse cosine, returns radians',
        'fn': lambda a: {'val': math.acos(a[0]['val']), 'unit': 'rad'},
    },
    'atan': {
        'args': 1, 'params': ['x'],
        'desc': 'atan(x) — inverse tangent, returns radians',
        'fn': lambda a: {'val': math.atan(a[0]['val']), 'unit': 'rad'},
    },

    # ── Physics: Mechanics ──────────────────────────────────────
    'newton': {
        'args': 2, 'params': ['mass', 'acceleration'],
        'desc': 'F = m*a  — Newton\'s Second Law → N',
        'fn': lambda a: {'val': a[0]['val'] * a[1]['val'], 'unit': 'N'},
    },
    'weight': {
        'args': 1, 'params': ['mass'],
        'desc': 'W = m*g  — Weight force (g = 9.8 m/s²) → N',
        'fn': lambda a: {'val': a[0]['val'] * 9.8, 'unit': 'N'},
    },
    'ke': {
        'args': 2, 'params': ['mass', 'velocity'],
        'desc': 'KE = ½mv²  — Kinetic Energy → J',
        'fn': lambda a: {'val': 0.5 * a[0]['val'] * a[1]['val'] ** 2, 'unit': 'J'},
    },
    'pe': {
        'args': 2, 'params': ['mass', 'height'],
        'desc': 'PE = mgh  — Gravitational Potential Energy (g = 9.8) → J',
        'fn': lambda a: {'val': a[0]['val'] * 9.8 * a[1]['val'], 'unit': 'J'},
    },
    'momentum': {
        'args': 2, 'params': ['mass', 'velocity'],
        'desc': 'p = mv  — Linear Momentum → kg·m/s',
        'fn': lambda a: {'val': a[0]['val'] * a[1]['val'], 'unit': 'kg*m/s'},
    },
    'work': {
        'args': 2, 'params': ['force', 'displacement'],
        'desc': 'W = Fd  — Work → J',
        'fn': lambda a: {'val': a[0]['val'] * a[1]['val'], 'unit': 'J'},
    },
    'power': {
        'args': 2, 'params': ['work', 'time'],
        'desc': 'P = W/t  — Power → W',
        'fn': lambda a: {'val': a[0]['val'] / a[1]['val'], 'unit': 'W'},
    },
    'avg_velocity': {
        'args': 2, 'params': ['displacement', 'time'],
        'desc': 'v = d/t  — Average Velocity → m/s',
        'fn': lambda a: {'val': a[0]['val'] / a[1]['val'], 'unit': 'm/s'},
    },
    'acceleration': {
        'args': 2, 'params': ['delta_velocity', 'time'],
        'desc': 'a = Δv/t  — Acceleration → m/s²',
        'fn': lambda a: {'val': a[0]['val'] / a[1]['val'], 'unit': 'm/s2'},
    },
    'vel_final': {
        'args': 3, 'params': ['initial_velocity', 'acceleration', 'time'],
        'desc': 'vf = v₀ + at  — Final Velocity (kinematics) → m/s',
        'fn': lambda a: {'val': a[0]['val'] + a[1]['val'] * a[2]['val'], 'unit': 'm/s'},
    },
    'displacement': {
        'args': 3, 'params': ['initial_velocity', 'acceleration', 'time'],
        'desc': 'd = v₀t + ½at²  — Displacement (kinematics) → m',
        'fn': lambda a: {
            'val': a[0]['val'] * a[2]['val'] + 0.5 * a[1]['val'] * a[2]['val'] ** 2,
            'unit': 'm',
        },
    },
    'hooke': {
        'args': 2, 'params': ['spring_constant', 'displacement'],
        'desc': 'F = kx  — Hooke\'s Law → N',
        'fn': lambda a: {'val': a[0]['val'] * a[1]['val'], 'unit': 'N'},
    },
    'pressure': {
        'args': 2, 'params': ['force', 'area'],
        'desc': 'P = F/A  — Pressure → Pa',
        'fn': lambda a: {'val': a[0]['val'] / a[1]['val'], 'unit': 'Pa'},
    },

    # ── Physics: Waves & Oscillations ───────────────────────────
    'wave_speed': {
        'args': 2, 'params': ['frequency', 'wavelength'],
        'desc': 'v = fλ  — Wave Speed → m/s',
        'fn': lambda a: {'val': a[0]['val'] * a[1]['val'], 'unit': 'm/s'},
    },
    'period': {
        'args': 1, 'params': ['frequency'],
        'desc': 'T = 1/f  — Period from Frequency → s',
        'fn': lambda a: {'val': 1.0 / a[0]['val'], 'unit': 's'},
    },
    'frequency': {
        'args': 1, 'params': ['period'],
        'desc': 'f = 1/T  — Frequency from Period → Hz',
        'fn': lambda a: {'val': 1.0 / a[0]['val'], 'unit': 'Hz'},
    },

    # ── Physics: Electricity ────────────────────────────────────
    'ohm_v': {
        'args': 2, 'params': ['current', 'resistance'],
        'desc': 'V = IR  — Ohm\'s Law (voltage) → V',
        'fn': lambda a: {'val': a[0]['val'] * a[1]['val'], 'unit': 'V'},
    },
    'ohm_i': {
        'args': 2, 'params': ['voltage', 'resistance'],
        'desc': 'I = V/R  — Ohm\'s Law (current) → A',
        'fn': lambda a: {'val': a[0]['val'] / a[1]['val'], 'unit': 'A'},
    },
    'coulomb': {
        'args': 3, 'params': ['charge1', 'charge2', 'distance'],
        'desc': 'F = kq₁q₂/r²  — Coulomb\'s Law (k = 8.99×10⁹) → N',
        'fn': lambda a: {
            'val': 8.99e9 * a[0]['val'] * a[1]['val'] / a[2]['val'] ** 2,
            'unit': 'N',
        },
    },

    # ── Physics: Thermodynamics ─────────────────────────────────
    'heat': {
        'args': 3, 'params': ['mass', 'specific_heat', 'delta_temp'],
        'desc': 'Q = mcΔT  — Heat Transfer → J',
        'fn': lambda a: {'val': a[0]['val'] * a[1]['val'] * a[2]['val'], 'unit': 'J'},
    },
    'ideal_gas_p': {
        'args': 3, 'params': ['n_moles', 'temperature_K', 'volume_m3'],
        'desc': 'P = nRT/V  — Ideal Gas Law (R = 8.314) → Pa',
        'fn': lambda a: {
            'val': a[0]['val'] * 8.314 * a[1]['val'] / a[2]['val'],
            'unit': 'Pa',
        },
    },

    # ── Unit Conversions ────────────────────────────────────────
    'km_to_m': {
        'args': 1, 'params': ['km'],
        'desc': 'Kilometers → meters  (×1000)',
        'fn': lambda a: {'val': a[0]['val'] * 1000, 'unit': 'm'},
    },
    'm_to_km': {
        'args': 1, 'params': ['meters'],
        'desc': 'Meters → kilometers  (÷1000)',
        'fn': lambda a: {'val': a[0]['val'] / 1000, 'unit': 'km'},
    },
    'cm_to_m': {
        'args': 1, 'params': ['cm'],
        'desc': 'Centimeters → meters  (÷100)',
        'fn': lambda a: {'val': a[0]['val'] / 100, 'unit': 'm'},
    },
    'm_to_cm': {
        'args': 1, 'params': ['meters'],
        'desc': 'Meters → centimeters  (×100)',
        'fn': lambda a: {'val': a[0]['val'] * 100, 'unit': 'cm'},
    },
    'g_to_kg': {
        'args': 1, 'params': ['grams'],
        'desc': 'Grams → kilograms  (÷1000)',
        'fn': lambda a: {'val': a[0]['val'] / 1000, 'unit': 'kg'},
    },
    'kg_to_g': {
        'args': 1, 'params': ['kg'],
        'desc': 'Kilograms → grams  (×1000)',
        'fn': lambda a: {'val': a[0]['val'] * 1000, 'unit': 'g'},
    },
    'celsius_to_k': {
        'args': 1, 'params': ['celsius'],
        'desc': 'Celsius → Kelvin  (+273.15)',
        'fn': lambda a: {'val': a[0]['val'] + 273.15, 'unit': 'K'},
    },
    'k_to_celsius': {
        'args': 1, 'params': ['kelvin'],
        'desc': 'Kelvin → Celsius  (-273.15)',
        'fn': lambda a: {'val': a[0]['val'] - 273.15, 'unit': 'C'},
    },
    'joules_to_cal': {
        'args': 1, 'params': ['joules'],
        'desc': 'Joules → calories  (÷4.184)',
        'fn': lambda a: {'val': a[0]['val'] / 4.184, 'unit': 'cal'},
    },
    'cal_to_joules': {
        'args': 1, 'params': ['calories'],
        'desc': 'Calories → Joules  (×4.184)',
        'fn': lambda a: {'val': a[0]['val'] * 4.184, 'unit': 'J'},
    },
    'mph_to_ms': {
        'args': 1, 'params': ['mph'],
        'desc': 'Miles per hour → m/s  (×0.44704)',
        'fn': lambda a: {'val': a[0]['val'] * 0.44704, 'unit': 'm/s'},
    },
    'ms_to_mph': {
        'args': 1, 'params': ['ms'],
        'desc': 'Meters per second → mph  (÷0.44704)',
        'fn': lambda a: {'val': a[0]['val'] / 0.44704, 'unit': 'mph'},
    },
    'n_to_lb': {
        'args': 1, 'params': ['newtons'],
        'desc': 'Newtons → pounds-force  (×0.224809)',
        'fn': lambda a: {'val': a[0]['val'] * 0.224809, 'unit': 'lbf'},
    },
    'lb_to_n': {
        'args': 1, 'params': ['pounds'],
        'desc': 'Pounds-force → Newtons  (×4.44822)',
        'fn': lambda a: {'val': a[0]['val'] * 4.44822, 'unit': 'N'},
    },
    'c_to_k': {
    'args': 1, 'params': ['celsius'],
    'desc': 'Celsius → Kelvin  (C + 273.15)',
    'fn': lambda a: {'val': a[0]['val'] + 273.15, 'unit': 'K'},
    },

    'k_to_c': {
        'args': 1, 'params': ['kelvin'],
        'desc': 'Kelvin → Celsius  (K - 273.15)',
        'fn': lambda a: {'val': a[0]['val'] - 273.15, 'unit': 'C'},
    },

    'c_to_f': {
        'args': 1, 'params': ['celsius'],
        'desc': 'Celsius → Fahrenheit  (C * 9/5 + 32)',
        'fn': lambda a: {'val': a[0]['val'] * 9/5 + 32, 'unit': 'F'},
    },

    'f_to_c': {
        'args': 1, 'params': ['fahrenheit'],
        'desc': 'Fahrenheit → Celsius  ((F - 32) * 5/9)',
        'fn': lambda a: {'val': (a[0]['val'] - 32) * 5/9, 'unit': 'C'},
    },

    'f_to_k': {
        'args': 1, 'params': ['fahrenheit'],
        'desc': 'Fahrenheit → Kelvin  ((F - 32) * 5/9 + 273.15)',
        'fn': lambda a: {'val': (a[0]['val'] - 32) * 5/9 + 273.15, 'unit': 'K'},
    },

    'k_to_f': {
        'args': 1, 'params': ['kelvin'],
        'desc': 'Kelvin → Fahrenheit  ((K - 273.15) * 9/5 + 32)',
        'fn': lambda a: {'val': (a[0]['val'] - 273.15) * 9/5 + 32, 'unit': 'F'},
    },
}


# ─────────────────────────────────────────────
# INTERPRETER
# ─────────────────────────────────────────────
class Interpreter:
    def __init__(self):
        self.variables = {
            # Mathematical constants
            'pi': {
                'val': 3.141592653589793,
                'unit': None
            },
            'e': {
                'val': 2.718281828459045,
                'unit': None
            },

            'grav': {
                'val': 9.81,
                'unit': 'm/s^2'
            },
            'c': {
                'val': 299792458,
                'unit': 'm/s'
            },
            'G': {
                'val': 6.67430e-11,
                'unit': 'm^3/kg/s^2'
            },
            'h': {
                'val': 6.62607015e-34,
                'unit': 'J*s'
            },
            'k_b': {
                'val': 1.380649e-23,
                'unit': 'J/K'
            }
        }

    def evaluate(self, node):
        if isinstance(node, IntegerLiteral):
            try:
                val = float(node.value)
            except ValueError:
                val = node.value
            return {'val': val, 'unit': node.unit}

        if isinstance(node, Identifier):
            if node.name in self.variables:
                return self.variables[node.name]
            raise NameError(f"Undefined variable: '{node.name}'")

        if isinstance(node, FunctionCall):
            return self._call_builtin(node.name, [self.evaluate(a) for a in node.args])

        # Functional if-then-else — evaluates to whichever branch is chosen
        if isinstance(node, IfExpression):
            condition = self.evaluate(node.condition)
            if condition['val']:
                return self.evaluate(node.then_expr)
            else:
                return self.evaluate(node.else_expr)

        if isinstance(node, BinaryExpression):
            left  = self.evaluate(node.left)
            right = self.evaluate(node.right)

            if node.operator == '==':
                return {'val': left['val'] == right['val'], 'unit': None}

            if node.operator == '!=':
                return {'val': left['val'] != right['val'], 'unit': None}

            if node.operator == '>':
                return {'val': left['val'] > right['val'], 'unit': None}

            if node.operator == '<':
                return {'val': left['val'] < right['val'], 'unit': None}

            if node.operator == '>=':
                return {'val': left['val'] >= right['val'], 'unit': None}

            if node.operator == '<=':
                return {'val': left['val'] <= right['val'], 'unit': None}

            if node.operator == '&&':
                return {'val': left['val'] and right['val'], 'unit': None}

            if node.operator == '||':
                return {'val': left['val'] or right['val'], 'unit': None}

            if node.operator == '*':
                u1 = left['unit'] or ''
                u2 = right['unit'] or ''
                unit = f"{u1}*{u2}".strip('*')
                return {'val': left['val'] * right['val'], 'unit': unit}

            if node.operator == '/':
                u1 = left['unit'] or ''
                u2 = right['unit'] or ''
                unit = f"{u1}/{u2}".strip('/')
                return {'val': left['val'] / right['val'], 'unit': unit}

            if node.operator == '+':
                return {'val': left['val'] + right['val'], 'unit': left['unit']}

            if node.operator == '-':
                return {'val': left['val'] - right['val'], 'unit': left['unit']}

    def _call_builtin(self, name, evaluated_args):
        if name not in BUILTIN_FUNCTIONS:
            raise NameError(
                f"Unknown function '{name}'. "
                f"Available: {', '.join(sorted(BUILTIN_FUNCTIONS))}"
            )
        fn_def = BUILTIN_FUNCTIONS[name]
        expected = fn_def['args']
        if len(evaluated_args) != expected:
            raise TypeError(
                f"'{name}' expects {expected} argument(s) "
                f"({', '.join(fn_def['params'])}), got {len(evaluated_args)}"
            )
        return fn_def['fn'](evaluated_args)

    def execute(self, node):
        if isinstance(node, Program):
            for stmt in node.statements:
                self.execute(stmt)
        elif isinstance(node, AssignmentStatement):
            self.variables[node.identifier.name] = self.evaluate(node.expression)
        elif isinstance(node, PrintStatement):
            res = self.evaluate(node.expression)
            unit_str = f" {res['unit']}" if res['unit'] else ''
            print(f"RESULT: {res['val']}{unit_str}")


# ─────────────────────────────────────────────
# UTILITY — pretty-print the AST
# ─────────────────────────────────────────────
def print_ast(node, indent=0):
    if node is None:
        return
    p = '  ' * indent
    if isinstance(node, Program):
        print('Program')
        for s in node.statements:
            print_ast(s, indent + 1)
    elif isinstance(node, AssignmentStatement):
        info = f"({node.mode or ''} {node.type_kw or ''})".strip()
        print(f"{p}AssignmentStatement {info}")
        print_ast(node.identifier, indent + 2)
        print_ast(node.expression, indent + 2)
    elif isinstance(node, PrintStatement):
        print(f"{p}PrintStatement")
        print_ast(node.expression, indent + 1)
    elif isinstance(node, BinaryExpression):
        print(f"{p}BinaryExpression ({node.operator})")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)
    elif isinstance(node, IntegerLiteral):
        u = f", unit: {node.unit}" if node.unit else ''
        print(f"{p}IntegerLiteral (value: {node.value}{u})")
    elif isinstance(node, Identifier):
        print(f"{p}Identifier ({node.name})")
    elif isinstance(node, FunctionCall):
        print(f"{p}FunctionCall ({node.name}, {len(node.args)} arg(s))")
        for arg in node.args:
            print_ast(arg, indent + 2)
    elif isinstance(node, IfExpression):
        print(f"{p}IfExpression")
        print(f"{p}  condition:")
        print_ast(node.condition, indent + 2)
        print(f"{p}  then:")
        print_ast(node.then_expr, indent + 2)
        print(f"{p}  else:")
        print_ast(node.else_expr, indent + 2)


# ─────────────────────────────────────────────
# MAIN — command-line entry point
# ─────────────────────────────────────────────
if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'test.phy'

    try:
        with open(filename, 'r') as f:
            source = f.read()

        tokens   = Lexer(source).tokenize()
        ast_tree = Parser(tokens).parse()

        print('\n--- ABSTRACT SYNTAX TREE ---')
        print_ast(ast_tree)

        print('\n--- INTERPRETED RESULTS ---')
        Interpreter().execute(ast_tree)
        print('---------------------------\n')

    except Exception as e:
        print(f'Error: {e}')

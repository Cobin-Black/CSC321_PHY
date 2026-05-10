"""
PHY IDE — standalone desktop application for the PHY physics language.
Run with:  python phy_ide.py
"""

import sys
import os
import io
import contextlib
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, font as tkfont

# Make sure imports from the same directory always work regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer import Lexer
from parser import Parser
from phy import Interpreter, print_ast, BUILTIN_FUNCTIONS

# ─────────────────────────────────────────────────────
# COLOUR PALETTE  (One-Dark inspired)
# ─────────────────────────────────────────────────────
BG_EDITOR   = '#282c34'
BG_OUTPUT   = '#1e2127'
BG_SIDEBAR  = '#21252b'
BG_TOOLBAR  = '#21252b'
FG_DEFAULT  = '#abb2bf'
FG_KEYWORD  = '#c678dd'   # purple   — given, let, print, givens
FG_TYPE_KW  = '#e5c07b'   # yellow   — mass, force, velocity …
FG_BUILTIN  = '#61afef'   # blue     — newton(), ke(), km_to_m() …
FG_NUMBER   = '#d19a66'   # orange   — numeric literals
FG_UNIT     = '#56b6c2'   # cyan     — kg, N, J, meter …
FG_COMMENT  = '#5c6370'   # grey     — // …
FG_OUTPUT   = '#98c379'   # green    — normal output
FG_ERROR    = '#e06c75'   # red      — errors
CURSOR_COL  = '#528bff'

FONT_EDITOR = ('Consolas', 12)
FONT_OUTPUT = ('Consolas', 11)
FONT_UI     = ('Segoe UI', 10)

# ─────────────────────────────────────────────────────
# SYNTAX HIGHLIGHTING PATTERNS
# ─────────────────────────────────────────────────────
import re

HIGHLIGHT_RULES = [
    # order matters — more specific first
    ('comment',  r'//[^\n]*'),
    ('number',   r'\b\d+(?:\.\d+)?\b'),
    ('keyword',  r'\b(?:givens|given|let|print|if|then|else)\b'),
    ('type_kw',  r'\b(?:mass|accel|velocity|length|power|temp|force|time|energy|work)\b'),
    ('unit',     r'\b(?:kg|g|secs|J|N|meter|k|W|C|F|K|rad)\b'),
    ('builtin',  r'\b(?:' + '|'.join(re.escape(n) for n in BUILTIN_FUNCTIONS) + r')\b'),
]


# ─────────────────────────────────────────────────────
# LINE-NUMBER CANVAS
# ─────────────────────────────────────────────────────
class LineNumbers(tk.Canvas):
    def __init__(self, parent, text_widget, **kwargs):
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.config(bg=BG_SIDEBAR, highlightthickness=0)

    def redraw(self, *_):
        self.delete('all')
        i = self.text_widget.index('@0,0')
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y    = dline[1]
            line = str(i).split('.')[0]
            self.create_text(
                2, y,
                anchor='nw',
                text=line,
                fill='#636d83',
                font=FONT_EDITOR,
            )
            i = self.text_widget.index(f'{i}+1line')
            if i == self.text_widget.index(f'{i}'):
                break


# ─────────────────────────────────────────────────────
# MAIN IDE CLASS
# ─────────────────────────────────────────────────────
class PhyIDE:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('PHY IDE — Physics Language')
        self.root.geometry('1200x750')
        self.root.configure(bg=BG_TOOLBAR)
        self.root.minsize(800, 500)

        self.current_file: str | None = None
        self.unsaved = False

        self._build_menu()
        self._build_toolbar()
        self._build_main_area()
        self._build_status_bar()

        self._apply_highlighting()
        self._update_title()

    # ── MENU BAR ────────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=BG_SIDEBAR, fg=FG_DEFAULT,
                          activebackground=CURSOR_COL, activeforeground='#ffffff',
                          relief='flat', bd=0)
        self.root.config(menu=menubar)

        # File
        file_menu = tk.Menu(menubar, tearoff=0, bg=BG_SIDEBAR, fg=FG_DEFAULT,
                            activebackground=CURSOR_COL, activeforeground='#ffffff')
        file_menu.add_command(label='New          Ctrl+N', command=self.new_file)
        file_menu.add_command(label='Open…        Ctrl+O', command=self.open_file)
        file_menu.add_command(label='Save         Ctrl+S', command=self.save_file)
        file_menu.add_command(label='Save As…     Ctrl+Shift+S', command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)
        menubar.add_cascade(label='File', menu=file_menu)

        # Run
        run_menu = tk.Menu(menubar, tearoff=0, bg=BG_SIDEBAR, fg=FG_DEFAULT,
                           activebackground=CURSOR_COL, activeforeground='#ffffff')
        run_menu.add_command(label='Run          F5', command=self.run_code)
        run_menu.add_command(label='Clear Output', command=self.clear_output)
        menubar.add_cascade(label='Run', menu=run_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0, bg=BG_SIDEBAR, fg=FG_DEFAULT,
                            activebackground=CURSOR_COL, activeforeground='#ffffff')
        help_menu.add_command(label='Function Reference',     command=self.show_function_ref)
        help_menu.add_command(label='Values & Types Reference', command=self.show_values_ref)
        help_menu.add_command(label='Language Guide',          command=self.show_language_guide)
        help_menu.add_command(label='About PHY',               command=self.show_about)
        menubar.add_cascade(label='Help', menu=help_menu)

        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-S>', lambda e: self.save_as())
        self.root.bind('<F5>',        lambda e: self.run_code())

    # ── TOOLBAR ─────────────────────────────────────
    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg=BG_TOOLBAR, pady=4)
        toolbar.pack(side='top', fill='x')

        btn_style = dict(
            bg=CURSOR_COL, fg='#ffffff', relief='flat',
            padx=14, pady=4, font=FONT_UI, cursor='hand2',
            activebackground='#6b9fff', activeforeground='#ffffff',
        )

        tk.Button(toolbar, text='▶  Run  (F5)', command=self.run_code, **btn_style).pack(side='left', padx=(6, 2))

        sep_style = dict(bg='#3e4452', width=1)
        tk.Frame(toolbar, **sep_style).pack(side='left', fill='y', padx=6, pady=2)

        flat = dict(bg=BG_TOOLBAR, fg=FG_DEFAULT, relief='flat',
                    padx=10, pady=4, font=FONT_UI, cursor='hand2',
                    activebackground='#2c313a', activeforeground=FG_DEFAULT)
        tk.Button(toolbar, text='New',    command=self.new_file,  **flat).pack(side='left', padx=1)
        tk.Button(toolbar, text='Open',   command=self.open_file, **flat).pack(side='left', padx=1)
        tk.Button(toolbar, text='Save',   command=self.save_file, **flat).pack(side='left', padx=1)

        tk.Frame(toolbar, **sep_style).pack(side='left', fill='y', padx=6, pady=2)
        tk.Button(toolbar, text='Function Reference',      command=self.show_function_ref, **flat).pack(side='left', padx=1)
        tk.Button(toolbar, text='Values & Types Reference', command=self.show_values_ref,   **flat).pack(side='left', padx=1)

    # ── MAIN AREA ────────────────────────────────────
    def _build_main_area(self):
        paned = tk.PanedWindow(self.root, orient='horizontal',
                               bg='#3e4452', sashwidth=4, sashrelief='flat')
        paned.pack(fill='both', expand=True)

        # ── Left: editor + line numbers ──
        editor_frame = tk.Frame(paned, bg=BG_EDITOR)
        paned.add(editor_frame, minsize=300)

        self.line_numbers = LineNumbers(editor_frame, None, width=42)
        self.line_numbers.pack(side='left', fill='y')

        self.editor = tk.Text(
            editor_frame,
            bg=BG_EDITOR, fg=FG_DEFAULT,
            insertbackground=CURSOR_COL,
            selectbackground='#3e4452',
            font=FONT_EDITOR,
            wrap='none',
            undo=True,
            relief='flat', bd=0,
            padx=8, pady=6,
            tabs=('4c',),
        )
        self.editor.pack(side='left', fill='both', expand=True)
        self.line_numbers.text_widget = self.editor

        vsb = tk.Scrollbar(editor_frame, command=self._editor_yscroll,
                           bg=BG_SIDEBAR, troughcolor=BG_EDITOR,
                           activebackground='#4b5263')
        vsb.pack(side='right', fill='y')
        self.editor.config(yscrollcommand=vsb.set)

        hsb = tk.Scrollbar(editor_frame, orient='horizontal',
                           command=self.editor.xview,
                           bg=BG_SIDEBAR, troughcolor=BG_EDITOR)
        hsb.pack(side='bottom', fill='x')
        self.editor.config(xscrollcommand=hsb.set)

        # ── Right: output panel ──
        out_frame = tk.Frame(paned, bg=BG_OUTPUT)
        paned.add(out_frame, minsize=250)

        hdr = tk.Label(out_frame, text='OUTPUT', bg=BG_SIDEBAR, fg='#636d83',
                       font=('Segoe UI', 9, 'bold'), pady=4, padx=8, anchor='w')
        hdr.pack(fill='x')

        self.output = tk.Text(
            out_frame,
            bg=BG_OUTPUT, fg=FG_OUTPUT,
            insertbackground=FG_OUTPUT,
            selectbackground='#3e4452',
            font=FONT_OUTPUT,
            wrap='word',
            state='disabled',
            relief='flat', bd=0,
            padx=8, pady=6,
        )
        self.output.pack(fill='both', expand=True)
        self.output.tag_config('error', foreground=FG_ERROR)
        self.output.tag_config('header', foreground='#636d83')

        out_vsb = tk.Scrollbar(out_frame, command=self.output.yview,
                               bg=BG_SIDEBAR, troughcolor=BG_OUTPUT)
        out_vsb.pack(side='right', fill='y')
        self.output.config(yscrollcommand=out_vsb.set)

        # ── Syntax-highlight tags ──
        self.editor.tag_config('keyword',  foreground=FG_KEYWORD)
        self.editor.tag_config('type_kw',  foreground=FG_TYPE_KW)
        self.editor.tag_config('builtin',  foreground=FG_BUILTIN)
        self.editor.tag_config('number',   foreground=FG_NUMBER)
        self.editor.tag_config('unit',     foreground=FG_UNIT)
        self.editor.tag_config('comment',  foreground=FG_COMMENT)

        # Bind events
        self.editor.bind('<<Modified>>', self._on_change)
        self.editor.bind('<KeyRelease>', self._on_key)
        self.editor.bind('<Configure>', self.line_numbers.redraw)
        self.editor.bind('<Return>', self._auto_indent)

        # Default starter code
        self._insert_starter()

    # ── STATUS BAR ──────────────────────────────────
    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BG_SIDEBAR, pady=2)
        bar.pack(side='bottom', fill='x')
        self.status_var = tk.StringVar(value='Ready')
        tk.Label(bar, textvariable=self.status_var,
                 bg=BG_SIDEBAR, fg='#636d83',
                 font=('Segoe UI', 9), anchor='w', padx=8).pack(side='left')
        tk.Label(bar, text='PHY Language  |  UTF-8',
                 bg=BG_SIDEBAR, fg='#636d83',
                 font=('Segoe UI', 9), anchor='e', padx=8).pack(side='right')

    # ── STARTER CODE ────────────────────────────────
    def _insert_starter(self):
        starter = """\
// PHY — Physics Language  |  Press F5 or click Run to execute

givens {
    given mass m = 10kg;
    given accel a = 9.8;
}

// Newton's Second Law:  F = m * a
let force F = newton(m, a);
print F;

// Kinetic Energy:  KE = ½mv²
let velocity v = 5;
let energy KE = ke(m, v);
print KE;

// Unit conversion: grams → kilograms
let mass raw = 2500;
let mass converted = g_to_kg(raw);
print converted;
"""
        self.editor.insert('1.0', starter)
        self.editor.edit_reset()
        self._apply_highlighting()

    # ── EVENTS ──────────────────────────────────────
    def _on_change(self, _=None):
        if self.editor.edit_modified():
            self.unsaved = True
            self._update_title()
            self._apply_highlighting()
            self.editor.edit_modified(False)

    def _on_key(self, _=None):
        self.line_numbers.redraw()

    def _auto_indent(self, _=None):
        # Get the full content of the current line up to the cursor
        current_line = self.editor.get('insert linestart', 'insert lineend')
        # Measure how many leading spaces/tabs the current line has
        stripped = current_line.lstrip()
        indent = current_line[:len(current_line) - len(stripped)]
        # If the line ends with { add one extra indent level (4 spaces)
        if current_line.rstrip().endswith('{'):
            indent += '    '
        self.editor.insert('insert', '\n' + indent)
        self.line_numbers.redraw()
        return 'break'  # stop tkinter from also inserting a plain newline

    def _editor_yscroll(self, *args):
        self.editor.yview(*args)
        self.line_numbers.redraw()

    # ── SYNTAX HIGHLIGHTING ─────────────────────────
    def _apply_highlighting(self):
        for tag, _ in HIGHLIGHT_RULES:
            self.editor.tag_remove(tag, '1.0', 'end')

        content = self.editor.get('1.0', 'end-1c')
        for tag, pattern in HIGHLIGHT_RULES:
            for m in re.finditer(pattern, content):
                start = f'1.0+{m.start()}c'
                end   = f'1.0+{m.end()}c'
                self.editor.tag_add(tag, start, end)

        self.line_numbers.redraw()

    # ── RUN ─────────────────────────────────────────
    def run_code(self):
        source = self.editor.get('1.0', 'end-1c').strip()
        if not source:
            return

        self.clear_output()
        self._write_output('--- RUNNING PHY PROGRAM ---\n', 'header')

        try:
            tokens   = Lexer(source).tokenize()
            ast_tree = Parser(tokens).parse()

            # Capture AST output
            ast_buf = io.StringIO()
            with contextlib.redirect_stdout(ast_buf):
                print_ast(ast_tree)
            self._write_output('\n[AST]\n', 'header')
            self._write_output(ast_buf.getvalue())

            # Capture interpreter output
            out_buf = io.StringIO()
            with contextlib.redirect_stdout(out_buf):
                Interpreter().execute(ast_tree)
            self._write_output('\n[RESULTS]\n', 'header')
            self._write_output(out_buf.getvalue())

            self._write_output('\n--- DONE ---\n', 'header')
            self.status_var.set('Run complete')

        except SyntaxError as e:
            self._write_output(f'\n[SYNTAX ERROR]\n{e}\n', 'error')
            self.status_var.set(f'Syntax error')
        except NameError as e:
            self._write_output(f'\n[NAME ERROR]\n{e}\n', 'error')
            self.status_var.set('Name error')
        except TypeError as e:
            self._write_output(f'\n[TYPE ERROR]\n{e}\n', 'error')
            self.status_var.set('Type error')
        except Exception as e:
            self._write_output(f'\n[ERROR]\n{type(e).__name__}: {e}\n', 'error')
            self.status_var.set('Error')

    def _write_output(self, text, tag=None):
        self.output.config(state='normal')
        if tag:
            self.output.insert('end', text, tag)
        else:
            self.output.insert('end', text)
        self.output.see('end')
        self.output.config(state='disabled')

    def clear_output(self):
        self.output.config(state='normal')
        self.output.delete('1.0', 'end')
        self.output.config(state='disabled')
        self.status_var.set('Output cleared')

    # ── FILE OPERATIONS ──────────────────────────────
    def _update_title(self):
        name = os.path.basename(self.current_file) if self.current_file else 'Untitled.phy'
        dirty = ' •' if self.unsaved else ''
        self.root.title(f'PHY IDE — {name}{dirty}')

    def new_file(self):
        if not self._confirm_discard():
            return
        self.editor.delete('1.0', 'end')
        self.current_file = None
        self.unsaved = False
        self._update_title()
        self.clear_output()

    def open_file(self):
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            title='Open PHY File',
            filetypes=[('PHY files', '*.phy'), ('All files', '*.*')],
        )
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', content)
        self.current_file = path
        self.unsaved = False
        self._update_title()
        self._apply_highlighting()
        self.status_var.set(f'Opened {os.path.basename(path)}')

    def save_file(self):
        if self.current_file is None:
            self.save_as()
            return
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(self.editor.get('1.0', 'end-1c'))
        self.unsaved = False
        self._update_title()
        self.status_var.set(f'Saved {os.path.basename(self.current_file)}')

    def save_as(self):
        path = filedialog.asksaveasfilename(
            title='Save PHY File',
            defaultextension='.phy',
            filetypes=[('PHY files', '*.phy'), ('All files', '*.*')],
        )
        if not path:
            return
        self.current_file = path
        self.save_file()

    def _confirm_discard(self) -> bool:
        if not self.unsaved:
            return True
        answer = messagebox.askyesnocancel(
            'Unsaved Changes',
            'You have unsaved changes. Save before continuing?',
        )
        if answer is None:
            return False      # Cancel
        if answer:
            self.save_file()  # Yes
        return True           # No — discard

    # ── HELP DIALOGS ────────────────────────────────
    def show_function_ref(self):
        win = tk.Toplevel(self.root)
        win.title('PHY — Built-in Function Reference')
        win.geometry('700x600')
        win.configure(bg=BG_EDITOR)

        tk.Label(win, text='Built-in Functions & Unit Conversions',
                 bg=BG_EDITOR, fg=FG_DEFAULT,
                 font=('Segoe UI', 12, 'bold'), pady=10).pack()

        text = tk.Text(win, bg=BG_SIDEBAR, fg=FG_DEFAULT,
                       font=FONT_OUTPUT, wrap='word',
                       relief='flat', bd=0, padx=12, pady=8)
        text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        text.tag_config('fn',      foreground=FG_BUILTIN, font=(FONT_OUTPUT[0], FONT_OUTPUT[1], 'bold'))
        text.tag_config('desc',    foreground=FG_DEFAULT)
        text.tag_config('head',    foreground=FG_TYPE_KW,  font=(FONT_OUTPUT[0], FONT_OUTPUT[1], 'bold'))
        text.tag_config('special', foreground=FG_KEYWORD,  font=(FONT_OUTPUT[0], FONT_OUTPUT[1], 'bold'))

        # if-then-else expression note
        text.insert('end', '\n── Conditional Expression ─────────────────────────────\n', 'head')
        text.insert('end', '  if(condition) then expr else expr\n', 'fn')
        text.insert('end', '    Functional if-then-else — evaluates to a value.\n', 'desc')
        text.insert('end', '    Both then and else branches are required.\n', 'desc')
        text.insert('end', '    Operators: ==  !=  >  <  >=  <=  &&  ||\n\n', 'desc')

        categories = [
            ('── Mechanics ─────────────────────────────────────────',
             ['newton','weight','ke','pe','momentum','work','power',
              'avg_velocity','acceleration','vel_final','displacement','hooke','pressure']),
            ('── Waves & Oscillations ──────────────────────────────',
             ['wave_speed','period','frequency']),
            ('── Electricity ───────────────────────────────────────',
             ['ohm_v','ohm_i','coulomb']),
            ('── Thermodynamics ────────────────────────────────────',
             ['heat','ideal_gas_p']),
            ('── Trigonometry ──────────────────────────────────────',
             ['sin','cos','tan','asin','acos','atan']),
            ('── Distance Conversions ──────────────────────────────',
             ['km_to_m','m_to_km','cm_to_m','m_to_cm']),
            ('── Mass Conversions ──────────────────────────────────',
             ['g_to_kg','kg_to_g']),
            ('── Temperature Conversions ───────────────────────────',
             ['celsius_to_k','k_to_celsius',
              'c_to_k','k_to_c','c_to_f','f_to_c','f_to_k','k_to_f']),
            ('── Energy Conversions ────────────────────────────────',
             ['joules_to_cal','cal_to_joules']),
            ('── Speed & Force Conversions ─────────────────────────',
             ['mph_to_ms','ms_to_mph','n_to_lb','lb_to_n']),
        ]

        for heading, names in categories:
            text.insert('end', f'\n{heading}\n', 'head')
            for name in names:
                if name not in BUILTIN_FUNCTIONS:
                    continue
                fn = BUILTIN_FUNCTIONS[name]
                sig = f"{name}({', '.join(fn['params'])})"
                text.insert('end', f'  {sig}\n', 'fn')
                text.insert('end', f'    {fn["desc"]}\n\n', 'desc')

        text.config(state='disabled')

        vsb = tk.Scrollbar(win, command=text.yview, bg=BG_SIDEBAR)
        vsb.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')
        text.config(yscrollcommand=vsb.set)

    def show_values_ref(self):
        win = tk.Toplevel(self.root)
        win.title('PHY — Values & Types Reference')
        win.geometry('680x620')
        win.configure(bg=BG_EDITOR)

        tk.Label(win, text='Values & Types Reference',
                 bg=BG_EDITOR, fg=FG_DEFAULT,
                 font=('Segoe UI', 12, 'bold'), pady=10).pack()

        text = tk.Text(win, bg=BG_SIDEBAR, fg=FG_DEFAULT,
                       font=FONT_OUTPUT, wrap='word',
                       relief='flat', bd=0, padx=12, pady=8)
        text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        text.tag_config('kw',    foreground=FG_TYPE_KW,  font=(FONT_OUTPUT[0], FONT_OUTPUT[1], 'bold'))
        text.tag_config('ex',    foreground=FG_BUILTIN)
        text.tag_config('desc',  foreground=FG_DEFAULT)
        text.tag_config('head',  foreground=FG_KEYWORD,  font=(FONT_OUTPUT[0], FONT_OUTPUT[1], 'bold'))
        text.tag_config('const', foreground=FG_NUMBER,   font=(FONT_OUTPUT[0], FONT_OUTPUT[1], 'bold'))
        text.tag_config('unit',  foreground=FG_UNIT,     font=(FONT_OUTPUT[0], FONT_OUTPUT[1], 'bold'))

        # ── Type Keywords ────────────────────────────────────
        text.insert('end', '── Type Keywords ──────────────────────────────────────\n', 'head')
        text.insert('end', 'Use these after let or given to label what a variable represents.\n', 'desc')
        text.insert('end', 'Syntax:  let <type> <name> = <value>;\n\n', 'desc')

        type_entries = [
            ('mass',     'm',       'Mass',                     'kg',    'let mass m = 70kg;'),
            ('accel',    'a',       'Acceleration',             'm/s²',  'let accel a = 9.8;'),
            ('velocity', 'v',       'Velocity / Speed',         'm/s',   'let velocity v = 30;'),
            ('length',   'd or h',  'Distance / Height / Size', 'm',     'let length d = 15meter;'),
            ('force',    'F',       'Force',                    'N',     'let force F = newton(m, a);'),
            ('energy',   'E or KE', 'Energy / Work',            'J',     'let energy KE = ke(m, v);'),
            ('power',    'P',       'Power',                    'W',     'let power P = 100W;'),
            ('temp',     'T',       'Temperature',              'K/C/F', 'let temp T = 300K;'),
            ('work',     'W',       'Work done',                'J',     'let work W = work(F, d);'),
            ('time',     't',       'Time',                     's',     'let time t = 5;'),
        ]

        for kw, common, full_name, si_unit, example in type_entries:
            text.insert('end', f'  {kw}', 'kw')
            text.insert('end', f'  —  {full_name}  (SI unit: {si_unit},  common var: {common})\n', 'desc')
            text.insert('end', f'    e.g.  {example}\n\n', 'ex')

        # ── Available Units ──────────────────────────────────
        text.insert('end', '── Units  (attach directly to a number, no space) ─────\n', 'head')
        unit_entries = [
            ('kg',    'Kilograms'),
            ('g',     'Grams'),
            ('N',     'Newtons'),
            ('J',     'Joules'),
            ('W',     'Watts'),
            ('meter', 'Meters'),
            ('secs',  'Seconds'),
            ('K',     'Kelvin'),
            ('C',     'Celsius'),
            ('F',     'Fahrenheit'),
            ('rad',   'Radians'),
            ('k',     'Generic constant / old Kelvin shorthand'),
        ]
        for sym, name in unit_entries:
            text.insert('end', f'  {sym}', 'unit')
            text.insert('end', f'  —  {name}\n', 'desc')

        # ── Pre-loaded Constants ─────────────────────────────
        text.insert('end', '\n── Pre-loaded Constants  (use directly, no declaration needed) ─\n', 'head')
        const_entries = [
            ('pi',   '3.14159…',       None,          'Mathematical constant π'),
            ('e',    '2.71828…',       None,          'Euler\'s number'),
            ('grav', '9.81',           'm/s²',        'Gravitational acceleration on Earth'),
            ('c',    '299,792,458',    'm/s',         'Speed of light'),
            ('G',    '6.674×10⁻¹¹',   'm³/kg/s²',   'Universal gravitational constant'),
            ('h',    '6.626×10⁻³⁴',   'J·s',         'Planck\'s constant'),
            ('k_b',  '1.381×10⁻²³',   'J/K',         'Boltzmann constant'),
        ]
        for name, val, unit, desc in const_entries:
            u = f'  [{unit}]' if unit else ''
            text.insert('end', f'  {name}', 'const')
            text.insert('end', f'  =  {val}{u}  —  {desc}\n', 'desc')

        text.config(state='disabled')

        vsb = tk.Scrollbar(win, command=text.yview, bg=BG_SIDEBAR)
        vsb.place(relx=1.0, rely=0, relheight=1.0, anchor='ne')
        text.config(yscrollcommand=vsb.set)

    def show_language_guide(self):
        guide = """\
PHY LANGUAGE QUICK GUIDE
═════════════════════════

VARIABLE DECLARATION
  let <name> = <expression>;
  given <name> = <value>;
  let <type> <name> = <expression>;

TYPE KEYWORDS
  mass  accel  velocity  length  power  temp  force

GIVENS BLOCK  (declare all inputs up front)
  givens {
      given mass m = 10kg;
      given accel a = 9.8;
  }

PRINT
  print <expression>;

ARITHMETIC  (standard operator precedence)
  +  -  *  /  and parentheses  ( )

FUNCTION CALLS
  let F = newton(m, a);
  let energy = ke(mass, speed);
  let d_m = km_to_m(distance_km);

UNITS  (attach directly to a number, no space)
  kg  g  N  J  W  meter  secs  k

COMMENTS
  // anything after double-slash is ignored

EXAMPLE
  givens {
      given mass m = 5kg;
      given velocity v = 20;
  }
  let energy KE = ke(m, v);
  print KE;
"""
        win = tk.Toplevel(self.root)
        win.title('PHY — Language Guide')
        win.geometry('560x500')
        win.configure(bg=BG_EDITOR)
        text = tk.Text(win, bg=BG_SIDEBAR, fg=FG_DEFAULT,
                       font=FONT_OUTPUT, wrap='word',
                       relief='flat', bd=0, padx=12, pady=10)
        text.pack(fill='both', expand=True, padx=10, pady=10)
        text.insert('1.0', guide)
        text.config(state='disabled')

    def show_about(self):
        messagebox.showinfo(
            'About PHY IDE',
            'PHY — Physics Programming Language\n'
            'Version 2.0  |  Final Phase\n\n'
            'A functional, domain-specific language for\n'
            'physics students and researchers.\n\n'
            'Features:\n'
            '  • Built-in physics equations\n'
            '  • Unit conversion functions\n'
            '  • Unit-aware arithmetic\n'
            '  • No mutable loops — pure functional style\n\n'
            'CSC 321 — Programming Languages',
        )


# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app  = PhyIDE(root)

    # Ask before closing if there are unsaved changes
    def on_close():
        if app._confirm_discard():
            root.destroy()

    root.protocol('WM_DELETE_WINDOW', on_close)
    root.mainloop()


if __name__ == '__main__':
    main()

import re
from tokens import Token

TOKEN_SPEC = [
    ("COMMENT_BLOCK", r"/\*[\s\S]*?\*/"),
    ("COMMENT_LINE", r"//.*"),
    ("STRING", r'"([^"\\]|\\.)*"'),
    ("CHAR", r"'(\\.|[^\\'])'"),
    ("HEX_INT", r'0[xX][0-9A-Fa-f]+'),
    ("OCT_INT", r'0[0-7]+'),
    ("FLOAT", r'((?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)'),
    ("INT", r'[0-9]+'),
    ("ID", r'[A-Za-z_][A-Za-z0-9_]*'),
    ("OP", r'==|!=|<=|>=|->|\+\+|--|&&|\|\||<<=|>>=|<<|>>|[-+*/%<>=&|^~!:;,.(){}\[\]?]'),
    ("WHITESPACE", r'\s+'),
    ("MISMATCH", r'.'),
]

master_pat = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))

KEYWORDS = {
    "if", "else", "for", "while", "int", "float", "char", "struct", "typedef", "const", "void", "unsigned", "long", "short", "double", "switch", "case", "break", "continue", "default", "goto", "enum", "sizeof", "volatile", "register", "extern", "auto", "inline", "_Bool", "_Complex", "_Imaginary", "return"
}

def lex(code: str):
    line = 1
    col = 1
    for mo in master_pat.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == "WHITESPACE":
            # Atualiza linha/col para proxima posição e não gera token
            nl = value.count("\n")
            line += nl
            if nl:
                col = len(value) - value.rfind("\n")
            else:
                col += len(value)
            continue
        if kind == "ID" and value in KEYWORDS:
            kind = "KEYWORD"
        if kind == "MISMATCH":
            raise SyntaxError(f"Caracter inesperado {value!r} em {line}:{col}")
        tok = Token(kind, value, line, col)
        yield tok
        # Atualiza posição apos consumir esse token
        nl = value.count("\n")
        line += nl
        if nl:
            col = len(value) - value.rfind("\n")
        else:
            col += len(value)
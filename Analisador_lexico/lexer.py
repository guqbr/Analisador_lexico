import re
from tokens import Token

TOKEN_SPEC = [
    ("PP_DIRECTIVE", r'\#[^\n]*'),
    ("COMMENT_BLOCK", r"/\*[\s\S]*?\*/"),
    ("COMMENT_LINE", r"//.*"),
    ("STRING", r'"([^"\\]|\\.)*"'),
    ("CHAR", r"'(\\.|[^\\'])'"),
    ("BAD_NUM_ID", r'[0-9]+[A-Za-z_][A-Za-z0-9_]*'),
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

def _update_pos(line: int, col: int, text: str):
    nl = text.count("\n")
    if nl == 0:
        col += len(text)
    else:
        line += nl
        last_nl = text.rfind("\n")
        col = len(text) - last_nl
    return line, col

def lex(code: str):
    line = 1
    col = 1
    for mo in master_pat.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == "WHITESPACE":
            line, col = _update_pos(line, col, value)
            continue

        # BAD_NUM_ID: produz token de erro e também emite INT + ID para continuar o parsing
        if kind == "BAD_NUM_ID":
            yield Token("BAD_NUM_ID", value, line, col)
            m = re.match(r'([0-9]+)([A-Za-z_][A-Za-z0-9_]*)\Z', value)
            if m:
                num_part, id_part = m.group(1), m.group(2)
                yield Token("INT", num_part, line, col)
                id_col = col + len(num_part)
                yield Token("ID", id_part, line, id_col)
            else:
                yield Token("MISMATCH", value, line, col)
            line, col = _update_pos(line, col, value)
            continue

        if kind == "ID" and value in KEYWORDS:
            kind = "KEYWORD"

        # em vez de abortar, produza token INVALID_CHAR e continue
        if kind == "MISMATCH":
            yield Token("INVALID_CHAR", value, line, col)
            line, col = _update_pos(line, col, value)
            continue

        tok = Token(kind, value, line, col)
        yield tok
        line, col = _update_pos(line, col, value)
        # Atualiza posição apos consumir esse token
        nl = value.count("\n")
        line += nl
        if nl:
            col = len(value) - value.rfind("\n")
        else:
            col += len(value)

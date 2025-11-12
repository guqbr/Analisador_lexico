import re
from tokens import Token

TOKEN_SPEC = [
    ("PP_DIRECTIVE",  r'\#[^\n]*'),
    ("COMMENT_BLOCK", r"/\*[\s\S]*?\*/"),
    ("COMMENT_LINE",  r"//.*"),
    ("STRING",        r'"([^"\\]|\\.)*"'),
    ("CHAR",          r"'(\\.|[^\\'])'"),
    ("HEX_INT",       r'0[xX][0-9A-Fa-f]+'),
    ("OCT_INT",       r'0[0-7]+'),
    ("FLOAT",         r'((?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)'),
    ("INT",           r'[0-9]+'),
    ("BAD_NUM_ID",    r'[0-9]+[A-Za-z_][A-Za-z0-9_]*'),
    ("ID",            r'[A-Za-z_][A-Za-z0-9_]*'),
    ("OP",            r'==|!=|<=|>=|->|\+\+|--|&&|\|\||<<=|>>=|<<|>>|[-+*/%<>=&|^~!:;,.(){}\[\]?]'),
    ("WHITESPACE",    r'\s+'),
    ("MISMATCH",      r'.'),
]

master_pat = re.compile("|".join(f"(?P<{n}>{p})" for n, p in TOKEN_SPEC))

KEYWORDS = {
    "auto","break","case","char","const","continue","default","do","double","else","enum",
    "extern","float","for","goto","if","inline","int","long","register","restrict","return",
    "short","signed","sizeof","static","struct","switch","typedef","union","unsigned","void",
    "volatile","while","_Bool","_Complex","_Imaginary"
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

def _unescaped_length(s: str) -> int:
    i = 0
    count = 0
    while i < len(s):
        if s[i] == '\\':
            i += 1
            if i < len(s):
                # trata escape (considera-se como 1 char)
                i += 1
            count += 1
        else:
            i += 1
            count += 1
    return count

def lex(code: str):
    line = 1
    col = 1
    for mo in master_pat.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == "WHITESPACE":
            line, col = _update_pos(line, col, value)
            continue

        # BAD_NUM_ID: tente reconhecer casos hex/oct/float que foram erroneamente casados
        if kind == "BAD_NUM_ID":
            # se for hex/octal/float, transforme no token correto (protege contra ordem)
            if re.fullmatch(r'0[xX][0-9A-Fa-f]+', value):
                yield Token("HEX_INT", value, line, col)
            elif re.fullmatch(r'0[0-7]+', value):
                yield Token("OCT_INT", value, line, col)
            elif re.fullmatch(r'((?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[0-9]+[eE][+-]?[0-9]+)', value):
                yield Token("FLOAT", value, line, col)
            else:
                # comportamento atual: emitimos token de erro e tokens de recuperação (INT + RECOVERED_ID)
                yield Token("BAD_NUM_ID", value, line, col)
                m = re.match(r'([0-9]+)([A-Za-z_][A-Za-z0-9_]*)\Z', value)
                if m:
                    num_part, id_part = m.group(1), m.group(2)
                    yield Token("INT", num_part, line, col)
                    id_col = col + len(num_part)
                    yield Token("RECOVERED_ID", id_part, line, id_col)
                else:
                    yield Token("MISMATCH", value, line, col)
            line, col = _update_pos(line, col, value)
            continue

        # validar CHAR: se o conteúdo não representa exatamente 1 caractere, produzir BAD_CHAR
        if kind == "CHAR":
            inner = value[1:-1]  # conteúdo entre aspas simples
            effective_len = _unescaped_length(inner)
            if effective_len != 1:
                # emitir token de erro (será coletado pelo main e reportado), não aborta
                yield Token("BAD_CHAR", value, line, col)
                line, col = _update_pos(line, col, value)
                continue
            else:
                # é char válido
                yield Token("CHAR", value, line, col)
                line, col = _update_pos(line, col, value)
                continue

        if kind == "ID" and value in KEYWORDS:
            kind = "KEYWORD"
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

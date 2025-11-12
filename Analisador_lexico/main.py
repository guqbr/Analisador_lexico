import argparse
import sys
import re

from lexer import lex
from tokens import Token
from symbols import SymbolTable

def format_value(v: str) -> str:
    return v.replace("\n", "\\n").replace("\t", "\\t")

def main():
    p = argparse.ArgumentParser(description="Analisador lexico - imprime tokens e tabela")
    p.add_argument("path", help="arquivo fonte .c")
    p.add_argument("--show-comments", action="store_true", help="imprimir tokens de comentario")
    args = p.parse_args()

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Erro ao abrir '{args.path}': {e}", file=sys.stderr)
        sys.exit(2)

    tokens = list(lex(code))
    # separar diretivas de pré-processador
    pp_directives = [t for t in tokens if t.type == "PP_DIRECTIVE"]
    # filtrar tokens que serão exibidos (remover PP_DIRECTIVE da lista principal)
    visible_tokens = [t for t in tokens if t.type != "PP_DIRECTIVE"]
    
    # tokenizar o alvo dos #include em PP_ID / PP_OP e inserir antes dos tokens visíveis
    include_tokens = []
    for pp in pp_directives:
        txt = pp.value.strip()
        m = re.search(r'#\s*include\s*(<[^>]*>|"[^"]*"|\S+)', txt)
        if not m:
            continue
        tgt = m.group(1)
        col = pp.col + pp.value.find(tgt)
        buf = ""
        for ch in tgt:
            if ch.isalnum() or ch == "_":
                buf += ch
                col += 1
                continue
            if buf:
                include_tokens.append(Token("PP_ID", buf, pp.line, col - len(buf)))
                buf = ""
            include_tokens.append(Token("PP_OP", ch, pp.line, col))
            col += 1
        if buf:
            include_tokens.append(Token("PP_ID", buf, pp.line, col - len(buf)))

    # colocar tokens do include antes dos demais para aparecerem na "lista de tokens"
    if include_tokens:
        visible_tokens = include_tokens + visible_tokens

    st = SymbolTable()
    for t in visible_tokens:
        if t.type != "ID":
            continue
        # pular IDs vazios
        if not t.value or t.value.strip() == "":
            continue
        if st.get(t.value) is None:
            st.add(t.value, line=t.line)

    name_to_index = {s.name: s.index for s in st.items()}

    # imprimir includes como "Palavras reservadas:" (apenas '#' e 'include' conforme pedido)
    if pp_directives:
        print("Palavras reservadas:")
        for pp in pp_directives:
            # detectar apenas includes; outras diretivas ficam silenciosas
            if pp.value.lstrip().startswith("#") and "include" in pp.value:
                print("#")
                print("include")

    # imprimir lista de tokens (filtra whitespace e, opcionalmente, comentários)
    print("lista de tokens:")
    for tok in visible_tokens:
        if not args.show_comments and tok.type in ("COMMENT_LINE", "COMMENT_BLOCK", "WHITESPACE"):
            continue
        # erros léxicos aparecem com prefixo ERR:
        if tok.type in ("BAD_NUM_ID", "INVALID_CHAR", "BAD_CHAR"):
            print(f"ERR:{tok.value}")
            continue
        # tokens sintéticos de includes (se existirem)
        if tok.type in ("PP_ID", "PP_OP"):
            print(tok.value)
            continue
        if tok.type == "KEYWORD":
            print(tok.value)
        elif tok.type == "ID":
            idx = name_to_index.get(tok.value, 0)
            print(f"id,{idx}")
        elif tok.type in ("INT", "HEX_INT", "OCT_INT", "FLOAT"):
            print(f"number,{tok.value}")
        elif tok.type == "STRING":
            print(f'string,"{format_value(tok.value[1:-1])}"')
        elif tok.type == "CHAR":
            print(f"char,{format_value(tok.value)}")
        else:
            print(tok.value)

    # imprimir tabela de símbolos
    print("\ntabela de simbolos:")
    for s in st.items():
        print(f"#{s.index}: {s.name}")

if __name__ == "__main__":
    main()

import argparse
import sys
import re
from collections import Counter, defaultdict

from lexer import lex
from tokens import Token
from symbols import SymbolTable
from parser import SimpleParser

def format_value(v: str) -> str:
    # mostra valor em uma linha, com escapes visiveis
    return v.replace("\n", "\\n").replace("\t", "\\t")

def _extract_include_target(pp_value: str):
    m = re.search(r'#\s*include\s*(<[^>]+>|"[^"]+")', pp_value)
    return m.group(1) if m else None

def main():
    p = argparse.ArgumentParser(description="Analisador lexico para C (Python)")
    p.add_argument("path", help="arquivo fonte .c")
    p.add_argument("--show-comments", action="store_true", help="imprimir tokens de comentario")
    args = p.parse_args()

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Erro ao abrir '{args.path}': {e}", file=sys.stderr)
        sys.exit(2)

    # lexema inicial
    tokens = list(lex(code))

    # separar diretivas de pré-processador (PP_DIRECTIVE) do restante
    pp_directives = [t for t in tokens if t.type == "PP_DIRECTIVE"]
    normal_tokens = [t for t in tokens if t.type != "PP_DIRECTIVE"]

    # tabela de simbolos
    st = SymbolTable()

    # tratar includes: imprimir #include antes da lista de tokens e adicionar o alvo na symbol table
    includes = []
    for pp in pp_directives:
        tgt = _extract_include_target(pp.value)
        if tgt:
            # limpar < > ou " "
            clean = tgt.strip('<>"')
            includes.append((pp, tgt, clean))

    # gerar tokens sintéticos para o conteúdo dos includes e inseri-los nos normal_tokens
    include_tokens: list[Token] = []
    for pp, raw_tgt, clean in includes:
        s = raw_tgt.strip()
        col = pp.col
        buf = ""
        for ch in s:
            if ch.isalnum() or ch == "_":
                buf += ch
                col += 1
                continue
            # flush buffer como ID
            if buf:
                include_tokens.append(Token("PP_ID", buf, pp.line, col - len(buf)))
                buf = ""
            # emitir o caracter não-alnum como OP token (p.ex. < . > " ')
            include_tokens.append(Token("PP_OP", ch, pp.line, col))
            col += 1
        if buf:
            include_tokens.append(Token("PP_ID", buf, pp.line, col - len(buf)))

    # inserir tokens dos includes antes dos tokens normais (para aparecerem na lista de tokens)
    if include_tokens:
        normal_tokens = include_tokens + normal_tokens
    # popular symbol table via parser (usar apenas tokens normais)
    parser = SimpleParser(normal_tokens, st)
    parser.process()

    # garantir que ids usados também entrem na tabela (ordem de primeira aparição)
    for tok in normal_tokens:
        if tok.type == "ID" and st.get(tok.value) is None:
            st.add(tok.value, line=tok.line)

    # mapa nome -> indice
    name_to_index = {s.name: s.index for s in st.items()}

    # imprimir apenas a palavra reservada #include (se houver includes)
    if includes:
        print("Palavras reservadas:")
        for _pp, _raw_tgt, _clean in includes:
            print("#include")

    # imprimir lista de tokens (exclui diretivas)
    print("lista de tokens:")
    for tok in normal_tokens:
        if not args.show_comments and tok.type in ("COMMENT_LINE", "COMMENT_BLOCK", "WHITESPACE"):
            continue
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

    # imprimir tabela de simbolos na ordem de inserção
    print("\ntabela de simbolos:")
    for s in st.items():
        print(f"#{s.index}: {s.name}")

if __name__ == "__main__":
    main()

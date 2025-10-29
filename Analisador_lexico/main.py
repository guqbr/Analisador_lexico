import argparse
import sys

from lexer import lex
from symbols import SymbolTable
from parser import SimpleParser

def format_value(v: str) -> str:
    # mostra valor em uma linha, com escapes visiveis
    return v.replace("\n", "\\n").replace("\t", "\\t")

def main():
    p = argparse.ArgumentParser(description="Analisador lexico para C (Python)")
    p.add_argument("path", help="arquivo fonte .c")
    p.add_argument("--show-comments", action="store_true", help="imprimir tokens de comentario")
    args = p.parse_args()

    try:
        with open(args.path, "r" , encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Erro ao abrir '{args.path}': {e}", file=sys.stderr)
        sys.exit(2)

    st = SymbolTable()
    try:
        tokens = list(lex(code))

        bad_tokens = [t for t in tokens if t.type in ("BAD_NUM_ID", "INVALID_CHAR")]
        normal_tokens = [t for t in tokens if t.type not in ("BAD_NUM_ID", "INVALID_CHAR")]

        for e in bad_tokens:
            if e.type == "BAD_NUM_ID":
                print(f"Erro lexico: identificador invalido {e.value!r} em {e.line}:{e.col}", file=sys.stderr)
            else:
                print(f"Erro lexico: caractere invalido {e.value!r} em {e.line}:{e.col}", file=sys.stderr)

        # popula a symbol table via parser
        parser = SimpleParser(normal_tokens, st)
        parser.process()

        #garantir que todos os ids apareçam na tabela
        for tok in normal_tokens:
            if tok.type == "ID" and st.get(tok.value) is None:
                st.add(tok.value, line=tok.line)

        #mapa nome -> indice(ordem correta)
        name_to_index = {s.name: s.index for s in st.items()}

        #imprimir
        print("lista de tokens:")
        for tok in normal_tokens:
            if not args.show_comments and tok.type in ("COMMENT_LINE", "COMMENT_BLOCK", "WHITESPACE", "PP_DIRECTIVE"):
                continue
            if tok.type == "KEYWORD":
                print(tok.value)
            elif tok.type == "ID":
                idx = name_to_index.get(tok.value, 0)
                print(f"id,{idx}")
            elif tok.type in ("INT", "HEX_INT", "OCT_INT", "FLOAT"):
                print(f"number,{tok.value}")
            elif tok.type == "STRING":
                print(f'string,{format_value(tok.value)}')
            elif tok.type == "CHAR":
                print(f"char,{format_value(tok.value)}")
            else:
                #imprime operador/pontuação
                print(tok.value)

    except Exception as e:
        print(f"Erro lexico: {e}", file=sys.stderr)
        sys.exit(1)

    #imprime a tabela de simbolos
    print("\ntabela de simbolos:")
    for s in st.items():
        print(f"#{s.index}: {s.name}")

if __name__ == "__main__":
    main()

import argparse
import sys

from lexer import lex
from symbols import SymbolTable

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
        for tok in lex(code):
            if not args.show_comments and tok.type in ("COMMENT_LINE", "COMMENT_BLOCK"):
                continue
            # Adiciona identificadores a tabela de simbolos
            if tok.type == "ID":
                st.add(tok.value, line=tok.line)
            print(f"{tok.line}:{tok.col}\t{tok.type}\t{format_value(tok.value)}")
    except Exception as e:
        print(f"Erro lexico: {e}", file=sys.stderr)
        sys.exit(1)

    # Resumo da tabela de simbolos
    print("\nTabela de simbolos (quantiade = {}):".format(len(st)))
    for s in st.items():
        print(f"{s.index:3d} {s.name:20s} occ={s.occurrences:3d} first_line={s.first_decl_line}")

if __name__ == "__main__":
    main()

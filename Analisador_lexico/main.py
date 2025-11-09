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

    # tenta formas completas primeiro
    m = re.search(r'#\s*include\s*(<[^>]+>|"[^"]+")', pp_value)
    if m:
        return m.group(1)
    # tenta formas incompletas (abre '<' ou abre '"' e pega até o fim da diretiva)
    m2 = re.search(r'#\s*include\s*(<\S+|\\"\S+|"[^"]*$|<[^>]*$)', pp_value)
    if m2:
        return m2.group(1)
    # fallback: pega o primeiro token após include
    m3 = re.search(r'#\s*include\s+(\S+)', pp_value)
    return m3.group(1) if m3 else None

def main():
    p = argparse.ArgumentParser(description="Analisador lexico para C (Python)")
    p.add_argument("path", help="arquivo fonte .c")
    p.add_argument("--show-comments", action="store_true", help="imprimir tokens de comentario")
    p.add_argument("--quiet", action="store_true", help="suprimir mensagens de erro/aviso")    
    args = p.parse_args()

    try:
        with open(args.path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"Erro ao abrir '{args.path}': {e}", file=sys.stderr)
        sys.exit(2)

    # lexema inicial
    tokens = list(lex(code))

    # linhas do arquivo para contexto de erro
    lines = code.splitlines()    

    # separar diretivas de pré-processador (PP_DIRECTIVE)
    pp_directives = [t for t in tokens if t.type == "PP_DIRECTIVE"]

    # coletar e reportar erros léxicos, mas NÃO imprimir os tokens de erro na lista
    # não remover BAD_CHAR para que o token apareça na lista; continua sendo reportado em stderr
    LEX_ERROR_TYPES = ("BAD_NUM_ID", "INVALID_CHAR", "UNCLOSED_STRING", "UNCLOSED_COMMENT")

    bad_tokens = [t for t in tokens if t.type in LEX_ERROR_TYPES]
    if not args.quiet:
        for e in bad_tokens:
            line_num = e.line
            col = e.col
            # mensagem principal
            if e.type == "BAD_NUM_ID":
                msg = f"Erro lexico: identificador invalido {e.value!r} em {line_num}:{col}"
            elif e.type == "INVALID_CHAR":
                msg = f"Erro lexico: caractere invalido {e.value!r} em {line_num}:{col}"
            elif e.type == "BAD_CHAR":
                msg = f"Erro lexico: literal de char invalido {e.value!r} em {line_num}:{col}"
            else:
                msg = f"Erro lexico: {e.type} {e.value!r} em {line_num}:{col}"
            print(msg, file=sys.stderr)
            # imprimir linha de contexto e caret apontando a coluna
            if 1 <= line_num <= len(lines):
                line_text = lines[line_num - 1]
                print(line_text, file=sys.stderr)
                caret_pos = max(0, min(len(line_text), col - 1))
                caret_line = " " * caret_pos + "^"
                print(caret_line, file=sys.stderr)
            else:
                print("(sem contexto de linha)", file=sys.stderr)

    # construir normal_tokens excluindo diretivas e tokens de erro
    normal_tokens = [t for t in tokens if t.type not in LEX_ERROR_TYPES and t.type != "PP_DIRECTIVE"]

    # tabela de simbolos
    st = SymbolTable()

    # tratar includes: imprimir #include antes da lista de tokens e adicionar o alvo na symbol table
    includes = []
    for pp in pp_directives:
        tgt = _extract_include_target(pp.value)
        if not tgt:
            includes.append((pp, pp.value, ""))  # mantém raw directive para tokenização posterior
            continue

        # NÃO modificar/autocorrigir 'tgt' — apenas armazenar
        includes.append((pp, tgt, tgt.strip('<>"')))

        # se malformado (abrindo sem fechar), apenas armazenar — sem imprimir aviso
        if (tgt.startswith("<") and not tgt.endswith(">")) or (tgt.startswith('"') and not tgt.endswith('"')):
            pass

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
    
    # tokens usados pelo parser (removendo apenas os tokens de erro)
    parser_tokens = [t for t in normal_tokens if t.type not in LEX_ERROR_TYPES]
    # tokens para impressão: incluir também os tokens de erro (BAD_NUM_ID/INVALID_CHAR etc.)
    # e incluir os PP tokens gerados (include_tokens já faz parte de normal_tokens)
    print_tokens = []
    for t in include_tokens:
        print_tokens.append(t)
    for t in tokens:
        if t.type == "PP_DIRECTIVE" or t.type == "WHITESPACE":
            continue
        print_tokens.append(t)
    # popular symbol table via parser (usar parser_tokens que não contêm tokens de erro)
    parser = SimpleParser(parser_tokens, st)
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
            print("#")
            print("include")

    # imprimir lista de tokens (exclui diretivas); agora usamos print_tokens para incluir tokens de erro
    print("lista de tokens:")
    for tok in print_tokens:
        # pular tokens vazios/apenas espaços e comentários (evita linhas em branco)
        if (tok.value is None) or (isinstance(tok.value, str) and tok.value.strip() == ""):
            continue
        if not args.show_comments and tok.type in ("COMMENT_LINE", "COMMENT_BLOCK", "WHITESPACE"):
            continue
        # mostrar lexemas de erro BAD_NUM_ID / INVALID_CHAR exatamente como apareceram
        if tok.type == "BAD_NUM_ID":
            print(f"ERR:{tok.value}")
            continue
        if tok.type == "INVALID_CHAR":
            print(f"ERR:{tok.value}")
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

from typing import List, Optional
from tokens import Token
from symbols import SymbolTable

TYPE_SPECIFIERS = {
    "int", "float", "double", "char", "void", "long", "short", "unsigned", "signed", "_Bool"
}
TYPE_QUALIFIERS = {"const", "volatile", "register", "static", "extern", "auto", "inline"}
ALL_TYPE_WORDS = TYPE_SPECIFIERS | TYPE_QUALIFIERS

class SimpleParser:
    def __init__(self, tokens: List[Token], symtab: SymbolTable):
        self.tokens = tokens
        self.n = len(tokens)
        self.i = 0
        self.symtab = symtab
        self.scope_stack = ["global"]
        self._scope_id = 0

    def current(self) -> Optional[Token]:
        return self.tokens[self.i] if self.i < self.n else None
    
    def peek(self, offset: int = 1) -> Optional[Token]:
        idx = self.i + offset
        return self.tokens[idx] if idx < self.n else None
    
    def advance(self) -> Optional[Token]:
        t = self.current()
        if t is not None:
            self.i += 1
        return t
    
    def push_scope(self, name: Optional[str] = None):
        self._scope_id += 1
        scope_name = name or f"scope{self._scope_id}"
        self.scope_stack.append(scope_name)
        return scope_name
    
    def pop_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def current_scope(self):
        return self.scope_stack[-1]
    
    def process(self):
        while self.i < self.n:
            t = self.current()
            if t is None:
                break

            if t.type == "OP" and t.value == "{":
                self.push_scope()
                self.advance()
                continue
            if t.type == "OP" and t.value == "}":
                self.pop_scope()
                self.advance()
                continue

            if t.type == "KEYWORD" and t.value in ALL_TYPE_WORDS:
                self.parse_declaration()
                continue

            if t.type == "ID" and self.peek() is not None and self.peek().value == "(":
                self.symtab.add(t.value, kind="call", line=t.line, scope=self.current_scope())
                self.advance()
                continue

            self.advance()

    def parse_declaration(self):

        type_parts = []
        while self.current() and self.current().type == "KEYWORD" and self.current().value in ALL_TYPE_WORDS:
            type_parts.append(self.current().value)
            self.advance()

        base_type = " ".join(type_parts) if type_parts else None

        while True:

            ptr = 0

            while self.current() and self.current().type == "OP" and self.current().value == "*":
                ptr += 1
                self.advance()

            name_tok = self.current()
            if name_tok and name_tok.type == "ID":
                name = name_tok.value

                if self.peek() and self.peek().value == "(":

                    self.advance()

                    self.advance()
                    params = self.parse_param_list()

                    after = self.current()
                    kind = "func"
                    declared_type = base_type
                    self.symtab.add(name, kind=kind, declared_type=declared_type, line=name_tok.line, scope="global")

                    if after and after.type == "OP" and after.value == "{":

                        self.push_scope(name)
                        for p_name, p_type, p_line in params:
                            self.symtab.add(p_name, kind="param", declared_type=p_type, line=p_line, scope=self.current_scope())
                else:

                    self.symtab.add(name, kind="var", declared_type=(base_type + " " + "* " * ptr).strip(), line=name_tok.line, scope=self.current_scope())
                    self.advance()

            else:

                pass

            if self.current() and self.current().type == "OP" and self.current(). value == "=":
                self.advance()
                self.skip_until_commasemicolon()

            if self.current() and self.current().type == "OP" and self.current().value == ",":
                self.advance()
                continue

            if self.current() and self.current().type == "OP" and self.current().value == ";":
                self.advance()
                break

            if self.current() and self.current().type == "OP" and self.current().value == "{":
                break

            if self.current():
                self.advance()
                break
            else:
                break
    
    def parse_param_list(self):

        params = []
        depth = 0
        while self.current():
            t = self.current()
            if t.type == "OP" and t.value == ")":
                self.advance()
                break

            type_parts = []
            while self.current() and self.current().type == "KEYWORD" and self.current().value in ALL_TYPE_WORDS:
                type_parts.append(self.current().value)
                self.advance()
            ptr = 0
            while self.current() and self.current().type == "OP" and self.current().value == "*":
                ptr += 1
                self.advance()

            if self.current() and self.current().type == "ID":
                pname = self.current().value
                ptype = (" ".join(type_parts) + " " + "*" * ptr).strip()
                params.append((pname, ptype, self.current().line))
                self.advance()

            if self.current() and self.current().type == "OP" and self.current().value == ",":
                self.advance()
                continue

            if self.current() and self.current().type == "OP" and self.current().value == "...":
                self.advance()
                continue

            if self.current() and self.current().type != "OP":
                self.advance()

            if depth > 10000:
                break
        return params
    
    def skip_until_commasemicolon(self):

        depth = 0
        while self.current():
            t = self.current()
            if t.type == "OP":
                if t.value in "([{":
                    depth += 1
                elif t.value in ")]}":
                    depth = max(0, depth - 1)
                elif depth == 0 and (t.value == "," or t.value == ";"):
                    return
            self.advance()

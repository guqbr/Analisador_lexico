from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class Symbol:
    name: str
    kind: Optional[str] = None
    declared_type: Optional[str] = None
    scope: Optional[str] = None
    first_decl_line: Optional[int] = None
    occurrences: int = 0
    index: int = 0

class SymbolTable:
    def __init__(self):
        self.__map: Dict[str, Symbol] = {}
        self._next_index = 1

    def add(self, name: str, kind: Optional[str] = None, declared_type: Optional[str] = None, scope: Optional[str] = None, line: Optional[int] = None) -> Symbol:
        sym = self.__map.get(name)
        if sym is None:
            sym = Symbol(name=name, kind=kind, declared_type=declared_type, scope=scope, first_decl_line=line, occurrences=1, index=self._next_index)
            self.__map[name] = sym
            self._next_index += 1
        else:
            sym.occurrences += 1
            if sym.first_decl_line is None and line is not None:
                sym.first_decl_line = line
            if sym.kind is None and kind is not None:
                sym.kind = kind
            if sym.declared_type is None and declared_type is not None:
                sym.declared_type = declared_type
            if sym.scope is None and scope is not None:
                sym.scope = scope
        return sym
    
    def get(self, name: str) -> Optional[Symbol]:
        return self.__map.get(name)
    
    def __len__(self) -> int:
        return len(self.__map)
    
    def items(self) -> List[Symbol]:
        return sorted(self.__map.values(), key=lambda s: s.index)
    
    def dump(self) -> List[Dict]:
        return [
            {
                "index": s.index,
                "name": s.name,
                "kind": s.kind,
                "declared_type": s.declared_type,
                "scope": s.scope,
                "first_decl_line": s.first_decl_line,
                "occurrences": s.occurrences
            }
            for s in self.items()
        ]
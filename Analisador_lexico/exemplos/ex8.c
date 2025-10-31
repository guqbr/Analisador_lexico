#include <stdio.h>

enum Estado {
    SOLTEIRO
    CASADO,
    DIVORCIADO,
};

union U {
    int x;
    float y;
};

int main() {
    enum Estado e = 10; // inválido
    union U u;
    u.x = 10;
    printf("%f\n", (char)u);  // cast inválido
    return 0;
}

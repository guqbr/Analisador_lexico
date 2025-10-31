#include <stdio.h>

int soma(int a, int b) {
    return a + b;
}

int main() {
    int resultado = soma(5, 7);
    if (resultado > 10) {
        printf("Maior que 10!\n");
    } else {
        printf("Menor ou igual a 10.\n");
    }
    return 0;
}

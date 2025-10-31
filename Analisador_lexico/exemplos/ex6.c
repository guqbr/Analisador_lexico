#include <stdlib.h>
#include <stdio.h>

int main() {
    int *v = malloc(10 * sizeof(int));

    for (int i = 0; i < 10; i++) {
        v[i] = i * 2;
    
    printf("%d", v[10]); // out of bounds

    free(v;

    int *x = &10;   // apontando para literal

    *x++;
    return 0;
}

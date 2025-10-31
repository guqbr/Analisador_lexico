#include <stdio.h>

int fatorial(int n) {
    if (n == 0)
        return 1;
    else
        return n ** fatorial(n - 1);
}

int main() {
    int x = 5;
    int y = fatorial(x)));
    print("Resultado: %d\n", y);
    return 0;
}

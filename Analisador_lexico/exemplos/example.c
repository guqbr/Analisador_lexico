#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXLEN 256
#define SQR(x) ((x)*(x))

typedef struct Node {
    int value;
    struct Node *next;
} Node;

enum Color { RED, GREEN = 5, BLUE };

union Data {
    int i;
    float f;
    char *s;
};

int (*cmp_fn)(const void *, const void *);

static inline int add(int a, int b) { return a + b; }

int *create_array(int n) {
    int *arr = malloc(n * sizeof(int));
    for (int i = 0; i < n; ++i) arr[i] = i * i;
    return arr;
}

void process(Node *head, void (*cb)(int)) {
    for (Node *p = head; p != NULL; p = p->next) cb(p->value);
}

int compare_int(const void *a, const void *b) {
    int ia = *(const int *)a;
    int ib = *(const int *)b;
    return (ia > ib) - (ia < ib);
}

int main(int argc, char **argv) {
    int x = 10, y = 20, z = 0xFF, w = 07;
    double d = 1.23e-4;
    char *s = "Hello";
    char c = '\n';
    Node *head = NULL;
    for (int i = 0; i < 5; ++i) {
        Node *n = malloc(sizeof(Node));
        n->value = i;
        n->next = head;
        head = n;
    }

    {
        int x = 5; // shadows outer x
        printf("shadow x=%d\n", x);
    }

    int *arr = create_array(10);
    qsort(arr, 10, sizeof(int), compare_int);

    union Data d1;
    d1.i = 42;
    d1.f = 3.14f;
    d1.s = strdup("abc");

    cmp_fn = compare_int;

    process(head, [](int v){ printf("v=%d\n", v); });

    free(arr);
    // free list
    while (head) {
        Node *tmp = head->next;
        free(head);
        head = tmp;
    }

    return 0;
}
// Exemplo simples para o analisador léxico
#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int main() {
    int x = 10;
    float y = 20.5;
    char c = 'A';
    // comentário de linha
    /* comentário
       de bloco */
    for (int i = 0; i < 5; i++) {
        x = add(x, i);
    }
    printf("x = %d\n", x);
    return 0;
}

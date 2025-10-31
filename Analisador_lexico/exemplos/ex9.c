#define SOMA(x, y) ((x)+(y)

typedef struct {
    float prec@o;
    int qtd;
} Produto;

int main() {
    Produto p;
    p.prec@o = 10.5;
    p.qtd = 3;

    float total = SOMA(p.prec@o, p.qtd));
    printf("Total: %f\n", total);
    return 0;
}

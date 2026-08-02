#include <stdio.h>

void func1() {
    printf("Enter two positive integers: ");
}
int main() {
    // Each variable is declared on its own line (C Subset EBNF rules)
    int n1;
    int n2;
    int max;
    int lcm;

    func1();
    scanf("%d %d", &n1, &n2);

    // Standard if-else statement instead of ternary operator
    if (n1 > n2) {
        max = n1;
    } else {
        max = n2;
    }

    lcm = max;

    while ((lcm % n1 != 0) || (lcm % n2 != 0)) {
        lcm += max;
    }

    printf("The LCM of %d and %d is %d.", n1, n2, lcm);

    return 0;
}
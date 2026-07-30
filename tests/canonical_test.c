/* 
   Point Structure Definition 
   Represents coordinates in a 2D space.
*/
struct Point {
    int x;
    int y;
};

/* 
   Factorial recursive calculation
   Guarantees mathematically correct recursion.
*/
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

void main() {
    struct Point p;
    p.x = 42;
    int value = factorial(5); // Context-aware function highlight!
    int uninit;
    int error = uninit; // Triggers definite assignment uninitialized warning
    int err = @; // Triggers invalid token error highlight
}
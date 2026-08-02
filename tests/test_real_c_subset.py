import pytest
from cc_analyzer.core.lexer import Lexer
from cc_analyzer.core.parser import Parser
from cc_analyzer.core.tokens import TokenType

REAL_C_PROGRAMS = [
    # 1. Least Common Multiple (LCM)
    """
    #include <stdio.h>
    int main() {
        int n1 = 12;
        int n2 = 15;
        int max;
        int lcm;
        if (n1 > n2) {
            max = n1;
        } else {
            max = n2;
        }
        lcm = max;
        while ((lcm % n1 != 0) || (lcm % n2 != 0)) {
            lcm += max;
        }
        printf("LCM is %d", lcm);
        return 0;
    }
    """,
    # 2. Greatest Common Divisor (GCD)
    """
    #include <stdio.h>
    int main() {
        int n1 = 81;
        int n2 = 153;
        while (n1 != n2) {
            if (n1 > n2) {
                n1 -= n2;
            } else {
                n2 -= n1;
            }
        }
        printf("GCD is %d", n1);
        return 0;
    }
    """,
    # 3. Factorial of a Number (Iterative)
    """
    #include <stdio.h>
    int main() {
        int n = 5;
        int i;
        int fact = 1;
        for (i = 1; i <= n; i = i + 1) {
            fact = fact * i;
        }
        printf("Fact: %d", fact);
        return 0;
    }
    """,
    # 4. Fibonacci Series Generator (Iterative)
    """
    #include <stdio.h>
    int main() {
        int n = 10;
        int t1 = 0;
        int t2 = 1;
        int nextTerm = 0;
        int i;
        for (i = 1; i <= n; i = i + 1) {
            printf("%d ", t1);
            nextTerm = t1 + t2;
            t1 = t2;
            t2 = nextTerm;
        }
        return 0;
    }
    """,
    # 5. Prime Number Checker
    """
    #include <stdio.h>
    int main() {
        int n = 29;
        int i;
        int is_prime = 1;
        for (i = 2; i <= n / 2; i = i + 1) {
            if (n % i == 0) {
                is_prime = 0;
            }
        }
        if (is_prime == 1) {
            printf("Prime");
        } else {
            printf("Not Prime");
        }
        return 0;
    }
    """,
    # 6. Swapping Two Numbers Using Pointers
    """
    #include <stdio.h>
    void swap(int* x, int* y) {
        int temp = *x;
        *x = *y;
        *y = temp;
    }
    int main() {
        int a = 10;
        int b = 20;
        swap(&a, &b);
        return 0;
    }
    """,
    # 7. Reverse an Integer
    """
    #include <stdio.h>
    int main() {
        int n = 1234;
        int rev = 0;
        int remainder;
        while (n != 0) {
            remainder = n % 10;
            rev = rev * 10 + remainder;
            n = n / 10;
        }
        return 0;
    }
    """,
    # 8. Check Armstrong Number
    """
    #include <stdio.h>
    int main() {
        int num = 153;
        int original = num;
        int rem;
        int result = 0;
        while (original != 0) {
            rem = original % 10;
            result = result + rem * rem * rem;
            original = original / 10;
        }
        if (result == num) {
            printf("Armstrong");
        }
        return 0;
    }
    """,
    # 9. Simple Struct Definitions and Allocations
    """
    #include <stdio.h>
    struct Student {
        int id;
        float gpa;
    };
    int main() {
        struct Student s;
        s.id = 101;
        s.gpa = 3.8;
        return 0;
    }
    """,
    # 10. Check Leap Year
    """
    #include <stdio.h>
    int main() {
        int year = 2024;
        if (year % 400 == 0) {
            printf("Leap Year");
        } else {
            if (year % 100 == 0) {
                printf("Not Leap Year");
            } else {
                if (year % 4 == 0) {
                    printf("Leap Year");
                } else {
                    printf("Not Leap Year");
                }
            }
        }
        return 0;
    }
    """,
    # 11. Bubble Sort Representation
    """
    #include <stdio.h>
    void sort(int* arr, int size) {
        int i;
        int j;
        int temp;
        for (i = 0; i < size - 1; i = i + 1) {
            for (j = 0; j < size - i - 1; j = j + 1) {
                if (arr[j] > arr[j + 1]) {
                    temp = arr[j];
                    arr[j] = arr[j + 1];
                    arr[j + 1] = temp;
                }
            }
        }
    }
    """,
    # 12. Selection Sort Representation
    """
    #include <stdio.h>
    void selection_sort(int* arr, int n) {
        int i;
        int j;
        int min_idx;
        int temp;
        for (i = 0; i < n - 1; i = i + 1) {
            min_idx = i;
            for (j = i + 1; j < n; j = j + 1) {
                if (arr[j] < arr[min_idx]) {
                    min_idx = j;
                }
            }
            temp = arr[min_idx];
            arr[min_idx] = arr[i];
            arr[i] = temp;
        }
    }
    """,
    # 13. Linear Search on Array
    """
    #include <stdio.h>
    int search(int* arr, int n, int x) {
        int i;
        for (i = 0; i < n; i = i + 1) {
            if (arr[i] == x) {
                return i;
            }
        }
        return -1;
    }
    """,
    # 14. Binary Search (Iterative)
    """
    #include <stdio.h>
    int binary_search(int* arr, int l, int r, int x) {
        int mid;
        while (l <= r) {
            mid = l + (r - l) / 2;
            if (arr[mid] == x) {
                return mid;
            }
            if (arr[mid] < x) {
                l = mid + 1;
            } else {
                r = mid - 1;
            }
        }
        return -1;
    }
    """,
    # 15. Matrix Addition
    """
    #include <stdio.h>
    void add_matrices(int* a, int* b, int* c, int rows, int cols) {
        int i;
        int j;
        int idx;
        for (i = 0; i < rows; i = i + 1) {
            for (j = 0; j < cols; j = j + 1) {
                idx = i * cols + j;
                c[idx] = a[idx] + b[idx];
            }
        }
    }
    """,
    # 16. Celsius to Fahrenheit Converter
    """
    #include <stdio.h>
    float to_fahrenheit(float celsius) {
        return (celsius * 9.0 / 5.0) + 32.0;
    }
    """,
    # 17. Fahrenheit to Celsius Converter
    """
    #include <stdio.h>
    float to_celsius(float fahrenheit) {
        return (fahrenheit - 32.0) * 5.0 / 9.0;
    }
    """,
    # 18. Circle Geometry Area and Circumference
    """
    #include <stdio.h>
    struct Circle {
        float radius;
        float area;
        float circumference;
    };
    void compute_circle(struct Circle* c) {
        c->area = 3.1415 * c->radius * c->radius;
        c->circumference = 2.0 * 3.1415 * c->radius;
    }
    """,
    # 19. Rectangle Area and Perimeter
    """
    #include <stdio.h>
    struct Rectangle {
        int width;
        int height;
        int area;
        int perimeter;
    };
    void compute_rect(struct Rectangle* r) {
        r->area = r->width * r->height;
        r->perimeter = 2 * (r->width + r->height);
    }
    """,
    # 20. Simple Interest Calculator
    """
    #include <stdio.h>
    float simple_interest(float principal, float rate, float time) {
        return (principal * rate * time) / 100.0;
    }
    """,
    # 21. Check Palindrome Number
    """
    #include <stdio.h>
    int is_palindrome(int n) {
        int original = n;
        int reversed = 0;
        int remainder;
        while (n != 0) {
            remainder = n % 10;
            reversed = reversed * 10 + remainder;
            n = n / 10;
        }
        if (original == reversed) {
            return 1;
        }
        return 0;
    }
    """,
    # 22. Sum of Digits of an Integer
    """
    #include <stdio.h>
    int sum_of_digits(int n) {
        int sum = 0;
        while (n != 0) {
            sum += n % 10;
            n = n / 10;
        }
        return sum;
    }
    """,
    # 23. Find Min and Max Element in Array
    """
    #include <stdio.h>
    void find_limits(int* arr, int size, int* min, int* max) {
        int i;
        *min = arr[0];
        *max = arr[0];
        for (i = 1; i < size; i = i + 1) {
            if (arr[i] < *min) {
                *min = arr[i];
            }
            if (arr[i] > *max) {
                *max = arr[i];
            }
        }
    }
    """,
    # 24. Calculate Average of Array Elements
    """
    #include <stdio.h>
    float array_average(int* arr, int size) {
        int i;
        int sum = 0;
        for (i = 0; i < size; i = i + 1) {
            sum += arr[i];
        }
        return sum * 1.0 / size;
    }
    """,
    # 25. Matrix Transpose
    """
    #include <stdio.h>
    void transpose(int* src, int* dst, int r, int c) {
        int i;
        int j;
        for (i = 0; i < r; i = i + 1) {
            for (j = 0; j < c; j = j + 1) {
                dst[j * r + i] = src[i * c + j];
            }
        }
    }
    """,
    # 26. Check Identity Matrix
    """
    #include <stdio.h>
    int is_identity(int* mat, int n) {
        int i;
        int j;
        for (i = 0; i < n; i = i + 1) {
            for (j = 0; j < n; j = j + 1) {
                if (i == j) {
                    if (mat[i * n + j] != 1) {
                        return 0;
                    }
                } else {
                    if (mat[i * n + j] != 0) {
                        return 0;
                    }
                }
            }
        }
        return 1;
    }
    """,
    # 27. Check Symmetric Matrix
    """
    #include <stdio.h>
    int is_symmetric(int* mat, int n) {
        int i;
        int j;
        for (i = 0; i < n; i = i + 1) {
            for (j = 0; j < n; j = j + 1) {
                if (mat[i * n + j] != mat[j * n + i]) {
                    return 0;
                }
            }
        }
        return 1;
    }
    """,
    # 28. Matrix Trace (Sum of Diagonal)
    """
    #include <stdio.h>
    int matrix_trace(int* mat, int n) {
        int i;
        int sum = 0;
        for (i = 0; i < n; i = i + 1) {
            sum += mat[i * n + i];
        }
        return sum;
    }
    """,
    # 29. Celsius to Kelvin Converter
    """
    #include <stdio.h>
    float to_kelvin(float celsius) {
        return celsius + 273.15;
    }
    """,
    # 30. Kelvin to Celsius Converter
    """
    #include <stdio.h>
    float kelvin_to_c(float kelvin) {
        return kelvin - 273.15;
    }
    """,
    # 31. Check Even or Odd (Unary representation)
    """
    #include <stdio.h>
    int is_even(int n) {
        if (n % 2 == 0) {
            return 1;
        }
        return 0;
    }
    """,
    # 32. Multi-Level Pointer Dereference
    """
    #include <stdio.h>
    int main() {
        int x = 100;
        int* p1 = &x;
        int** p2 = &p1;
        int val = **p2;
        printf("Val: %d", val);
        return 0;
    }
    """,
    # 33. Structure coordinates distance calculator
    """
    #include <stdio.h>
    struct Point3D {
        int x;
        int y;
        int z;
    };
    int sum_coords(struct Point3D p) {
        return p.x + p.y + p.z;
    }
    """,
    # 34. Check Perfect Number
    """
    #include <stdio.h>
    int is_perfect(int n) {
        int i;
        int sum = 0;
        for (i = 1; i < n; i = i + 1) {
            if (n % i == 0) {
                sum += i;
            }
        }
        if (sum == n) {
            return 1;
        }
        return 0;
    }
    """,
    # 35. Power Function (Iterative)
    """
    #include <stdio.h>
    int power(int base, int exp) {
        int i;
        int result = 1;
        for (i = 1; i <= exp; i = i + 1) {
            result = result * base;
        }
        return result;
    }
    """,
    # 36. Find Gcd and Lcm together
    """
    #include <stdio.h>
    struct GcdLcm {
        int gcd;
        int lcm;
    };
    void compute_both(int a, int b, struct GcdLcm* res) {
        int temp_a = a;
        int temp_b = b;
        while (temp_a != temp_b) {
            if (temp_a > temp_b) {
                temp_a -= temp_b;
            } else {
                temp_b -= temp_a;
            }
        }
        res->gcd = temp_a;
        res->lcm = (a * b) / temp_a;
    }
    """,
    # 37. Calculate Triangle Area (Heron's approximation)
    """
    #include <stdio.h>
    float semi_perimeter(float a, float b, float c) {
        return (a + b + c) / 2.0;
    }
    """,
    # 38. Cube a Number
    """
    #include <stdio.h>
    int cube(int n) {
        return n * n * n;
    }
    """,
    # 39. Square a Number
    """
    #include <stdio.h>
    int square(int n) {
        return n * n;
    }
    """,
    # 40. Check Positive Negative or Zero
    """
    #include <stdio.h>
    int num_sign(int n) {
        if (n > 0) {
            return 1;
        } else {
            if (n < 0) {
                return -1;
            }
        }
        return 0;
    }
    """,
    # 41. Structure of complex number addition
    """
    #include <stdio.h>
    struct Complex {
        float real;
        float imag;
    };
    struct Complex add_complex(struct Complex c1, struct Complex c2) {
        struct Complex res;
        res.real = c1.real + c2.real;
        res.imag = c1.imag + c2.imag;
        return res;
    }
    """,
    # 42. Structure of Time Difference
    """
    #include <stdio.h>
    struct Time {
        int hours;
        int minutes;
    };
    int to_minutes(struct Time t) {
        return t.hours * 60 + t.minutes;
    }
    """,
    # 43. Simple Calculator (Math operations matcher)
    """
    #include <stdio.h>
    int calculate(int op, int a, int b) {
        if (op == 1) {
            return a + b;
        } else {
            if (op == 2) {
                return a - b;
            } else {
                if (op == 3) {
                    return a * b;
                }
            }
        }
        return 0;
    }
    """,
    # 44. Calculate Arithmetic mean
    """
    #include <stdio.h>
    float mean(float a, float b) {
        return (a + b) / 2.0;
    }
    """,
    # 45. Calculate Harmonic Mean approximation
    """
    #include <stdio.h>
    float harmonic_mean(float a, float b) {
        return (2.0 * a * b) / (a + b);
    }
    """,
    # 46. Factorial using recursion
    """
    #include <stdio.h>
    int r_factorial(int n) {
        if (n <= 1) {
            return 1;
        }
        return n * r_factorial(n - 1);
    }
    """,
    # 47. Fibonacci using recursion
    """
    #include <stdio.h>
    int r_fibonacci(int n) {
        if (n <= 1) {
            return n;
        }
        return r_fibonacci(n - 1) + r_fibonacci(n - 2);
    }
    """,
    # 48. Gcd using recursion
    """
    #include <stdio.h>
    int r_gcd(int a, int b) {
        if (b == 0) {
            return a;
        }
        return r_gcd(b, a % b);
    }
    """,
    # 49. Power using recursion
    """
    #include <stdio.h>
    int r_power(int base, int exp) {
        if (exp == 0) {
            return 1;
        }
        return base * r_power(base, exp - 1);
    }
    """,
    # 50. Sum of natural numbers using recursion
    """
    #include <stdio.h>
    int r_sum(int n) {
        if (n <= 1) {
            return n;
        }
        return n + r_sum(n - 1);
    }
    """,
    # 51. Check if Character is Uppercase
    """
    #include <stdio.h>
    int is_upper(char c) {
        if (c >= 'A' && c <= 'Z') {
            return 1;
        }
        return 0;
    }
    """,
    # 52. Check if Character is Lowercase
    """
    #include <stdio.h>
    int is_lower(char c) {
        if (c >= 'a' && c <= 'z') {
            return 1;
        }
        return 0;
    }
    """,
    # 53. Check if Character is a Digit
    """
    #include <stdio.h>
    int is_digit(char c) {
        if (c >= '0' && c <= '9') {
            return 1;
        }
        return 0;
    }
    """,
    # 54. Convert Celsius to Rankine Temperature Scale
    """
    #include <stdio.h>
    float to_rankine(float celsius) {
        return (celsius + 273.15) * 9.0 / 5.0;
    }
    """,
    # 55. Convert Celsius to Reaumur Temperature Scale
    """
    #include <stdio.h>
    float to_reaumur(float celsius) {
        return celsius * 4.0 / 5.0;
    }
    """,
    # 56. Basic Pointer Increment
    """
    #include <stdio.h>
    void advance_ptr(int** p) {
        *p = *p + 1;
    }
    """,
    # 57. Array index copier using pointers
    """
    #include <stdio.h>
    void copy_array(int* src, int* dst, int n) {
        int i;
        for (i = 0; i < n; i = i + 1) {
            dst[i] = src[i];
        }
    }
    """,
    # 58. Calculate Matrix Scalar Multiplication
    """
    #include <stdio.h>
    void scalar_multiply(int* mat, int size, int k) {
        int i;
        for (i = 0; i < size; i = i + 1) {
            mat[i] = mat[i] * k;
        }
    }
    """,
    # 59. Calculate Matrix Main Diagonal Sum
    """
    #include <stdio.h>
    int diagonal_sum(int* mat, int n) {
        int i;
        int sum = 0;
        for (i = 0; i < n; i = i + 1) {
            sum += mat[i * n + i];
        }
        return sum;
    }
    """,
    # 60. Check Upper Triangular Matrix
    """
    #include <stdio.h>
    int is_upper_triangular(int* mat, int n) {
        int i;
        int j;
        for (i = 0; i < n; i = i + 1) {
            for (j = 0; j < i; j = j + 1) {
                if (mat[i * n + j] != 0) {
                    return 0;
                }
            }
        }
        return 1;
    }
    """,
    # 61. Check Lower Triangular Matrix
    """
    #include <stdio.h>
    int is_lower_triangular(int* mat, int n) {
        int i;
        int j;
        for (i = 0; i < n; i = i + 1) {
            for (j = i + 1; j < n; j = j + 1) {
                if (mat[i * n + j] != 0) {
                    return 0;
                }
            }
        }
        return 1;
    }
    """,
    # 62. Structure representing Employee Profile
    """
    #include <stdio.h>
    struct Employee {
        int id;
        int salary;
        int age;
    };
    int is_senior(struct Employee e) {
        if (e.age > 60) {
            return 1;
        }
        return 0;
    }
    """,
    # 63. Structure representing Book details
    """
    #include <stdio.h>
    struct Book {
        int id;
        int pages;
    };
    int is_thick(struct Book b) {
        if (b.pages > 500) {
            return 1;
        }
        return 0;
    }
    """,
    # 64. Structure representing Bank Account Transactions
    """
    #include <stdio.h>
    struct Account {
        int id;
        int balance;
    };
    void deposit(struct Account* a, int amount) {
        a->balance += amount;
    }
    """,
    # 65. Structure representing Employee Salary Update
    """
    #include <stdio.h>
    struct Emp {
        int id;
        int salary;
    };
    void raise_salary(struct Emp* e, int pct) {
        e->salary = e->salary + (e->salary * pct) / 100;
    }
    """,
    # 66. Series Sum: 1 + 2 + 3 + ... + N
    """
    #include <stdio.h>
    int sum_series_linear(int n) {
        int i;
        int total = 0;
        for (i = 1; i <= n; i = i + 1) {
            total += i;
        }
        return total;
    }
    """,
    # 67. Series Sum: 1^2 + 2^2 + ... + N^2
    """
    #include <stdio.h>
    int sum_squares_series(int n) {
        int i;
        int total = 0;
        for (i = 1; i <= n; i = i + 1) {
            total += i * i;
        }
        return total;
    }
    """,
    # 68. Series Sum: 1^3 + 2^3 + ... + N^3
    """
    #include <stdio.h>
    int sum_cubes_series(int n) {
        int i;
        int total = 0;
        for (i = 1; i <= n; i = i + 1) {
            total += i * i * i;
        }
        return total;
    }
    """,
    # 69. Series Sum of Arithmetic Progression
    """
    #include <stdio.h>
    int ap_series(int start, int diff, int n) {
        int i;
        int total = 0;
        int current = start;
        for (i = 0; i < n; i = i + 1) {
            total += current;
            current += diff;
        }
        return total;
    }
    """,
    # 70. Series Sum of Geometric Progression
    """
    #include <stdio.h>
    int gp_series(int start, int ratio, int n) {
        int i;
        int total = 0;
        int current = start;
        for (i = 0; i < n; i = i + 1) {
            total += current;
            current = current * ratio;
        }
        return total;
    }
    """,
    # 71. Factorial check for large numbers approximation
    """
    #include <stdio.h>
    int approx_fact(int n) {
        int i = 1;
        int total = 1;
        while (i <= n) {
            total = total * i;
            i = i + 1;
        }
        return total;
    }
    """,
    # 72. Count digits of number using division loop
    """
    #include <stdio.h>
    int count_digits(int n) {
        int count = 0;
        while (n != 0) {
            n = n / 10;
            count = count + 1;
        }
        return count;
    }
    """,
    # 73. Print Alternate elements from array using C89-style for
    """
    #include <stdio.h>
    void print_alternate(int* arr, int n) {
        int i;
        for (i = 0; i < n; i = i + 2) {
            printf("%d ", arr[i]);
        }
    }
    """,
    # 74. Sum Alternate elements of array
    """
    #include <stdio.h>
    int sum_alternate(int* arr, int n) {
        int i;
        int total = 0;
        for (i = 0; i < n; i = i + 2) {
            total += arr[i];
        }
        return total;
    }
    """,
    # 75. Product of array elements using loop
    """
    #include <stdio.h>
    int array_product(int* arr, int n) {
        int i;
        int total = 1;
        for (i = 0; i < n; i = i + 1) {
            total = total * arr[i];
        }
        return total;
    }
    """,
    # 76. Linear Search returning index position
    """
    #include <stdio.h>
    int find_index(int* arr, int n, int val) {
        int i;
        for (i = 0; i < n; i = i + 1) {
            if (arr[i] == val) {
                return i;
            }
        }
        return -1;
    }
    """,
    # 77. Check if Array is sorted
    """
    #include <stdio.h>
    int is_array_sorted(int* arr, int n) {
        int i;
        for (i = 0; i < n - 1; i = i + 1) {
            if (arr[i] > arr[i + 1]) {
                return 0;
            }
        }
        return 1;
    }
    """,
    # 78. Absolute value of a float number
    """
    #include <stdio.h>
    float float_abs(float x) {
        if (x < 0.0) {
            return -x;
        }
        return x;
    }
    """,
    # 79. Maximum of two integers
    """
    #include <stdio.h>
    int max_int(int a, int b) {
        if (a > b) {
            return a;
        }
        return b;
    }
    """,
    # 80. Minimum of two integers
    """
    #include <stdio.h>
    int min_int(int a, int b) {
        if (a < b) {
            return a;
        }
        return b;
    }
    """,
    # 81. Check if number is inside range [min, max]
    """
    #include <stdio.h>
    int is_in_range(int val, int min, int max) {
        if (val >= min && val <= max) {
            return 1;
        }
        return 0;
    }
    """,
    # 82. Calculate Triangle Area using base and height
    """
    #include <stdio.h>
    float triangle_area(float b, float h) {
        return 0.5 * b * h;
    }
    """,
    # 83. Calculate Cylinder Volume
    """
    #include <stdio.h>
    float cylinder_volume(float r, float h) {
        return 3.1415 * r * r * h;
    }
    """,
    # 84. Calculate Sphere Volume
    """
    #include <stdio.h>
    float sphere_volume(float r) {
        return (4.0 / 3.0) * 3.1415 * r * r * r;
    }
    """,
    # 85. Calculate Cone Volume
    """
    #include <stdio.h>
    float cone_volume(float r, float h) {
        return (1.0 / 3.0) * 3.1415 * r * r * h;
    }
    """,
    # 86. Calculate Torus Volume approximation
    """
    #include <stdio.h>
    float torus_volume(float r, float r_major) {
        return 2.0 * 3.1415 * 3.1415 * r * r * r_major;
    }
    """,
    # 87. Linear search for occurrences count
    """
    #include <stdio.h>
    int count_occurrences(int* arr, int n, int val) {
        int i;
        int total = 0;
        for (i = 0; i < n; i = i + 1) {
            if (arr[i] == val) {
                total = total + 1;
            }
        }
        return total;
    }
    """,
    # 88. Count even elements in array
    """
    #include <stdio.h>
    int count_even(int* arr, int n) {
        int i;
        int total = 0;
        for (i = 0; i < n; i = i + 1) {
            if (arr[i] % 2 == 0) {
                total = total + 1;
            }
        }
        return total;
    }
    """,
    # 89. Count odd elements in array
    """
    #include <stdio.h>
    int count_odd(int* arr, int n) {
        int i;
        int total = 0;
        for (i = 0; i < n; i = i + 1) {
            if (arr[i] % 2 != 0) {
                total = total + 1;
            }
        }
        return total;
    }
    """,
    # 90. Copy one array to another using pointers
    """
    #include <stdio.h>
    void array_copy_ptr(int* src, int* dst, int n) {
        int i;
        for (i = 0; i < n; i = i + 1) {
            *(dst + i) = *(src + i);
        }
    }
    """,
    # 91. Scalar product of two arrays (dot product)
    """
    #include <stdio.h>
    int dot_product(int* a, int* b, int n) {
        int i;
        int total = 0;
        for (i = 0; i < n; i = i + 1) {
            total += a[i] * b[i];
        }
        return total;
    }
    """,
    # 92. Check if a number is negative
    """
    #include <stdio.h>
    int is_negative(int n) {
        if (n < 0) {
            return 1;
        }
        return 0;
    }
    """,
    # 93. Check if a number is positive
    """
    #include <stdio.h>
    int is_positive(int n) {
        if (n > 0) {
            return 1;
        }
        return 0;
    }
    """,
    # 94. Simple structures representing a Line
    """
    #include <stdio.h>
    struct Line {
        int x1;
        int y1;
        int x2;
        int y2;
    };
    int is_horizontal(struct Line l) {
        if (l.y1 == l.y2) {
            return 1;
        }
        return 0;
    }
    """,
    # 95. Struct representing vertical line check
    """
    #include <stdio.h>
    struct L {
        int x1;
        int y1;
        int x2;
        int y2;
    };
    int is_vertical(struct L l) {
        if (l.x1 == l.x2) {
            return 1;
        }
        return 0;
    }
    """,
    # 96. Arithmetic Mean of floats
    """
    #include <stdio.h>
    float float_mean(float a, float b) {
        return (a + b) / 2.0;
    }
    """,
    # 97. Geometric Mean of floats approximation
    """
    #include <stdio.h>
    float float_geo_mean(float a, float b) {
        return a * b;
    }
    """,
    # 98. Check if two floats are equal approximation
    """
    #include <stdio.h>
    int floats_equal(float a, float b) {
        float diff = a - b;
        if (diff < 0.001) {
            return 1;
        }
        return 0;
    }
    """,
    # 99. Swap floats using pointers
    """
    #include <stdio.h>
    void swap_floats(float* a, float* b) {
        float temp = *a;
        *a = *b;
        *b = temp;
    }
    """,
    # 100. Infinite while loop representation
    """
    #include <stdio.h>
    void infinite_loop() {
        while (1) {
            printf("Running");
        }
    }
    """
]

@pytest.mark.parametrize("source", REAL_C_PROGRAMS)
def test_real_c_subset_programs(source):
    """Verify that 100 real-world, multi-line, standard C-Subset programs parse successfully."""
    lexer = Lexer(source)
    tokens = lexer.tokenize(keep_comments=False)
    parser = Parser(tokens)
    program = parser.parse()
    
    # Ensuring no lexical or syntax errors are registered
    assert len(parser.errors) == 0, f"Parser error on real C code:\n{source}\nErrors: {parser.errors}"
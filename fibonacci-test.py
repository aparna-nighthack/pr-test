def fibonacci(n):
    """Generate Fibonacci series up to n terms"""
    a, b = 0, 1
    for _ in range(n):
        print(a, end=" ")
        a, b = b, a + b

# Get input from user
terms = int(input("Enter the number of terms: "))
fibonacci(terms)

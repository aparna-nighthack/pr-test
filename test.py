def fibonacci(n):
    """Return a list of the first n Fibonacci numbers."""
    if n <= 0:
        return []
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence

if __name__ == "__main__":
    # Get input from user and print the resulting list
    terms = int(input("Enter the number of terms: "))
    print(fibonacci(terms))

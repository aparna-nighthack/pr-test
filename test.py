def fibonacci(n):
    """Return a list of the first n Fibonacci numbers.

    Parameters:
        n (int): Number of terms to generate. Must be a non-negative integer.

    Returns:
        list[int]: Fibonacci sequence with length ``n`` (or empty list if ``n == 0``).

    Raises:
        TypeError: If ``n`` is not an integer.
        ValueError: If ``n`` is negative.
    """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0:
        return []
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence

if __name__ == "__main__":
    # Get input from user and print the resulting list, with robust error handling
    import sys

    try:
        raw = input("Enter the number of terms: ")
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.", file=sys.stderr)
        sys.exit(1)

    try:
        terms = int(raw)
    except ValueError:
        print("Please enter a valid integer.", file=sys.stderr)
        sys.exit(2)

    if terms < 0:
        print("Number of terms must be non-negative.", file=sys.stderr)
        sys.exit(3)

    try:
        print(fibonacci(terms))
    except Exception as exc:
        # Catch any unexpected errors from fibonacci and report clearly
        print(f"Error computing fibonacci: {exc}", file=sys.stderr)
        sys.exit(4)

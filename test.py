from __future__ import annotations

import os
import sys
import argparse
from typing import List, Optional


def fibonacci(n: int) -> List[int]:
    """Return a list of the first n Fibonacci numbers.

    Parameters:
        n (int): Number of terms to generate. Must be a non-negative integer.

    Returns:
        list[int]: Fibonacci sequence with length ``n`` (or empty list if ``n == 0``).

    Raises:
        TypeError: If ``n`` is not an integer (bool is not allowed).
        ValueError: If ``n`` is negative or exceeds the safety limit.
        MemoryError: If the system cannot allocate memory for the sequence.
    """
    if isinstance(n, bool):
        raise TypeError("n must be an integer, not bool")
    if not isinstance(n, int):
        raise TypeError("n must be an integer")
    if n < 0:
        raise ValueError("n must be non-negative")

    # Prevent pathological inputs that could exhaust memory or time.
    # Determine the maximum number of terms permitted, with robust validation.
    try:
        raw_max = os.getenv("FIBONACCI_MAX_TERMS", "100000")
        max_terms = int(raw_max)
    except (TypeError, ValueError):
        # If the environment variable is missing or malformed, fall back to a safe default.
        max_terms = 100000
    # Ensure the limit is a sensible, positive integer. If not, reset to default.
    if max_terms <= 0:
        max_terms = 100000
    # Apply a hard upper bound to avoid accidental runaway settings.
    if max_terms > 5_000_000:
        max_terms = 5_000_000
    if n > max_terms:
        raise ValueError(
            f"n must not exceed {max_terms} (set FIBONACCI_MAX_TERMS to override)"
        )

    if n == 0:
        return []
    sequence: List[int] = []
    a, b = 0, 1
    try:
        for _ in range(n):
            sequence.append(a)
            a, b = b, a + b
    except MemoryError as mem_err:
        # Re-raise with a clearer message for callers.
        raise MemoryError(
            "Insufficient memory to generate the requested Fibonacci sequence"
        ) from mem_err
    return sequence


if __name__ == "__main__":
    # Parse CLI arguments with argparse for robust validation and usage help.
    parser = argparse.ArgumentParser(
        description="Generate the first N Fibonacci numbers.",
    )
    parser.add_argument(
        "n",
        nargs="?",
        type=int,
        help="Number of terms to generate (non-negative integer)",
    )
    parser.add_argument(
        "--max-terms",
        dest="max_terms",
        type=int,
        default=None,
        help=(
            "Override maximum allowed terms (default comes from FIBONACCI_MAX_TERMS env, "
            "capped to 5,000,000)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce non-essential output (affects only prompts).",
    )

    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse already printed the appropriate message; propagate exit code
        raise

    # If --max-terms is provided, set the environment variable used by fibonacci()
    if args.max_terms is not None:
        if not isinstance(args.max_terms, int) or args.max_terms <= 0:
            print("--max-terms must be a positive integer", file=sys.stderr)
            sys.exit(2)
        # Apply the same hard cap to keep behavior predictable.
        capped = min(args.max_terms, 5_000_000)
        os.environ["FIBONACCI_MAX_TERMS"] = str(capped)

    # Acquire N from positional arg or from interactive prompt.
    raw: Optional[str] = None
    if args.n is not None:
        raw = str(args.n)
    else:
        try:
            prompt = "Enter the number of terms: " if not args.quiet else ""
            raw = input(prompt)
        except EOFError:
            print("\nNo input provided.", file=sys.stderr)
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nInput cancelled.", file=sys.stderr)
            sys.exit(130)

    try:
        terms = int(raw) if raw is not None else 0
    except (TypeError, ValueError):
        print("Please enter a valid integer.", file=sys.stderr)
        sys.exit(2)

    try:
        result = fibonacci(terms)
    except (TypeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(3)
    except MemoryError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(5)
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:  # Fallback for unexpected errors
        print(f"Error computing fibonacci: {exc}", file=sys.stderr)
        sys.exit(4)

    try:
        print(result)
    except BrokenPipeError:
        # Handle cases like piping to `head` where the reader closes early.
        try:
            sys.stdout.close()
        finally:
            sys.exit(0)

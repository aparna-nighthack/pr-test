# pr-test

Simple Fibonacci CLI with robust error handling.

Usage
- Generate terms: `python3 test.py 10`
- Interactive prompt: `python3 test.py` then enter a number.
- Cap terms: `python3 test.py 100 --max-terms 200`
- Environment cap: set `FIBONACCI_MAX_TERMS` (default 100000, hard-capped at 5,000,000).

Exit codes
- 0: Success
- 1: No input provided (EOF)
- 2: Invalid argument (`n` or `--max-terms`)
- 3: Validation error (e.g., exceeds max terms)
- 4: Unexpected error
- 5: Memory error
- 130: Cancelled (Ctrl-C)

from __future__ import annotations

import os
import sys
import argparse
import signal
from typing import List, Optional

# Exit code constants for clarity and consistency
EXIT_OK = 0
EXIT_NOINPUT = 1
EXIT_USAGE = 2
EXIT_INVALID = 3
EXIT_UNKNOWN = 4
EXIT_MEMORY = 5
EXIT_CANCELLED = 130

# Shared limits and parsing guards
MAX_TERMS_DEFAULT = 100_000
MAX_TERMS_CAP = 5_000_000
# Guard against absurdly long numeric inputs that can be expensive to parse
MAX_INPUT_DIGITS = 12  # up to 999,999,999,999


def _parse_max_terms_env(env_key: str = "FIBONACCI_MAX_TERMS") -> int:
    """Safely parse the maximum allowed terms from an environment variable.

    - Ignores malformed values and falls back to a safe default.
    - Applies a hard upper bound to avoid runaway settings.
    - Defends against extremely long strings that could be expensive to parse.
    """
    raw = None
    try:
        raw = os.getenv(env_key, str(MAX_TERMS_DEFAULT))
    except Exception:
        # Very defensive: if environment access fails, fall back to default
        return MAX_TERMS_DEFAULT
    try:
        if raw is None:
            return MAX_TERMS_DEFAULT
        # Trim whitespace and allow underscores for readability (e.g., "1_000_000").
        cleaned = raw.strip().replace("_", "")
        # Defend against pathological sizes (e.g., millions of digits).
        # If the string is too long to be sane, treat as malformed and use default.
        if len(cleaned) > MAX_INPUT_DIGITS:
            return MAX_TERMS_DEFAULT
        max_terms = int(cleaned)
    except (TypeError, ValueError):
        return MAX_TERMS_DEFAULT
    if max_terms <= 0:
        max_terms = MAX_TERMS_DEFAULT
    if max_terms > MAX_TERMS_CAP:
        max_terms = MAX_TERMS_CAP
    return max_terms


def fibonacci(n: int) -> List[inti]:
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

    # Determine and validate the maximum number of terms permitted.
    max_terms = _parse_max_terms_env()
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
    # Be a good Unix CLI citizen: avoid BrokenPipe tracebacks.
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except Exception:
        # Not all platforms support SIGPIPE; ignore if unavailable.
        pass

    # Custom ArgumentParser to standardize exit codes on usage errors.
    class SafeArgumentParser(argparse.ArgumentParser):
        def error(self, message):  # type: ignore[override]
            try:
                sys.stderr.write(f"error: {message}\n")
                self.print_help(sys.stderr)
            except Exception:
                # If stderr is unavailable, fall back silently to exit code
                pass
            raise SystemExit(EXIT_USAGE)

        def exit(self, status=0, message=None):  # type: ignore[override]
            if message:
                try:
                    sys.stderr.write(message)
                except Exception:
                    # If writing to stderr fails (e.g., broken pipe), continue to exit
                    pass
            # Normalize argparse's default 2 to our EXIT_USAGE for consistency.
            norm = EXIT_USAGE if status == 2 else status
            raise SystemExit(norm)

    # Parse CLI arguments with argparse for robust validation and usage help.
    parser = SafeArgumentParser(
        description="Generate the first N Fibonacci numbers.",
    )
    def _non_negative_int(value: str) -> int:
        # Allow underscores and surrounding whitespace for readability
        cleaned = value.strip().replace("_", "")
        if len(cleaned) > MAX_INPUT_DIGITS:
            raise argparse.ArgumentTypeError(
                f"value has too many digits (>{MAX_INPUT_DIGITS})"
            )
        try:
            n = int(cleaned)
        except (TypeError, ValueError):
            raise argparse.ArgumentTypeError("must be an integer")
        if isinstance(n, bool):
            # Prevent True/False from being treated as 1/0
            raise argparse.ArgumentTypeError("must be an integer, not bool")
        if n < 0:
            raise argparse.ArgumentTypeError("must be non-negative")
        return n

    def _positive_int(value: str) -> int:
        n = _non_negative_int(value)
        if n == 0:
            raise argparse.ArgumentTypeError("must be a positive integer")
        return n
    parser.add_argument(
        "n",
        nargs="?",
        type=_non_negative_int,
        help="Number of terms to generate (non-negative integer)",
    )
    parser.add_argument(
        "--max-terms",
        dest="max_terms",
        type=_positive_int,
        default=None,
        help=(
            "Override maximum allowed terms (default comes from FIBONACCI_MAX_TERMS env, "
            f"capped to {MAX_TERMS_CAP:,})."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce non-essential output (affects only prompts).",
    )

    try:
        args = parser.parse_args()
    except KeyboardInterrupt:
        try:
            sys.stderr.write("\nParsing cancelled.\n")
        except Exception:
            pass
        sys.exit(EXIT_CANCELLED)
    except MemoryError:
        try:
            sys.stderr.write("Out of memory while parsing arguments.\n")
        except Exception:
            pass
        sys.exit(EXIT_MEMORY)
    except SystemExit:
        # Already normalized in SafeArgumentParser.exit/error; just propagate
        raise
    except Exception as exc:
        try:
            sys.stderr.write(f"Unexpected error while parsing args: {exc}\n")
        except Exception:
            pass
        sys.exit(EXIT_UNKNOWN)

    # If --max-terms is provided, set the environment variable used by fibonacci()
    if args.max_terms is not None:
        # Apply the same hard cap to keep behavior predictable.
        capped = min(args.max_terms, MAX_TERMS_CAP)
        if args.max_terms > MAX_TERMS_CAP:
            try:
                print(
                    (
                        f"Warning: --max-terms capped to {MAX_TERMS_CAP:,} "
                        f"(requested {args.max_terms:,})."
                    ),
                    file=sys.stderr,
                )
            except Exception:
                # Ignore warning output failures; proceed with capped value
                pass
        try:
            os.environ["FIBONACCI_MAX_TERMS"] = str(capped)
        except Exception as env_err:
            try:
                print(f"Failed to set environment variable: {env_err}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_UNKNOWN)

    # Acquire N from positional arg or from interactive prompt.
    raw: Optional[str] = None
    if args.n is not None:
        raw = str(args.n)
    else:
        try:
            prompt = "Enter the number of terms: " if not args.quiet else ""
            raw = input(prompt)
        except EOFError:
            try:
                print("\nNo input provided.", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_NOINPUT)
        except KeyboardInterrupt:
            try:
                print("\nInput cancelled.", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_CANCELLED)
        except OSError as io_err:
            try:
                print(f"\nInput error: {io_err}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_UNKNOWN)
        except UnicodeEncodeError as enc_err:
            try:
                print(f"\nEncoding error while prompting for input: {enc_err}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_UNKNOWN)
        except Exception as exc:
            try:
                print(f"\nUnexpected input error: {exc}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_UNKNOWN)

    def _parse_terms_from_string_allow_empty(value: Optional[str]) -> int:
        """Parse user-entered term count with consistent validation.

        Accepts empty/whitespace as 0, otherwise enforces digit and length guards.
        Raises ValueError with user-friendly messages on invalid input.
        """
        cleaned = (value or "").strip().replace("_", "")
        if cleaned == "":
            return 0
        if len(cleaned) > MAX_INPUT_DIGITS:
            raise ValueError(
                f"Input has too many digits (>{MAX_INPUT_DIGITS}); refusing to parse"
            )
        try:
            n = int(cleaned)
        except (TypeError, ValueError):
            raise ValueError("Please enter a valid integer.")
        if isinstance(n, bool):
            raise ValueError("Please enter an integer, not a boolean value.")
        if n < 0:
            raise ValueError("Please enter a non-negative integer.")
        return n

    try:
        terms = _parse_terms_from_string_allow_empty(raw)
    except ValueError as exc:
        try:
            print(str(exc), file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_USAGE)

    try:
        result = fibonacci(terms)
    except (TypeError, ValueError) as exc:
        try:
            print(str(exc), file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_INVALID)
    except MemoryError as exc:
        try:
            print(str(exc), file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_MEMORY)
    except KeyboardInterrupt:
        try:
            print("\nOperation cancelled.", file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_CANCELLED)
    except Exception as exc:  # Fallback for unexpected errors
        try:
            print(f"Error computing fibonacci: {exc}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_UNKNOWN)

    # Print with robust handling of common IO failures.
    try:
        print(result)
        try:
            sys.stdout.flush()
        except BrokenPipeError:
            try:
                sys.stdout.close()
            finally:
                sys.exit(EXIT_OK)
        except (OSError, IOError) as io_err:
            try:
                print(f"Output flush error: {io_err}", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_UNKNOWN)
        except MemoryError:
            try:
                print("Insufficient memory while finalizing output.", file=sys.stderr)
            except Exception:
                pass
            sys.exit(EXIT_MEMORY)
    except BrokenPipeError:
        # Handle cases like piping to `head` where the reader closes early.
        try:
            sys.stdout.close()
        finally:
            sys.exit(EXIT_OK)
    except UnicodeEncodeError as enc_err:
        try:
            print(f"Encoding error while writing output: {enc_err}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_UNKNOWN)
    except (OSError, IOError) as io_err:
        # Generic output error (e.g., bad file descriptor)
        try:
            print(f"Output error: {io_err}", file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_UNKNOWN)
    except MemoryError:
        try:
            print("Insufficient memory to print the result.", file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_MEMORY)
    except KeyboardInterrupt:
        try:
            print("\nOutput cancelled.", file=sys.stderr)
        except Exception:
            pass
        sys.exit(EXIT_CANCELLED)

"""
Command-line entry points for spheroidkit.

Installing the package registers `spheroidkit-serve` (see pyproject.toml
[project.scripts]). This launches the web application without the user needing
to remember the uvicorn command. Requires the [web] extra:

    pip install spheroidkit[web]
    spheroidkit-serve                  # serves on http://127.0.0.1:8000
    spheroidkit-serve --port 9000      # custom port
    spheroidkit-serve --host 0.0.0.0   # expose on the network / for containers
"""
import argparse
import sys


def serve(argv=None):
    """Launch the spheroidkit web application."""
    parser = argparse.ArgumentParser(
        prog="spheroidkit-serve",
        description="Launch the spheroidkit web application.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address (use 0.0.0.0 to expose on the network).")
    parser.add_argument("--port", type=int, default=8000, help="Port (default 8000).")
    parser.add_argument("--reload", action="store_true",
                        help="Auto-reload on code changes (development only).")
    args = parser.parse_args(argv)

    try:
        import uvicorn  # noqa: F401
    except ImportError:
        sys.exit("The web server needs the [web] extra:\n"
                 "    pip install spheroidkit[web]")

    print(f"Starting spheroidkit on http://{args.host}:{args.port}")
    uvicorn.run("spheroidkit.web.app:app", host=args.host,
                port=args.port, reload=args.reload)


if __name__ == "__main__":
    serve()

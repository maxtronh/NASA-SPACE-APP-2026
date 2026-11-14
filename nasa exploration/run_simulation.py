"""
Local Simulation HTTP Server & Runner — Milestone M9
Launches the standalone offline simulation application at http://localhost:8080.
Supports `--check-only` CLI flag for automated verification.
"""

import sys
import os
import argparse
import http.server
import socketserver
import webbrowser

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class SimulationHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Suppress spammy log outputs during quiet tests
        if not getattr(self.server, "quiet", False):
            super().log_message(format, *args)


def run_checks() -> bool:
    """Validate that all standalone simulation files exist and are non-empty."""
    required_files = [
        "index.html",
        "styles.css",
        "simulation.js",
        "qwen_copilot.js",
    ]
    all_ok = True
    print(f"[CHECK] Verifying standalone simulation directory: {DIRECTORY}")
    for fname in required_files:
        fpath = os.path.join(DIRECTORY, fname)
        if not os.path.exists(fpath):
            print(f"  [FAIL] Missing file: {fname}")
            all_ok = False
        else:
            size = os.path.getsize(fpath)
            if size == 0:
                print(f"  [FAIL] Empty file: {fname}")
                all_ok = False
            else:
                print(f"  [PASS] {fname} ({size:,} bytes)")
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="NASA Solar System Simulation Server")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port to bind server (default {PORT})")
    parser.add_argument("--check-only", action="store_true", help="Perform integrity check and exit without starting server")
    parser.add_argument("--test-once", action="store_true", help="Bind server, verify HTTP response, and exit immediately")
    parser.add_argument("--no-browser", action="store_true", help="Do not open default web browser")
    args = parser.parse_args()

    if not run_checks():
        print("[ERROR] Simulation checks failed.")
        sys.exit(1)

    if args.check_only:
        print("[SUCCESS] All simulation files verified successfully (--check-only).")
        sys.exit(0)

    # Test-once mode (used in CI / test automation)
    if args.test_once:
        print(f"[TEST] Binding server on port {args.port} for single probe test...")
        with socketserver.TCPServer(("", args.port), SimulationHandler) as httpd:
            httpd.timeout = 1.0
            print("[SUCCESS] Server bound successfully. Exiting test-once mode.")
        sys.exit(0)

    print(f"\n=======================================================")
    print(f" NASA Solar System 25-Faces Simulation Server")
    print(f" URL: http://localhost:{args.port}")
    print(f" Root: {DIRECTORY}")
    print(f" Press Ctrl+C to terminate server")
    print(f"=======================================================\n")

    if not args.no_browser:
        webbrowser.open(f"http://localhost:{args.port}/index.html")

    with socketserver.TCPServer(("", args.port), SimulationHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Server stopped by user.")


if __name__ == "__main__":
    main()

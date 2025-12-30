"""Shared CLI utilities for image manager commands."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class Command:
    """A CLI subcommand."""
    name: str
    help: str
    handler: Callable[[], int]


@dataclass
class Option:
    """A CLI option."""
    name: str
    help: str
    takes_value: bool = True


class CLI:
    """Simple CLI framework for consistent command structure."""

    def __init__(
        self,
        name: str,
        description: str,
        daemon_name: str,
        daemon_addr_fn: Callable[[], str],
        is_running_fn: Callable[[], bool],
        start_fn: Callable[[], int],
        stop_fn: Callable[[], int],
    ):
        self.name = name
        self.description = description
        self.daemon_name = daemon_name
        self.daemon_addr_fn = daemon_addr_fn
        self.is_running_fn = is_running_fn
        self.start_fn = start_fn
        self.stop_fn = stop_fn
        self.options: list[Option] = []
        self.examples: list[str] = []

    def add_option(self, name: str, help: str, takes_value: bool = True) -> "CLI":
        """Add an option to the CLI."""
        self.options.append(Option(name, help, takes_value))
        return self

    def add_example(self, example: str) -> "CLI":
        """Add an example to the CLI."""
        self.examples.append(example)
        return self

    def print_usage(self) -> None:
        """Print usage information."""
        print(f"Usage: {self.name} <command|image:tag> [options]", file=sys.stderr)
        print()
        print(self.description)
        print()
        print("Commands:")
        print(f"  start             Start {self.daemon_name}")
        print(f"  stop              Stop {self.daemon_name}")
        print(f"  status            Check if {self.daemon_name} is running")
        print()
        if self.options:
            print("Options:")
            for opt in self.options:
                if opt.takes_value:
                    print(f"  --{opt.name} <value>  {opt.help}")
                else:
                    print(f"  --{opt.name}          {opt.help}")
            print()
        if self.examples:
            print("Examples:")
            for ex in self.examples:
                print(f"  {self.name} {ex}")

    def parse_args(self) -> tuple[str | None, dict[str, str | bool]]:
        """Parse command line arguments.

        Returns:
            Tuple of (image_ref or None for subcommands, options dict)
        """
        if len(sys.argv) < 2:
            self.print_usage()
            sys.exit(1)

        command = sys.argv[1]

        # Handle subcommands
        if command == "start":
            sys.exit(self.start_fn())
        elif command == "stop":
            sys.exit(self.stop_fn())
        elif command == "status":
            if self.is_running_fn():
                addr = self.daemon_addr_fn()
                print(f"{self.daemon_name} is running (addr: {addr})")
                sys.exit(0)
            else:
                print(f"{self.daemon_name} is not running")
                sys.exit(1)
        elif command in ("--help", "-h"):
            self.print_usage()
            sys.exit(0)

        # Parse options
        image_ref = command
        opts: dict[str, str | bool] = {}

        args = sys.argv[2:]
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                opt_name = arg[2:]
                opt = next((o for o in self.options if o.name == opt_name), None)
                if opt is None:
                    print(f"Unknown option: {arg}", file=sys.stderr)
                    sys.exit(1)
                if opt.takes_value:
                    if i + 1 >= len(args):
                        print(f"Option --{opt_name} requires a value", file=sys.stderr)
                        sys.exit(1)
                    opts[opt_name] = args[i + 1]
                    i += 2
                else:
                    opts[opt_name] = True
                    i += 1
            else:
                print(f"Unknown argument: {arg}", file=sys.stderr)
                sys.exit(1)

        return image_ref, opts

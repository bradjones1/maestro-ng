# Copyright (C) 2013 SignalFuse, Inc.
#
# Docker container orchestration utility.

import datetime
import threading
import sys


def color(cond):
    """Returns 32 (green) or 31 (red) depending on the validity of the given
    condition."""
    return cond and 32 or 31


def green(s):
    return '\033[32;1m{}\033[;0m'.format(s)


def blue(s):
    return '\033[36;m{}\033[;0m'.format(s)


def red(s):
    return '\033[31;1m{}\033[;0m'.format(s)


def _default_printer(s):
    sys.stdout.write(s)
    sys.stdout.write('\033[K\r')
    sys.stdout.flush()


def time_ago(t, base=None):
    """Return a string representing the time delta between now and the given
    datetime object.

    Args:
        t (datetime.datetime): A UTC timestamp as a datetime object.
        base (datetime.datetime): If not None, the time to calculate the delta
            against.
    """
    delta = int(((base or datetime.datetime.utcnow()) - t).total_seconds())
    if delta < 0:
        return None
    if delta < 60:
        return '{}s'.format(delta)
    if delta < 3600:
        return '{}m'.format(delta/60)
    if delta < 86400:
        return '{}d'.format(delta/60/60)

    # Biggest step is by month.
    return '{}mo'.format(delta/60/60/24)


class OutputManager:
    """Multi-line concurrently updated output.

    Manages a multi-line, position-indexed output that is concurrently updated
    by multiple threads. The total number of expected lines must be known in
    advance so that terminal space can be provisioned.

    Output is automatically synchronized between the threads, each individual
    thread operating using an OutputFormatter that targets a specific,
    positioned line on the output block.
    """

    def __init__(self, lines):
        self._lines = lines
        self._formatters = {}
        self._lock = threading.Lock()

    def start(self):
        self._print('{}\033[{}A'.format('\n' * self._lines, self._lines))

    def get_formatter(self, pos, prefix=None):
        f = OutputFormatter(lambda s: self._print(s, pos), prefix=prefix)
        self._formatters[pos] = f
        return f

    def end(self):
        self._print('\033[{}B'.format(self._lines))

    def _print(self, s, pos=None):
        with self._lock:
            if pos:
                sys.stdout.write('\033[{}B'.format(pos))
            sys.stdout.write('\r{}\033[K\r'.format(s))
            if pos:
                sys.stdout.write('\033[{}A'.format(pos))
            sys.stdout.flush()


class OutputFormatter:
    """Output formatter for nice, progressive terminal output.

    Manages the output of a progressively updated terminal line, with "in
    progress" labels and a "committed" base label.
    """

    def __init__(self, printer=_default_printer, prefix=None):
        self._printer = printer
        self._prefix = prefix
        self._committed = prefix

    def commit(self, s=None):
        """Output, and commit, a string at the end of the currently committed
        line."""
        if self._committed and s:
            self._committed = '{} {}'.format(self._committed, s)
        elif not self._committed and s:
            self._committed = s
        self._printer(self._committed)

    def pending(self, s):
        """Output a temporary message at the end of the currently committed
        line."""
        if self._committed and s:
            self._printer('{} {}'.format(self._committed, s))
        if not self._committed and s:
            self._printer(s)

    def reset(self):
        """Reset the line to its base, saved prefix."""
        self._committed = self._prefix
        self.commit()

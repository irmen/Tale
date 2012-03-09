# exceptions


class SecurityViolation(Exception):
    """Some security constraint was violated"""
    pass


class ParseError(Exception):
    """Problem with parsing the user input. Should be shown to the user as a nice error message."""
    pass

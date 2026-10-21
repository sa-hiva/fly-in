class ParseError(Exception):
    def __init__(self, line: int, message: str) -> None:
        self.line = line
        self.message = message
        super().__init__(f"Line {line}: Error: {message}")


class ZoneNotInConnectionError(Exception):
    def __init__(self, zone: str, endpoints: frozenset[str]) -> None:
        self.zone = zone
        self.endpoints = endpoints
        super().__init__(f"Invalid zone {zone} provided for "
                         f"connection {'-'.join(endpoints)}")

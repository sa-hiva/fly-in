from model import Zone, ZoneCategory, ZoneType, Connection, ParseError
from pydantic import ValidationError
from typing import cast


class Parser:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.nb_drones: int | None = None
        self.start_hub_line: int | None = None
        self.end_hub_line: int | None = None
        self.zones: list[Zone] = []
        self.connections: list[Connection] = []
        self.zone_names: dict[str, int] = {}
        self.zone_coordinates: set[tuple[int, int]] = set()
        self.connection_pairs: set[frozenset[str]] = set()

    def parse(self) -> tuple[int, list[Zone], list[Connection]]:
        try:
            with open(self.file_path, "r") as file:
                for line_number, raw_line in enumerate(file, start=1):
                    self._parse_line(line_number, raw_line.strip())
        except FileNotFoundError as error:
            raise ParseError(0, "Configuration file "
                             f"'{self.file_path}' not found")from error
        except PermissionError as error:
            raise ParseError(0, "Permission denied "
                             f"reading '{self.file_path}'") from error

        if self.nb_drones is None:
            raise ParseError(0, "nb_drones was never defined")
        if self.start_hub_line is None:
            raise ParseError(0, "there is no start_hub defined")
        if self.end_hub_line is None:
            raise ParseError(0, "there is no end_hub defined")

        return self.nb_drones, self.zones, self.connections

    def _parse_line(self, line_number: int, line: str) -> None:
        if not line or line.startswith("#"):
            return

        if ":" not in line:
            raise ParseError(line_number,
                             "invalid format. Must be 'key: values'")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key == "nb_drones":
            self._parse_nb_drones(line_number, value)
            return

        if self.nb_drones is None:
            raise ParseError(line_number,
                             "nb_drones must be defined "
                             "before any zone or connection")

        if key in ("start_hub", "end_hub", "hub"):
            self._parse_zone(line_number, key, value)
        elif key == "connection":
            self._parse_connection(line_number, value)
        else:
            raise ParseError(line_number, f"Invalid key '{key}'")

    def _parse_nb_drones(self, line_number: int, value: str) -> None:
        if self.nb_drones is not None:
            raise ParseError(line_number, "nb_drones already defined")
        try:
            n = int(value)
        except ValueError:
            raise ParseError(line_number,
                             "nb_drones must be an integer") from None
        if n <= 0:
            raise ParseError(line_number,
                             "nb_drones must be a positive integer")
        self.nb_drones = n

    def _parse_zone(self, line_number: int, key: str, value: str) -> None:
        if "[" in value:
            main_part, metadata_part = value.split("[", 1)
            metadata_part = metadata_part.rstrip("]")
        else:
            main_part = value
            metadata_part = ""

        arguments = main_part.strip().split()

        if len(arguments) < 3:
            raise ParseError(line_number, "at least 3 arguments "
                             "are required: <name> <x> <y>")

        name = arguments[0]
        if "-" in name:
            raise ParseError(line_number, f"zone name '{name}' "
                             "cannot contain dashes or spaces")
        if name in self.zone_names:
            raise ParseError(line_number, "zone with that name "
                             "already defined on line "
                             f"{self.zone_names[name]}.")
        self.zone_names[name] = line_number

        try:
            x = int(arguments[1])
            y = int(arguments[2])
        except ValueError:
            raise ParseError(line_number, "x and y must be integers") from None

        if (x, y) in self.zone_coordinates:
            raise ParseError(line_number,
                             "a zone with those coordinates already exists")
        self.zone_coordinates.add((x, y))

        metadata = self._parse_metadata(line_number,
                                        metadata_part,
                                        ["color",
                                         "zone",
                                         "max_drones"],
                                        ["max_drones"])

        zone_category = ZoneCategory.REGULAR
        if key == "start_hub":
            if self.start_hub_line is not None:
                raise ParseError(line_number, "start_hub already defined "
                                 f"on line {self.start_hub_line}")
            self.start_hub_line = line_number
            zone_category = ZoneCategory.START
        if key == "end_hub":
            if self.end_hub_line is not None:
                raise ParseError(line_number, "end_hub already defined "
                                 f"on line {self.end_hub_line}")
            self.end_hub_line = line_number
            zone_category = ZoneCategory.END
        if zone_category in (ZoneCategory.START, ZoneCategory.END):
            assert self.nb_drones is not None
            metadata["max_drones"] = self.nb_drones

        zone_type_value = metadata.get("zone", ZoneType.NORMAL.value)
        color_value = metadata.get("color")
        max_drones_value = metadata.get("max_drones", 1)

        try:
            zone = Zone(
                name=name,
                x=x,
                y=y,
                zone_category=zone_category,
                zone=cast(ZoneType, zone_type_value),
                color=cast("str | None", color_value),
                max_drones=cast(int, max_drones_value),
            )
        except ValidationError as error:
            raise self._translate_validation_error(line_number,
                                                   error) from error
        self.zones.append(zone)

    def _parse_connection(self, line_number: int, value: str) -> None:
        if "[" in value:
            main_part, metadata_part = value.split("[", 1)
            metadata_part = metadata_part.rstrip("]")
        else:
            main_part = value
            metadata_part = ""

        arguments = main_part.strip().split("-")
        if len(arguments) != 2:
            raise ParseError(line_number, "connections must connect "
                             "exactly 2 zones: <zone1>-<zone2>")
        zone1 = arguments[0]
        zone2 = arguments[1]

        if zone1 not in self.zone_names:
            raise ParseError(line_number, f"zone {zone1} in "
                             "connection was not defined before")
        if zone2 not in self.zone_names:
            raise ParseError(line_number, f"zone {zone2} in "
                             "connection was not defined before")
        if zone1 == zone2:
            raise ParseError(line_number, "connection must link "
                             "two different zones")

        pair = frozenset({zone1, zone2})
        if pair in self.connection_pairs:
            raise ParseError(line_number, "duplicate connection "
                             f"between '{zone1}' and '{zone2}'")
        self.connection_pairs.add(pair)

        metadata = self._parse_metadata(line_number,
                                        metadata_part,
                                        ["max_link_capacity"],
                                        ["max_link_capacity"])
        max_links_value = metadata.get("max_link_capacity", 1)
        try:
            connection = Connection(endpoints=pair,
                                    max_link_capacity=cast(
                                        int,
                                        max_links_value
                                        )
                                    )
        except ValidationError as error:
            raise self._translate_validation_error(line_number,
                                                   error) from error
        self.connections.append(connection)

    def _parse_metadata(
            self,
            line_number: int,
            metadata: str,
            valid_keys: list[str],
            int_keys: list[str],
            ) -> dict[str, str | int]:
        parsed_metadata: dict[str, str | int] = {}
        fields = metadata.strip().split()
        for field in fields:
            if "=" not in field:
                raise ParseError(line_number, "invalid metadata token "
                                 f"'{field}', expected <key>=<value>")
            key, value_str = field.split("=", 1)
            if not key or not value_str:
                raise ParseError(line_number,
                                 f"invalid metadata token '{field}'")
            key = key.lower()
            if key not in valid_keys:
                raise ParseError(line_number,
                                 f"invalid metadata key '{key}' "
                                 "for this context")
            if key in parsed_metadata:
                raise ParseError(line_number,
                                 f"duplicate metadata key '{key}'")

            value: str | int = value_str
            if key in int_keys:
                try:
                    value = int(value_str)
                except ValueError:
                    raise ParseError(line_number, f"invalid value for '{key}':"
                                     " must be a positive integer") from None

            parsed_metadata[key] = value
        return parsed_metadata

    def _translate_validation_error(self,
                                    line_number: int,
                                    error: ValidationError
                                    ) -> ParseError:
        messages: list[str] = []
        for err in error.errors():
            if err["loc"]:
                messages.append(f"{err['loc'][0]}: {err['msg']}")
            else:
                messages.append(err["msg"].replace("Value error, ", ""))
        return ParseError(line_number, "; ".join(messages))

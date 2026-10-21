from model import Zone, Connection
from collections import defaultdict


class Graph:
    def __init__(self,
                 zones: list[Zone],
                 connections: list[Connection]) -> None:
        self.zones: dict[str, Zone] = {z.name: z for z in zones}
        self.neighbour_conns: dict[str, list[Connection]] = defaultdict(list)
        for conn in connections:
            for endpoint in conn.endpoints:
                self.neighbour_conns[endpoint].append(conn)

import asyncio
import shutil
from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from xml.etree import ElementTree


class NmapScanError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenPort:
    number: int
    service_name: str


@dataclass(frozen=True)
class AliveHost:
    ip: str
    hostname: str | None = None
    open_ports: list[OpenPort] | None = None

    def with_open_ports(self, open_ports: list[OpenPort]) -> "AliveHost":
        return AliveHost(ip=self.ip, hostname=self.hostname, open_ports=open_ports)


@dataclass(frozen=True)
class NmapScanResult:
    target: str
    alive_hosts: list[AliveHost]

    @property
    def alive_ips(self) -> list[str]:
        return [host.ip for host in self.alive_hosts]


def parse_alive_hosts(nmap_xml: str) -> list[AliveHost]:
    try:
        root = ElementTree.fromstring(nmap_xml)
    except ElementTree.ParseError as exc:
        raise NmapScanError("nmap returned invalid XML") from exc

    hosts: list[AliveHost] = []
    for host_node in root.findall("host"):
        status_node = host_node.find("status")
        if status_node is None or status_node.get("state") != "up":
            continue

        address_node = _host_address_node(host_node)
        if address_node is None:
            continue

        hostname_node = host_node.find("hostnames/hostname")
        hosts.append(
            AliveHost(
                ip=address_node.get("addr", ""),
                hostname=hostname_node.get("name") if hostname_node is not None else None,
            )
        )

    return sorted(hosts, key=lambda host: _ip_sort_key(host.ip))


def parse_open_ports(nmap_xml: str) -> dict[str, list[OpenPort]]:
    try:
        root = ElementTree.fromstring(nmap_xml)
    except ElementTree.ParseError as exc:
        raise NmapScanError("nmap returned invalid XML") from exc

    ports_by_ip: dict[str, list[OpenPort]] = {}
    for host_node in root.findall("host"):
        address_node = _host_address_node(host_node)
        if address_node is None:
            continue

        ports: list[OpenPort] = []
        for port_node in host_node.findall("ports/port"):
            if port_node.get("protocol") != "tcp":
                continue

            state_node = port_node.find("state")
            if state_node is None or state_node.get("state") != "open":
                continue

            port_id = port_node.get("portid")
            if port_id is None:
                continue
            try:
                port_number = int(port_id)
            except ValueError:
                continue

            service_node = port_node.find("service")
            ports.append(
                OpenPort(
                    number=port_number,
                    service_name=(
                        service_node.get("name", "unknown")
                        if service_node is not None
                        else "unknown"
                    ),
                )
            )

        ports_by_ip[address_node.get("addr", "")] = sorted(ports, key=lambda port: port.number)

    return ports_by_ip


async def scan_alive_hosts(target: str, *, nmap_binary: str = "nmap") -> NmapScanResult:
    normalized_target = str(ip_network(target, strict=False))
    if shutil.which(nmap_binary) is None:
        raise NmapScanError(f"nmap binary not found: {nmap_binary}")

    process = await asyncio.create_subprocess_exec(
        nmap_binary,
        "-sn",
        "-oX",
        "-",
        normalized_target,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error = stderr.decode(errors="replace").strip()
        raise NmapScanError(error or f"nmap exited with code {process.returncode}")

    return NmapScanResult(
        target=normalized_target,
        alive_hosts=parse_alive_hosts(stdout.decode(errors="replace")),
    )


async def scan_target(target: str, *, nmap_binary: str = "nmap") -> NmapScanResult:
    discovery_result = await scan_alive_hosts(target, nmap_binary=nmap_binary)
    if not discovery_result.alive_hosts:
        return discovery_result

    ports_by_ip = await scan_open_ports(discovery_result.alive_ips, nmap_binary=nmap_binary)
    return NmapScanResult(
        target=discovery_result.target,
        alive_hosts=[
            host.with_open_ports(ports_by_ip.get(host.ip, []))
            for host in discovery_result.alive_hosts
        ],
    )


async def scan_open_ports(
    targets: list[str],
    *,
    nmap_binary: str = "nmap",
) -> dict[str, list[OpenPort]]:
    if shutil.which(nmap_binary) is None:
        raise NmapScanError(f"nmap binary not found: {nmap_binary}")

    process = await asyncio.create_subprocess_exec(
        nmap_binary,
        "-Pn",
        "-oX",
        "-",
        *targets,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error = stderr.decode(errors="replace").strip()
        raise NmapScanError(error or f"nmap exited with code {process.returncode}")

    return parse_open_ports(stdout.decode(errors="replace"))


def _host_address_node(host_node: ElementTree.Element) -> ElementTree.Element | None:
    for address_type in ("ipv4", "ipv6"):
        for address_node in host_node.findall("address"):
            if address_node.get("addrtype") == address_type and address_node.get("addr"):
                return address_node
    return None


def _ip_sort_key(ip: str) -> tuple[int, int]:
    address = ip_address(ip)
    return address.version, int(address)

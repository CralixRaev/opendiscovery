import unittest

from nmap_scan import NmapScanError, parse_alive_hosts, parse_open_ports


class ParseAliveHostsTest(unittest.TestCase):
    def test_returns_only_up_hosts_sorted_by_ip(self) -> None:
        xml = """
        <nmaprun>
          <host>
            <status state="up"/>
            <address addr="192.168.1.10" addrtype="ipv4"/>
            <hostnames>
              <hostname name="workstation.local"/>
            </hostnames>
          </host>
          <host>
            <status state="down"/>
            <address addr="192.168.1.2" addrtype="ipv4"/>
          </host>
          <host>
            <status state="up"/>
            <address addr="192.168.1.3" addrtype="ipv4"/>
          </host>
        </nmaprun>
        """

        hosts = parse_alive_hosts(xml)

        self.assertEqual([host.ip for host in hosts], ["192.168.1.3", "192.168.1.10"])
        self.assertIsNone(hosts[0].hostname)
        self.assertEqual(hosts[1].hostname, "workstation.local")

    def test_raises_domain_error_for_invalid_xml(self) -> None:
        with self.assertRaises(NmapScanError):
            parse_alive_hosts("<nmaprun>")

    def test_parses_open_tcp_ports_by_host(self) -> None:
        xml = """
        <nmaprun>
          <host>
            <status state="up"/>
            <address addr="192.168.1.10" addrtype="ipv4"/>
            <ports>
              <port protocol="tcp" portid="443">
                <state state="open"/>
                <service name="https"/>
              </port>
              <port protocol="tcp" portid="22">
                <state state="open"/>
                <service name="ssh"/>
              </port>
              <port protocol="tcp" portid="25">
                <state state="closed"/>
                <service name="smtp"/>
              </port>
              <port protocol="udp" portid="53">
                <state state="open"/>
                <service name="domain"/>
              </port>
            </ports>
          </host>
        </nmaprun>
        """

        ports_by_ip = parse_open_ports(xml)

        self.assertEqual(list(ports_by_ip), ["192.168.1.10"])
        self.assertEqual([port.number for port in ports_by_ip["192.168.1.10"]], [22, 443])
        self.assertEqual([port.service_name for port in ports_by_ip["192.168.1.10"]], ["ssh", "https"])


if __name__ == "__main__":
    unittest.main()

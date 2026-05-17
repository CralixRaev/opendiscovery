import unittest

from nmap_scan import NmapScanError, parse_alive_hosts


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


if __name__ == "__main__":
    unittest.main()

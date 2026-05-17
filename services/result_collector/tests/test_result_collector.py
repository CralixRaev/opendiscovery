import unittest

from result_collector.payloads import (
    InvalidScanJobResultError,
    parse_scan_job_result,
    parse_scan_job_result_subject,
)


class ScanJobResultParserTest(unittest.TestCase):
    def test_parses_scan_job_result(self) -> None:
        result = parse_scan_job_result(
            {
                "id": 42,
                "tenant_id": 7,
                "scanner_id": 9,
                "ip_network": "192.168.1.0/24",
                "alive_hosts": [
                    {"ip": "192.168.1.10", "hostname": "workstation.local"},
                    {"ip": "192.168.1.11", "hostname": None},
                ],
            }
        )

        self.assertEqual(result.id, 42)
        self.assertEqual(result.tenant_id, 7)
        self.assertEqual(result.scanner_id, 9)
        self.assertEqual([host.ip for host in result.alive_hosts], ["192.168.1.10", "192.168.1.11"])

    def test_rejects_invalid_host_ip(self) -> None:
        with self.assertRaises(InvalidScanJobResultError):
            parse_scan_job_result(
                {
                    "id": 42,
                    "tenant_id": 7,
                    "scanner_id": 9,
                    "ip_network": "192.168.1.0/24",
                    "alive_hosts": [{"ip": "not-an-ip"}],
                }
            )

    def test_parses_result_subject(self) -> None:
        self.assertEqual(
            parse_scan_job_result_subject("opendiscovery.tenants.7.scanners.9.jobs.42.result"),
            (7, 9, 42),
        )

    def test_rejects_non_result_subject(self) -> None:
        with self.assertRaises(InvalidScanJobResultError):
            parse_scan_job_result_subject("opendiscovery.tenants.7.scanners.9.jobs.42.status")


if __name__ == "__main__":
    unittest.main()

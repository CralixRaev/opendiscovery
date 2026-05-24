from core.database.models.asset import Host, HostPort, Port
from core.database.models.discovery import ScanJobHostDiscovery, ScanJobPortDiscovery
from core.database.models.scan_job import ScanJob, ScanJobStatus as ScanJobStatus
from core.database.models.scanner import Scanner
from core.database.models.tenant import Tenant
from core.database.models.user import User

__models__ = [
    Tenant,
    User,
    Scanner,
    ScanJob,
    Host,
    HostPort,
    Port,
    ScanJobHostDiscovery,
    ScanJobPortDiscovery,
]

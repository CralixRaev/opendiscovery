<script setup lang="ts">
import type {
  BadgeColor,
  DiscoveredHost,
  HostTableState,
  ScanJob,
  ScanJobForm,
  ScanJobStatus,
  Scanner,
  ScannerForm
} from '~/composables/useOpenDiscoveryDashboard'

defineProps<{
  copyScannerToken: () => Promise<void>
  createScanner: () => Promise<void>
  createScanJob: () => Promise<void>
  deleteScanner: (scanner: Scanner) => Promise<void>
  formatDate: (value: string) => string
  hosts: DiscoveredHost[]
  hostsLoading: boolean
  hostPageCount: number
  issuedScannerName: string | null
  issuedScannerToken: string | null
  loadScanners: () => Promise<void>
  loadScanJobs: () => Promise<void>
  loadHosts: (options?: { silent?: boolean, resetPage?: boolean }) => Promise<void>
  scanJobCreating: boolean
  scanJobStatusColor: (status: ScanJobStatus) => BadgeColor
  scanJobStatusIcon: (status: ScanJobStatus) => string
  scanJobs: ScanJob[]
  scanJobsLoading: boolean
  scannerCreating: boolean
  scannerDeletingId: number | null
  scannerName: (scannerId: number) => string
  scannerTokenReissuingId: number | null
  scannerUpdatingId: number | null
  scanners: Scanner[]
  scannersLoading: boolean
  reissueScannerToken: (scanner: Scanner) => Promise<void>
  updateScanner: (scanner: Scanner, name: string) => Promise<void>
}>()

const scannerForm = defineModel<ScannerForm>('scannerForm', { required: true })
const scanJobForm = defineModel<ScanJobForm>('scanJobForm', { required: true })
const hostTableState = defineModel<HostTableState>('hostTableState', { required: true })

const activeTab = ref('home')
const dashboardTabs = [
  {
    label: 'Главная',
    icon: 'i-lucide-house',
    value: 'home',
    slot: 'home'
  },
  {
    label: 'Сканеры',
    icon: 'i-lucide-scan-line',
    value: 'scanners',
    slot: 'scanners'
  },
  {
    label: 'Задания',
    icon: 'i-lucide-clipboard-list',
    value: 'scan-jobs',
    slot: 'scan-jobs'
  },
  {
    label: 'Хосты',
    icon: 'i-lucide-server',
    value: 'hosts',
    slot: 'hosts'
  }
]
</script>

<template>
  <UTabs
    v-model="activeTab"
    :items="dashboardTabs"
    variant="link"
    :unmount-on-hide="false"
    :ui="{ content: 'pt-6' }"
  >
    <template #home>
      <DashboardHostDiscoveryDashboard
        :hosts="hosts"
        :hosts-loading="hostsLoading"
        :load-hosts="loadHosts"
      />
    </template>

    <template #scanners>
      <DashboardScannerSettings
        v-model:scanner-form="scannerForm"
        :copy-scanner-token="copyScannerToken"
        :create-scanner="createScanner"
        :delete-scanner="deleteScanner"
        :format-date="formatDate"
        :issued-scanner-name="issuedScannerName"
        :issued-scanner-token="issuedScannerToken"
        :load-scanners="loadScanners"
        :scanner-creating="scannerCreating"
        :scanner-deleting-id="scannerDeletingId"
        :scanner-token-reissuing-id="scannerTokenReissuingId"
        :scanner-updating-id="scannerUpdatingId"
        :scanners="scanners"
        :scanners-loading="scannersLoading"
        :reissue-scanner-token="reissueScannerToken"
        :update-scanner="updateScanner"
      />
    </template>

    <template #scan-jobs>
      <DashboardScanJobSettings
        v-model:scan-job-form="scanJobForm"
        :create-scan-job="createScanJob"
        :format-date="formatDate"
        :load-scan-jobs="loadScanJobs"
        :scan-job-creating="scanJobCreating"
        :scan-job-status-color="scanJobStatusColor"
        :scan-job-status-icon="scanJobStatusIcon"
        :scan-jobs="scanJobs"
        :scan-jobs-loading="scanJobsLoading"
        :scanner-name="scannerName"
        :scanners="scanners"
      />
    </template>

    <template #hosts>
      <DashboardHostTable
        v-model:host-table-state="hostTableState"
        :format-date="formatDate"
        :hosts="hosts"
        :hosts-loading="hostsLoading"
        :host-page-count="hostPageCount"
        :load-hosts="loadHosts"
      />
    </template>
  </UTabs>
</template>

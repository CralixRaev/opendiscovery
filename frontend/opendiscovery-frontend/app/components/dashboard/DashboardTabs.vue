<script setup lang="ts">
import type {
  BadgeColor,
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
  formatDate: (value: string) => string
  issuedScannerName: string | null
  issuedScannerToken: string | null
  loadScanners: () => Promise<void>
  loadScanJobs: () => Promise<void>
  scanJobCreating: boolean
  scanJobStatusColor: (status: ScanJobStatus) => BadgeColor
  scanJobStatusIcon: (status: ScanJobStatus) => string
  scanJobs: ScanJob[]
  scanJobsLoading: boolean
  scannerCreating: boolean
  scannerName: (scannerId: number) => string
  scanners: Scanner[]
  scannersLoading: boolean
}>()

const scannerForm = defineModel<ScannerForm>('scannerForm', { required: true })
const scanJobForm = defineModel<ScanJobForm>('scanJobForm', { required: true })

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
      <section class="min-h-[320px]" />
    </template>

    <template #scanners>
      <DashboardScannerSettings
        v-model:scanner-form="scannerForm"
        :copy-scanner-token="copyScannerToken"
        :create-scanner="createScanner"
        :format-date="formatDate"
        :issued-scanner-name="issuedScannerName"
        :issued-scanner-token="issuedScannerToken"
        :load-scanners="loadScanners"
        :scanner-creating="scannerCreating"
        :scanners="scanners"
        :scanners-loading="scannersLoading"
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
  </UTabs>
</template>

<script setup lang="ts">
const {
  auth,
  copyScannerToken,
  createScanner,
  createScanJob,
  deleteScanner,
  formatDate,
  hosts,
  hostsLoading,
  hostPageCount,
  hostTableState,
  isAuthenticated,
  issuedScannerName,
  issuedScannerToken,
  loadScanners,
  loadScanJobs,
  loadHosts,
  loginForm,
  loginLoading,
  logout,
  scanJobCreating,
  scanJobForm,
  scanJobStatusColor,
  scanJobStatusIcon,
  scanJobs,
  scanJobsLoading,
  scannerCreating,
  scannerDeletingId,
  scannerForm,
  scannerName,
  scannerTokenReissuingId,
  scannerUpdatingId,
  scanners,
  scannersLoading,
  sessionLoading,
  submitLogin,
  reissueScannerToken,
  updateScanner
} = useOpenDiscoveryDashboard()
</script>

<template>
  <main
    v-if="sessionLoading"
    class="mx-auto flex min-h-[calc(100dvh-3.5rem)] max-w-6xl items-center justify-center px-4 py-10 sm:px-6"
  >
    <UIcon
      name="i-lucide-loader-circle"
      class="size-7 animate-spin text-primary"
    />
  </main>

  <AuthLoginView
    v-else-if="!isAuthenticated"
    v-model:login-form="loginForm"
    :login-loading="loginLoading"
    :submit-login="submitLogin"
  />

  <main
    v-else
    class="mx-auto min-h-[calc(100dvh-3.5rem)] max-w-6xl px-4 py-8 sm:px-6"
  >
    <DashboardHeader
      :auth="auth"
      :logout="logout"
    />

    <DashboardTabs
      v-model:scanner-form="scannerForm"
      v-model:scan-job-form="scanJobForm"
      v-model:host-table-state="hostTableState"
      :copy-scanner-token="copyScannerToken"
      :create-scanner="createScanner"
      :create-scan-job="createScanJob"
      :delete-scanner="deleteScanner"
      :format-date="formatDate"
      :hosts="hosts"
      :hosts-loading="hostsLoading"
      :host-page-count="hostPageCount"
      :issued-scanner-name="issuedScannerName"
      :issued-scanner-token="issuedScannerToken"
      :load-scanners="loadScanners"
      :load-scan-jobs="loadScanJobs"
      :load-hosts="loadHosts"
      :scan-job-creating="scanJobCreating"
      :scan-job-status-color="scanJobStatusColor"
      :scan-job-status-icon="scanJobStatusIcon"
      :scan-jobs="scanJobs"
      :scan-jobs-loading="scanJobsLoading"
      :scanner-creating="scannerCreating"
      :scanner-deleting-id="scannerDeletingId"
      :scanner-name="scannerName"
      :scanner-token-reissuing-id="scannerTokenReissuingId"
      :scanner-updating-id="scannerUpdatingId"
      :scanners="scanners"
      :scanners-loading="scannersLoading"
      :reissue-scanner-token="reissueScannerToken"
      :update-scanner="updateScanner"
    />
  </main>
</template>

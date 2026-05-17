<script setup lang="ts">
const {
  auth,
  copyScannerToken,
  createScanner,
  createScanJob,
  formatDate,
  hosts,
  hostsLoading,
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
  scannerForm,
  scannerName,
  scanners,
  scannersLoading,
  sessionLoading,
  submitLogin
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
      :copy-scanner-token="copyScannerToken"
      :create-scanner="createScanner"
      :create-scan-job="createScanJob"
      :format-date="formatDate"
      :hosts="hosts"
      :hosts-loading="hostsLoading"
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
      :scanner-name="scannerName"
      :scanners="scanners"
      :scanners-loading="scannersLoading"
    />
  </main>
</template>

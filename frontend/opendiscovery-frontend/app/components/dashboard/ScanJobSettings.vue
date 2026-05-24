<script setup lang="ts">
import type { BadgeColor, ScanJob, ScanJobForm, ScanJobStatus, Scanner } from '~/composables/useOpenDiscoveryDashboard'

defineProps<{
  createScanJob: () => Promise<void>
  formatDate: (value: string) => string
  loadScanJobs: () => Promise<void>
  scanJobCreating: boolean
  scanJobStatusColor: (status: ScanJobStatus) => BadgeColor
  scanJobStatusIcon: (status: ScanJobStatus) => string
  scanJobs: ScanJob[]
  scanJobsLoading: boolean
  scannerName: (scannerId: number) => string
  scanners: Scanner[]
}>()

const scanJobForm = defineModel<ScanJobForm>('scanJobForm', { required: true })
</script>

<template>
  <div class="grid gap-6 lg:grid-cols-[420px_1fr]">
    <section>
      <UCard
        variant="subtle"
        :ui="{ root: 'rounded-lg', body: 'p-5 sm:p-6' }"
      >
        <template #header>
          <div class="flex items-center gap-3">
            <UIcon
              name="i-lucide-play"
              class="size-5 text-primary"
            />
            <h2 class="text-base font-semibold text-highlighted">
              Новое задание
            </h2>
          </div>
        </template>

        <form
          class="space-y-5"
          @submit.prevent="createScanJob"
        >
          <UFormField
            label="Подсеть"
            name="scan-job-ip-network"
            required
          >
            <UInput
              v-model="scanJobForm.ip_network"
              class="w-full"
              icon="i-lucide-network"
              placeholder="192.168.1.0/24"
              required
              maxlength="128"
            />
          </UFormField>

          <UFormField
            label="Сканер"
            name="scan-job-scanner"
            required
          >
            <select
              v-model="scanJobForm.scanner_id"
              class="h-9 w-full rounded-md border border-default bg-default px-3 text-sm text-highlighted outline-none focus:border-primary"
              required
            >
              <option
                value=""
                disabled
              >
                Выберите сканер
              </option>
              <option
                v-for="scanner in scanners"
                :key="scanner.id"
                :value="String(scanner.id)"
              >
                {{ scanner.name }}
              </option>
            </select>
          </UFormField>

          <UButton
            type="submit"
            block
            icon="i-lucide-send"
            :loading="scanJobCreating"
            :disabled="!scanners.length"
          >
            Создать и отправить
          </UButton>
        </form>
      </UCard>
    </section>

    <section>
      <div class="mb-4 flex items-center justify-between gap-3">
        <h2 class="text-base font-semibold text-highlighted">
          Задания
        </h2>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-refresh-cw"
          :loading="scanJobsLoading"
          @click="loadScanJobs"
        />
      </div>

      <div
        v-if="scanJobs.length"
        class="overflow-hidden rounded-lg border border-default"
      >
        <div
          v-for="scanJob in scanJobs"
          :key="scanJob.id"
          class="grid gap-3 border-b border-default px-4 py-4 last:border-b-0 sm:grid-cols-[1fr_auto] sm:items-center"
        >
          <div class="min-w-0">
            <p class="truncate font-medium text-highlighted">
              {{ scanJob.ip_network }}
            </p>
            <p class="mt-1 text-sm text-muted">
              ID {{ scanJob.id }} · {{ scannerName(scanJob.scanner_id) }} · {{ formatDate(scanJob.created_at) }}
            </p>
          </div>
          <UBadge
            :color="scanJobStatusColor(scanJob.status)"
            variant="subtle"
            :icon="scanJobStatusIcon(scanJob.status)"
            :class="{ 'animate-pulse': scanJob.status === 'running' }"
          >
            {{ scanJob.status }}
          </UBadge>
        </div>
      </div>

      <UAlert
        v-else
        color="neutral"
        variant="subtle"
        icon="i-lucide-clipboard-list"
        title="Заданий пока нет"
      />
    </section>
  </div>
</template>

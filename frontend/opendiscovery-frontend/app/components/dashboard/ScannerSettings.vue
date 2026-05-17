<script setup lang="ts">
import type { Scanner, ScannerForm } from '~/composables/useOpenDiscoveryDashboard'

defineProps<{
  copyScannerToken: () => Promise<void>
  createScanner: () => Promise<void>
  formatDate: (value: string) => string
  issuedScannerName: string | null
  issuedScannerToken: string | null
  loadScanners: () => Promise<void>
  scannerCreating: boolean
  scanners: Scanner[]
  scannersLoading: boolean
}>()

const scannerForm = defineModel<ScannerForm>('scannerForm', { required: true })
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
              name="i-lucide-scan-line"
              class="size-5 text-primary"
            />
            <h2 class="text-base font-semibold text-highlighted">
              Новый сканер
            </h2>
          </div>
        </template>

        <form
          class="space-y-5"
          @submit.prevent="createScanner"
        >
          <UFormField
            label="Имя сканера"
            name="scanner-name"
            required
          >
            <UInput
              v-model="scannerForm.name"
              class="w-full"
              icon="i-lucide-radio-receiver"
              placeholder="office-network-01"
              required
              maxlength="128"
            />
          </UFormField>

          <UButton
            type="submit"
            block
            icon="i-lucide-plus"
            :loading="scannerCreating"
          >
            Создать сканер
          </UButton>
        </form>
      </UCard>

      <UCard
        v-if="issuedScannerToken"
        class="mt-6"
        variant="subtle"
        :ui="{ root: 'rounded-lg', body: 'p-5 sm:p-6' }"
      >
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <div class="min-w-0">
              <p class="text-sm font-medium text-muted">
                JWT для сканера
              </p>
              <h2 class="truncate text-base font-semibold text-highlighted">
                {{ issuedScannerName }}
              </h2>
            </div>
            <UButton
              color="neutral"
              variant="outline"
              icon="i-lucide-copy"
              @click="copyScannerToken"
            >
              Копировать
            </UButton>
          </div>
        </template>

        <UTextarea
          :model-value="issuedScannerToken"
          class="w-full font-mono text-xs"
          autoresize
          readonly
          :rows="6"
        />
      </UCard>
    </section>

    <section>
      <div class="mb-4 flex items-center justify-between gap-3">
        <h2 class="text-base font-semibold text-highlighted">
          Сканеры
        </h2>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-refresh-cw"
          :loading="scannersLoading"
          @click="loadScanners"
        />
      </div>

      <div
        v-if="scanners.length"
        class="overflow-hidden rounded-lg border border-default"
      >
        <div
          v-for="scanner in scanners"
          :key="scanner.id"
          class="grid gap-3 border-b border-default px-4 py-4 last:border-b-0 sm:grid-cols-[1fr_auto] sm:items-center"
        >
          <div class="min-w-0">
            <p class="truncate font-medium text-highlighted">
              {{ scanner.name }}
            </p>
            <p class="mt-1 text-sm text-muted">
              ID {{ scanner.id }} · {{ formatDate(scanner.created_at) }}
            </p>
          </div>
          <UBadge
            color="success"
            variant="subtle"
            icon="i-lucide-circle-check"
          >
            создан
          </UBadge>
        </div>
      </div>

      <UAlert
        v-else
        color="neutral"
        variant="subtle"
        icon="i-lucide-inbox"
        title="Сканеров пока нет"
      />
    </section>
  </div>
</template>

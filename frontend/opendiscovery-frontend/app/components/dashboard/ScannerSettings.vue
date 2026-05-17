<script setup lang="ts">
import type { Scanner, ScannerForm } from '~/composables/useOpenDiscoveryDashboard'

const props = defineProps<{
  copyScannerToken: () => Promise<void>
  createScanner: () => Promise<void>
  deleteScanner: (scanner: Scanner) => Promise<void>
  formatDate: (value: string) => string
  issuedScannerName: string | null
  issuedScannerToken: string | null
  loadScanners: () => Promise<void>
  scannerCreating: boolean
  scannerDeletingId: number | null
  scannerTokenReissuingId: number | null
  scannerUpdatingId: number | null
  scanners: Scanner[]
  scannersLoading: boolean
  reissueScannerToken: (scanner: Scanner) => Promise<void>
  updateScanner: (scanner: Scanner, name: string) => Promise<void>
}>()

const scannerForm = defineModel<ScannerForm>('scannerForm', { required: true })
const editingScannerId = ref<number | null>(null)
const editingScannerName = ref('')

function startScannerRename(scanner: Scanner) {
  editingScannerId.value = scanner.id
  editingScannerName.value = scanner.name
}

function cancelScannerRename() {
  editingScannerId.value = null
  editingScannerName.value = ''
}

async function finishScannerRename(scanner: Scanner) {
  if (!editingScannerName.value.trim()) {
    return
  }

  await props.updateScanner(scanner, editingScannerName.value)
  cancelScannerRename()
}
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
          class="grid gap-3 border-b border-default px-4 py-4 last:border-b-0 lg:grid-cols-[1fr_auto] lg:items-center"
        >
          <form
            v-if="editingScannerId === scanner.id"
            class="grid gap-3 lg:col-span-2 sm:grid-cols-[minmax(0,1fr)_auto]"
            @submit.prevent="finishScannerRename(scanner)"
          >
            <div class="min-w-0">
              <UInput
                v-model="editingScannerName"
                class="w-full"
                icon="i-lucide-radio-receiver"
                required
                maxlength="128"
                autofocus
              />
              <p class="mt-1 text-sm text-muted">
                ID {{ scanner.id }} · {{ formatDate(scanner.created_at) }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2 sm:justify-end">
              <UButton
                type="submit"
                icon="i-lucide-check"
                :loading="scannerUpdatingId === scanner.id"
              >
                Сохранить
              </UButton>
              <UButton
                type="button"
                color="neutral"
                variant="ghost"
                icon="i-lucide-x"
                :disabled="scannerUpdatingId === scanner.id"
                @click="cancelScannerRename"
              >
                Отмена
              </UButton>
            </div>
          </form>

          <template v-else>
            <div class="min-w-0">
              <p class="truncate font-medium text-highlighted">
                {{ scanner.name }}
              </p>
              <p class="mt-1 text-sm text-muted">
                ID {{ scanner.id }} · {{ formatDate(scanner.created_at) }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2 lg:justify-end">
              <UButton
                color="neutral"
                variant="outline"
                icon="i-lucide-pencil"
                @click="startScannerRename(scanner)"
              >
                Переименовать
              </UButton>
              <UButton
                color="neutral"
                variant="outline"
                icon="i-lucide-key-round"
                :loading="scannerTokenReissuingId === scanner.id"
                @click="reissueScannerToken(scanner)"
              >
                Перевыпустить JWT
              </UButton>
              <UButton
                color="error"
                variant="subtle"
                icon="i-lucide-trash-2"
                :loading="scannerDeletingId === scanner.id"
                @click="deleteScanner(scanner)"
              >
                Удалить
              </UButton>
            </div>
          </template>
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

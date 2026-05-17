<script setup lang="ts">
type AuthenticatedUser = {
  id: number
  username: string
  tenant: string
  tenant_id: number
}

type LoginResponse = {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: AuthenticatedUser
}

type Scanner = {
  id: number
  name: string
  created_at: string
  tenant_id: number
}

type ScannerCreateResponse = {
  scanner: Scanner
  scanner_token: string
  token_type: 'bearer'
  expires_in: number
}

type ScanJobStatus = 'pending' | 'running' | 'finished' | 'failed'

type ScanJob = {
  id: number
  ip_network: string
  created_at: string
  finished_at: string | null
  status: ScanJobStatus
  tenant_id: number
  scanner_id: number
}

const config = useRuntimeConfig()
const toast = useToast()

const loginForm = reactive({
  tenant: '',
  username: '',
  password: ''
})

const scannerForm = reactive({
  name: ''
})

const scanJobForm = reactive({
  ip_network: '',
  scanner_id: ''
})

const loginLoading = ref(false)
const sessionLoading = ref(true)
const scannersLoading = ref(false)
const scannerCreating = ref(false)
const scanJobsLoading = ref(false)
const scanJobCreating = ref(false)
const auth = ref<LoginResponse | null>(null)
const scanners = ref<Scanner[]>([])
const scanJobs = ref<ScanJob[]>([])
const issuedScannerToken = ref<string | null>(null)
const issuedScannerName = ref<string | null>(null)

const apiBaseUrl = computed(() => String(config.public.apiBaseUrl).replace(/\/$/, ''))
const isAuthenticated = computed(() => auth.value !== null)
let scanJobsPollingTimer: number | null = null
let scanJobsRequestInFlight = false

function authHeaders(): Record<string, string> {
  if (!auth.value) {
    return {}
  }

  return {
    Authorization: `Bearer ${auth.value.access_token}`
  }
}

function persistSession(response: LoginResponse) {
  auth.value = response
  localStorage.setItem('opendiscovery.accessToken', response.access_token)
  localStorage.setItem('opendiscovery.session', JSON.stringify(response))
}

function clearSession() {
  stopScanJobsPolling()
  auth.value = null
  scanners.value = []
  scanJobs.value = []
  issuedScannerToken.value = null
  issuedScannerName.value = null
  localStorage.removeItem('opendiscovery.accessToken')
  localStorage.removeItem('opendiscovery.session')
}

async function restoreSession() {
  const storedSession = localStorage.getItem('opendiscovery.session')
  const storedToken = localStorage.getItem('opendiscovery.accessToken')

  if (!storedSession || !storedToken) {
    sessionLoading.value = false
    return
  }

  try {
    const parsed = JSON.parse(storedSession) as LoginResponse
    auth.value = parsed
    const user = await $fetch<AuthenticatedUser>(`${apiBaseUrl.value}/api/auth/me`, {
      headers: authHeaders()
    })
    auth.value = { ...parsed, user }
    await Promise.all([loadScanners(), loadScanJobs()])
    startScanJobsPolling()
  } catch {
    clearSession()
  } finally {
    sessionLoading.value = false
  }
}

async function submitLogin() {
  loginLoading.value = true

  try {
    const response = await $fetch<LoginResponse>(`${apiBaseUrl.value}/api/auth/login`, {
      method: 'POST',
      body: loginForm
    })

    persistSession(response)
    loginForm.password = ''
    await Promise.all([loadScanners(), loadScanJobs()])
    startScanJobsPolling()

    toast.add({
      title: 'Вход выполнен',
      description: `${response.user.tenant} / ${response.user.username}`,
      color: 'success',
      icon: 'i-lucide-circle-check'
    })
  } catch {
    clearSession()

    toast.add({
      title: 'Не удалось войти',
      description: 'Проверьте тенант, имя пользователя и пароль',
      color: 'error',
      icon: 'i-lucide-circle-alert'
    })
  } finally {
    loginLoading.value = false
  }
}

async function loadScanners() {
  if (!auth.value) {
    return
  }

  scannersLoading.value = true

  try {
    scanners.value = await $fetch<Scanner[]>(`${apiBaseUrl.value}/api/scanners`, {
      headers: authHeaders()
    })
  } catch {
    toast.add({
      title: 'Не удалось загрузить сканеры',
      color: 'error',
      icon: 'i-lucide-circle-alert'
    })
  } finally {
    scannersLoading.value = false
  }
}

async function loadScanJobs(options: { silent?: boolean } = {}) {
  if (!auth.value) {
    return
  }

  if (scanJobsRequestInFlight) {
    return
  }

  scanJobsRequestInFlight = true

  if (!options.silent) {
    scanJobsLoading.value = true
  }

  try {
    scanJobs.value = await $fetch<ScanJob[]>(`${apiBaseUrl.value}/api/scan-jobs`, {
      headers: authHeaders()
    })
  } catch {
    if (!options.silent) {
      toast.add({
        title: 'Не удалось загрузить задания',
        color: 'error',
        icon: 'i-lucide-circle-alert'
      })
    }
  } finally {
    scanJobsRequestInFlight = false
    if (!options.silent) {
      scanJobsLoading.value = false
    }
  }
}

function startScanJobsPolling() {
  if (scanJobsPollingTimer !== null) {
    return
  }

  scanJobsPollingTimer = window.setInterval(() => {
    void loadScanJobs({ silent: true })
  }, 5000)
}

function stopScanJobsPolling() {
  if (scanJobsPollingTimer === null) {
    return
  }

  window.clearInterval(scanJobsPollingTimer)
  scanJobsPollingTimer = null
}

async function createScanner() {
  if (!auth.value) {
    return
  }

  scannerCreating.value = true
  issuedScannerToken.value = null
  issuedScannerName.value = null

  try {
    const response = await $fetch<ScannerCreateResponse>(`${apiBaseUrl.value}/api/scanners`, {
      method: 'POST',
      headers: authHeaders(),
      body: scannerForm
    })

    scanners.value = [response.scanner, ...scanners.value]
    if (!scanJobForm.scanner_id) {
      scanJobForm.scanner_id = String(response.scanner.id)
    }
    issuedScannerToken.value = response.scanner_token
    issuedScannerName.value = response.scanner.name
    scannerForm.name = ''

    toast.add({
      title: 'Сканер создан',
      description: response.scanner.name,
      color: 'success',
      icon: 'i-lucide-scan-line'
    })
  } catch {
    toast.add({
      title: 'Не удалось создать сканер',
      description: 'Проверьте имя и попробуйте еще раз',
      color: 'error',
      icon: 'i-lucide-circle-alert'
    })
  } finally {
    scannerCreating.value = false
  }
}

async function createScanJob() {
  if (!auth.value) {
    return
  }

  scanJobCreating.value = true

  try {
    const response = await $fetch<ScanJob>(`${apiBaseUrl.value}/api/scan-jobs`, {
      method: 'POST',
      headers: authHeaders(),
      body: {
        ip_network: scanJobForm.ip_network,
        scanner_id: Number(scanJobForm.scanner_id)
      }
    })

    scanJobs.value = [response, ...scanJobs.value]
    scanJobForm.ip_network = ''

    toast.add({
      title: 'Задание создано',
      description: response.ip_network,
      color: 'success',
      icon: 'i-lucide-play'
    })
  } catch {
    toast.add({
      title: 'Не удалось создать задание',
      description: 'Выберите сканер и проверьте подсеть',
      color: 'error',
      icon: 'i-lucide-circle-alert'
    })
  } finally {
    scanJobCreating.value = false
  }
}

async function copyScannerToken() {
  if (!issuedScannerToken.value) {
    return
  }

  await navigator.clipboard.writeText(issuedScannerToken.value)
  toast.add({
    title: 'JWT скопирован',
    color: 'success',
    icon: 'i-lucide-copy-check'
  })
}

function logout() {
  clearSession()
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value))
}

function scannerName(scannerId: number) {
  return scanners.value.find(scanner => scanner.id === scannerId)?.name ?? `scanner #${scannerId}`
}

function scanJobStatusColor(status: ScanJobStatus) {
  if (status === 'finished') {
    return 'success'
  }
  if (status === 'failed') {
    return 'error'
  }
  if (status === 'running') {
    return 'warning'
  }
  return 'neutral'
}

function scanJobStatusIcon(status: ScanJobStatus) {
  if (status === 'finished') {
    return 'i-lucide-circle-check'
  }
  if (status === 'failed') {
    return 'i-lucide-circle-x'
  }
  if (status === 'running') {
    return 'i-lucide-loader-circle'
  }
  return 'i-lucide-clock'
}

onMounted(restoreSession)
onUnmounted(stopScanJobsPolling)
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

  <main
    v-else-if="!isAuthenticated"
    class="mx-auto grid min-h-[calc(100dvh-3.5rem)] max-w-6xl items-center gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_440px]"
  >
    <section class="max-w-2xl">
      <p class="mb-3 text-sm font-medium text-primary">
        OpenDiscovery
      </p>
      <h1 class="text-3xl font-semibold tracking-normal text-highlighted sm:text-5xl">
        Войти
      </h1>
    </section>

    <UCard
      variant="subtle"
      class="w-full"
      :ui="{ root: 'rounded-lg', body: 'p-5 sm:p-6' }"
    >
      <form
        class="space-y-5"
        @submit.prevent="submitLogin"
      >
        <UFormField
          label="Тенант"
          name="tenant"
          required
        >
          <UInput
            v-model="loginForm.tenant"
            class="w-full"
            icon="i-lucide-building-2"
            placeholder="acme"
            autocomplete="organization"
            required
          />
        </UFormField>

        <UFormField
          label="Пользователь"
          name="username"
          required
        >
          <UInput
            v-model="loginForm.username"
            class="w-full"
            icon="i-lucide-user"
            placeholder="admin"
            autocomplete="username"
            required
          />
        </UFormField>

        <UFormField
          label="Пароль"
          name="password"
          required
        >
          <UInput
            v-model="loginForm.password"
            class="w-full"
            icon="i-lucide-lock-keyhole"
            type="password"
            autocomplete="current-password"
            required
          />
        </UFormField>

        <UButton
          type="submit"
          block
          size="lg"
          icon="i-lucide-log-in"
          :loading="loginLoading"
        >
          Войти
        </UButton>
      </form>
    </UCard>
  </main>

  <main
    v-else
    class="mx-auto min-h-[calc(100dvh-3.5rem)] max-w-6xl px-4 py-8 sm:px-6"
  >
    <section class="mb-8 flex flex-col gap-4 border-b border-default pb-6 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-sm font-medium text-primary">
          {{ auth?.user.tenant }}
        </p>
        <h1 class="mt-1 text-2xl font-semibold tracking-normal text-highlighted sm:text-3xl">
          Дашборд
        </h1>
      </div>

      <div class="flex items-center gap-3">
        <UBadge
          variant="subtle"
          color="neutral"
          icon="i-lucide-user"
        >
          {{ auth?.user.username }}
        </UBadge>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-log-out"
          @click="logout"
        >
          Выйти
        </UButton>
      </div>
    </section>

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

        <UCard
          class="mt-6"
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

        <div class="mb-4 mt-8 flex items-center justify-between gap-3">
          <h2 class="text-base font-semibold text-highlighted">
            Задания
          </h2>
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-lucide-refresh-cw"
            :loading="scanJobsLoading"
            @click="() => loadScanJobs()"
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
  </main>
</template>

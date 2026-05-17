import { computed, onMounted, onUnmounted, reactive, ref, useRuntimeConfig, useToast } from '#imports'

export type AuthenticatedUser = {
  id: number
  username: string
  tenant: string
  tenant_id: number
}

export type LoginResponse = {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: AuthenticatedUser
}

export type LoginForm = {
  tenant: string
  username: string
  password: string
}

export type Scanner = {
  id: number
  name: string
  created_at: string
  tenant_id: number
}

export type ScannerForm = {
  name: string
}

type ScannerCreateResponse = {
  scanner: Scanner
  scanner_token: string
  token_type: 'bearer'
  expires_in: number
}

export type ScanJobStatus = 'pending' | 'running' | 'finished' | 'failed'

export type ScanJob = {
  id: number
  ip_network: string
  created_at: string
  finished_at: string | null
  status: ScanJobStatus
  tenant_id: number
  scanner_id: number
}

export type DiscoveredHost = {
  id: number
  ip: string
  created_at: string
  updated_at: string
  tenant_id: number
  open_ports: Array<{
    number: number
    service_name: string
  }>
}

export type ScanJobForm = {
  ip_network: string
  scanner_id: string
}

export type BadgeColor = 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'

export function useOpenDiscoveryDashboard() {
  const config = useRuntimeConfig()
  const toast = useToast()

  const loginForm = reactive<LoginForm>({
    tenant: '',
    username: '',
    password: ''
  })

  const scannerForm = reactive<ScannerForm>({
    name: ''
  })

  const scanJobForm = reactive<ScanJobForm>({
    ip_network: '',
    scanner_id: ''
  })

  const loginLoading = ref(false)
  const sessionLoading = ref(true)
  const scannersLoading = ref(false)
  const scannerCreating = ref(false)
  const scanJobsLoading = ref(false)
  const scanJobCreating = ref(false)
  const hostsLoading = ref(false)
  const auth = ref<LoginResponse | null>(null)
  const scanners = ref<Scanner[]>([])
  const scanJobs = ref<ScanJob[]>([])
  const hosts = ref<DiscoveredHost[]>([])
  const issuedScannerToken = ref<string | null>(null)
  const issuedScannerName = ref<string | null>(null)

  const apiBaseUrl = computed(() => String(config.public.apiBaseUrl).replace(/\/$/, ''))
  const isAuthenticated = computed(() => auth.value !== null)
  let scanJobsPollingTimer: number | null = null
  let scanJobsRequestInFlight = false
  let hostsRequestInFlight = false

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
    hosts.value = []
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
      await Promise.all([loadScanners(), loadScanJobs(), loadHosts()])
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
      await Promise.all([loadScanners(), loadScanJobs(), loadHosts()])
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

  async function loadHosts(options: { silent?: boolean } = {}) {
    if (!auth.value) {
      return
    }

    if (hostsRequestInFlight) {
      return
    }

    hostsRequestInFlight = true

    if (!options.silent) {
      hostsLoading.value = true
    }

    try {
      hosts.value = await $fetch<DiscoveredHost[]>(`${apiBaseUrl.value}/api/hosts`, {
        headers: authHeaders()
      })
    } catch {
      if (!options.silent) {
        toast.add({
          title: 'Не удалось загрузить хосты',
          color: 'error',
          icon: 'i-lucide-circle-alert'
        })
      }
    } finally {
      hostsRequestInFlight = false
      if (!options.silent) {
        hostsLoading.value = false
      }
    }
  }

  function startScanJobsPolling() {
    if (scanJobsPollingTimer !== null) {
      return
    }

    scanJobsPollingTimer = window.setInterval(() => {
      void loadScanJobs({ silent: true })
      void loadHosts({ silent: true })
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

  function scanJobStatusColor(status: ScanJobStatus): BadgeColor {
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

  return {
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
  }
}

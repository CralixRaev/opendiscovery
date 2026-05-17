<script setup lang="ts">
type LoginResponse = {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: {
    id: number
    username: string
    tenant: string
    tenant_id: number
  }
}

const config = useRuntimeConfig()
const toast = useToast()

const form = reactive({
  tenant: '',
  username: '',
  password: ''
})

const loading = ref(false)
const auth = ref<LoginResponse | null>(null)

const apiBaseUrl = computed(() => String(config.public.apiBaseUrl).replace(/\/$/, ''))

async function submit() {
  loading.value = true

  try {
    const response = await $fetch<LoginResponse>(`${apiBaseUrl.value}/api/auth/login`, {
      method: 'POST',
      body: form
    })

    auth.value = response
    localStorage.setItem('opendiscovery.accessToken', response.access_token)

    toast.add({
      title: 'Вход выполнен',
      description: `${response.user.tenant} / ${response.user.username}`,
      color: 'success',
      icon: 'i-lucide-circle-check'
    })
  } catch {
    auth.value = null
    localStorage.removeItem('opendiscovery.accessToken')

    toast.add({
      title: 'Не удалось войти',
      description: 'Проверьте тенант, имя пользователя и пароль',
      color: 'error',
      icon: 'i-lucide-circle-alert'
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="mx-auto grid min-h-[calc(100dvh-3.5rem)] max-w-6xl items-center gap-10 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_440px]">
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
        @submit.prevent="submit"
      >
        <UFormField
          label="Тенант"
          name="tenant"
          required
        >
          <UInput
            v-model="form.tenant"
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
            v-model="form.username"
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
            v-model="form.password"
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
          :loading="loading"
        >
          Войти
        </UButton>
      </form>

      <UAlert
        v-if="auth"
        class="mt-5"
        color="success"
        variant="subtle"
        icon="i-lucide-circle-check"
        title="Сессия активна"
        :description="`${auth.user.tenant} / ${auth.user.username}`"
      />
    </UCard>
  </main>
</template>

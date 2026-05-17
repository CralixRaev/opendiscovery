<script setup lang="ts">
import type { LoginForm } from '~/composables/useOpenDiscoveryDashboard'

defineProps<{
  loginLoading: boolean
  submitLogin: () => Promise<void>
}>()

const loginForm = defineModel<LoginForm>('loginForm', { required: true })
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
</template>

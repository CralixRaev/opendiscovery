<script setup lang="ts">
import type { LoginResponse } from '~/composables/useOpenDiscoveryDashboard'

defineProps<{
  auth: LoginResponse | null
  logout: () => void
}>()
</script>

<template>
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
</template>

<script setup lang="ts">
import type { DiscoveredHost } from '~/composables/useOpenDiscoveryDashboard'

defineProps<{
  formatDate: (value: string) => string
  hosts: DiscoveredHost[]
  hostsLoading: boolean
  loadHosts: () => Promise<void>
}>()
</script>

<template>
  <section>
    <div class="mb-4 flex items-center justify-between gap-3">
      <div class="min-w-0">
        <h2 class="text-base font-semibold text-highlighted">
          Задискаверенные хосты
        </h2>
        <p class="mt-1 text-sm text-muted">
          {{ hosts.length }} всего
        </p>
      </div>
      <UButton
        color="neutral"
        variant="ghost"
        icon="i-lucide-refresh-cw"
        :loading="hostsLoading"
        @click="loadHosts"
      />
    </div>

    <div
      v-if="hosts.length"
      class="overflow-hidden rounded-lg border border-default"
    >
      <div class="overflow-x-auto">
        <table class="w-full min-w-[820px] text-left text-sm">
          <thead class="border-b border-default bg-muted/40 text-xs uppercase text-muted">
            <tr>
              <th class="px-4 py-3 font-medium">
                IP
              </th>
              <th class="px-4 py-3 font-medium">
                ID
              </th>
              <th class="px-4 py-3 font-medium">
                Открытые порты
              </th>
              <th class="px-4 py-3 font-medium">
                Обнаружен
              </th>
              <th class="px-4 py-3 font-medium">
                Обновлен
              </th>
            </tr>
          </thead>
          <tbody class="divide-y divide-default">
            <tr
              v-for="host in hosts"
              :key="host.id"
              class="bg-default"
            >
              <td class="px-4 py-3 font-mono font-medium text-highlighted">
                {{ host.ip }}
              </td>
              <td class="px-4 py-3 text-muted">
                {{ host.id }}
              </td>
              <td class="px-4 py-3 text-muted">
                <div
                  v-if="host.open_ports.length"
                  class="flex flex-wrap gap-1.5"
                >
                  <UBadge
                    v-for="port in host.open_ports"
                    :key="`${host.id}-${port.number}-${port.service_name}`"
                    color="neutral"
                    variant="soft"
                    size="sm"
                  >
                    {{ port.number }}/{{ port.service_name }}
                  </UBadge>
                </div>
                <span v-else>нет</span>
              </td>
              <td class="px-4 py-3 text-muted">
                {{ formatDate(host.created_at) }}
              </td>
              <td class="px-4 py-3 text-muted">
                {{ formatDate(host.updated_at) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <UAlert
      v-else
      color="neutral"
      variant="subtle"
      icon="i-lucide-server"
      title="Хостов пока нет"
    />
  </section>
</template>

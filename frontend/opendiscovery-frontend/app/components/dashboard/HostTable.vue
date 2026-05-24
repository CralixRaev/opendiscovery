<script setup lang="ts">
import type { DiscoveredHost, HostSortBy, HostTableState } from '~/composables/useOpenDiscoveryDashboard'

const props = defineProps<{
  formatDate: (value: string) => string
  hosts: DiscoveredHost[]
  hostsLoading: boolean
  hostPageCount: number
  loadHosts: (options?: { silent?: boolean, resetPage?: boolean }) => Promise<void>
}>()

const hostTableState = defineModel<HostTableState>('hostTableState', { required: true })

const sortLabels: Record<HostSortBy, string> = {
  ip: 'IP',
  id: 'ID',
  created_at: 'Обнаружен',
  updated_at: 'Обновлен'
}

const pageSizeOptions = [10, 20, 50, 100]

const rangeStart = computed(() => {
  if (!hostTableState.value.total) {
    return 0
  }
  return (hostTableState.value.page - 1) * hostTableState.value.pageSize + 1
})

const rangeEnd = computed(() => Math.min(
  hostTableState.value.page * hostTableState.value.pageSize,
  hostTableState.value.total
))

async function applySearch() {
  await props.loadHosts({ resetPage: true })
}

async function resetSearch() {
  hostTableState.value.search = ''
  await props.loadHosts({ resetPage: true })
}

async function setSort(sortBy: HostSortBy) {
  if (hostTableState.value.sortBy === sortBy) {
    hostTableState.value.sortDirection = hostTableState.value.sortDirection === 'asc' ? 'desc' : 'asc'
  } else {
    hostTableState.value.sortBy = sortBy
    hostTableState.value.sortDirection = sortBy === 'ip' || sortBy === 'id' ? 'asc' : 'desc'
  }
  await props.loadHosts({ resetPage: true })
}

async function setPage(page: number) {
  hostTableState.value.page = Math.min(Math.max(page, 1), props.hostPageCount)
  await props.loadHosts()
}

async function setPageSize(event: Event) {
  hostTableState.value.pageSize = Number((event.target as HTMLSelectElement).value)
  await props.loadHosts({ resetPage: true })
}

function sortIcon(sortBy: HostSortBy) {
  if (hostTableState.value.sortBy !== sortBy) {
    return 'i-lucide-arrow-up-down'
  }
  return hostTableState.value.sortDirection === 'asc' ? 'i-lucide-arrow-up' : 'i-lucide-arrow-down'
}
</script>

<template>
  <section>
    <div class="mb-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div class="min-w-0">
        <h2 class="text-base font-semibold text-highlighted">
          Задискаверенные хосты
        </h2>
        <p class="mt-1 text-sm text-muted">
          {{ hostTableState.total }} всего
        </p>
      </div>
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
        <UInput
          v-model="hostTableState.search"
          icon="i-lucide-search"
          placeholder="IP, ID, порт или сервис"
          class="w-full sm:w-72"
          @keydown.enter="applySearch"
        />
        <div class="flex items-center gap-2">
          <UButton
            color="neutral"
            variant="soft"
            icon="i-lucide-search"
            :loading="hostsLoading"
            @click="applySearch"
          />
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-lucide-x"
            :disabled="!hostTableState.search || hostsLoading"
            @click="resetSearch"
          />
          <UButton
            color="neutral"
            variant="ghost"
            icon="i-lucide-refresh-cw"
            :loading="hostsLoading"
            @click="() => loadHosts()"
          />
        </div>
      </div>
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
                <UButton
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  :icon="sortIcon('ip')"
                  trailing
                  @click="setSort('ip')"
                >
                  {{ sortLabels.ip }}
                </UButton>
              </th>
              <th class="px-4 py-3 font-medium">
                <UButton
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  :icon="sortIcon('id')"
                  trailing
                  @click="setSort('id')"
                >
                  {{ sortLabels.id }}
                </UButton>
              </th>
              <th class="px-4 py-3 font-medium">
                Открытые порты
              </th>
              <th class="px-4 py-3 font-medium">
                <UButton
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  :icon="sortIcon('created_at')"
                  trailing
                  @click="setSort('created_at')"
                >
                  {{ sortLabels.created_at }}
                </UButton>
              </th>
              <th class="px-4 py-3 font-medium">
                <UButton
                  color="neutral"
                  variant="ghost"
                  size="xs"
                  :icon="sortIcon('updated_at')"
                  trailing
                  @click="setSort('updated_at')"
                >
                  {{ sortLabels.updated_at }}
                </UButton>
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
      :title="hostTableState.search ? 'Ничего не найдено' : 'Хостов пока нет'"
    />

    <div
      v-if="hostTableState.total"
      class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
    >
      <p class="text-sm text-muted">
        {{ rangeStart }}-{{ rangeEnd }} из {{ hostTableState.total }}
      </p>
      <div class="flex flex-wrap items-center gap-2">
        <select
          class="h-9 rounded-md border border-default bg-default px-3 text-sm text-highlighted"
          :value="hostTableState.pageSize"
          :disabled="hostsLoading"
          @change="setPageSize"
        >
          <option
            v-for="pageSize in pageSizeOptions"
            :key="pageSize"
            :value="pageSize"
          >
            {{ pageSize }}
          </option>
        </select>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-chevron-left"
          :disabled="hostTableState.page <= 1 || hostsLoading"
          @click="setPage(hostTableState.page - 1)"
        />
        <span class="min-w-20 text-center text-sm text-muted">
          {{ hostTableState.page }} / {{ hostPageCount }}
        </span>
        <UButton
          color="neutral"
          variant="ghost"
          icon="i-lucide-chevron-right"
          :disabled="hostTableState.page >= hostPageCount || hostsLoading"
          @click="setPage(hostTableState.page + 1)"
        />
      </div>
    </div>
  </section>
</template>

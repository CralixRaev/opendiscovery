<script setup lang="ts">
import type { DiscoveredHost } from '~/composables/useOpenDiscoveryDashboard'

const props = defineProps<{
  hosts: DiscoveredHost[]
  hostsLoading: boolean
  loadHosts: () => Promise<void>
}>()

type HostChartPoint = {
  key: string
  label: string
  count: number
}

type PortChartPoint = {
  key: string
  label: string
  count: number
}

const dayFormatter = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: 'short'
})

function startOfDay(date: Date) {
  const value = new Date(date)
  value.setHours(0, 0, 0, 0)
  return value
}

function dayKey(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const hostChartData = computed<HostChartPoint[]>(() => {
  const today = startOfDay(new Date())
  const days = Array.from({ length: 31 }, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() - (30 - index))
    return date
  })

  const countsByDay = new Map(days.map(date => [dayKey(date), 0]))
  const firstDay = days[0] ?? today

  for (const host of props.hosts) {
    const discoveredAt = startOfDay(new Date(host.created_at))

    if (discoveredAt < firstDay || discoveredAt > today) {
      continue
    }

    const key = dayKey(discoveredAt)
    countsByDay.set(key, (countsByDay.get(key) ?? 0) + 1)
  }

  return days.map((date) => {
    const key = dayKey(date)
    return {
      key,
      label: dayFormatter.format(date).replace('.', ''),
      count: countsByDay.get(key) ?? 0
    }
  })
})

const maxHostCount = computed(() => Math.max(...hostChartData.value.map(point => point.count), 1))

const portChartData = computed<PortChartPoint[]>(() => {
  const ports = new Map<number, { count: number, services: Set<string> }>()

  for (const host of props.hosts) {
    for (const port of host.open_ports) {
      const current = ports.get(port.number) ?? { count: 0, services: new Set<string>() }
      current.count += 1

      if (port.service_name) {
        current.services.add(port.service_name)
      }

      ports.set(port.number, current)
    }
  }

  return Array.from(ports.entries())
    .map(([number, value]) => {
      const services = Array.from(value.services).sort()
      const serviceLabel = services.length === 1 ? `/${services[0]}` : ''

      return {
        key: String(number),
        label: `${number}${serviceLabel}`,
        count: value.count
      }
    })
    .sort((first, second) => second.count - first.count || Number(first.key) - Number(second.key))
    .slice(0, 5)
})

const maxPortCount = computed(() => Math.max(...portChartData.value.map(point => point.count), 1))
const totalOpenPorts = computed(() => props.hosts.reduce((sum, host) => sum + host.open_ports.length, 0))
</script>

<template>
  <section>
    <div class="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
      <div class="rounded-lg border border-default bg-default">
        <div class="flex items-center justify-between gap-3 border-b border-default px-4 py-3">
          <div class="min-w-0">
            <h2 class="text-base font-semibold text-highlighted">
              Хосты по дням
            </h2>
            <p class="mt-1 text-sm text-muted">
              Последние 31 день
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

        <div class="overflow-x-auto px-4 py-5">
          <div class="flex h-52 min-w-[720px] items-end gap-2">
            <div
              v-for="point in hostChartData"
              :key="point.key"
              class="flex h-full min-w-0 flex-1 flex-col items-center justify-end gap-2"
              :title="`${point.label}: ${point.count}`"
            >
              <span class="text-xs font-medium text-muted">
                {{ point.count }}
              </span>
              <div class="flex h-36 w-full items-end rounded bg-muted/50">
                <div
                  class="w-full rounded bg-primary transition-[height]"
                  :style="{ height: `${Math.max((point.count / maxHostCount) * 100, point.count ? 8 : 0)}%` }"
                />
              </div>
              <span class="w-12 truncate text-center text-xs text-muted">
                {{ point.label }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-lg border border-default bg-default">
        <div class="flex items-center justify-between gap-3 border-b border-default px-4 py-3">
          <div class="min-w-0">
            <h2 class="text-base font-semibold text-highlighted">
              ТОП-5 портов
            </h2>
            <p class="mt-1 text-sm text-muted">
              {{ totalOpenPorts }} открытых портов
            </p>
          </div>
          <UIcon
            name="i-lucide-network"
            class="size-5 shrink-0 text-muted"
          />
        </div>

        <div class="px-4 py-5">
          <div
            v-if="portChartData.length"
            class="space-y-4"
          >
            <div
              v-for="point in portChartData"
              :key="point.key"
              class="grid grid-cols-[5.5rem_minmax(0,1fr)_2.5rem] items-center gap-3"
              :title="`${point.label}: ${point.count}`"
            >
              <span class="truncate font-mono text-sm font-medium text-highlighted">
                {{ point.label }}
              </span>
              <div class="h-3 overflow-hidden rounded bg-muted/50">
                <div
                  class="h-full rounded bg-primary transition-[width]"
                  :style="{ width: `${Math.max((point.count / maxPortCount) * 100, 6)}%` }"
                />
              </div>
              <span class="text-right text-sm font-medium text-muted">
                {{ point.count }}
              </span>
            </div>
          </div>

          <UAlert
            v-else
            color="neutral"
            variant="subtle"
            icon="i-lucide-circle-slash"
            title="Портов пока нет"
          />
        </div>
      </div>
    </div>
  </section>
</template>

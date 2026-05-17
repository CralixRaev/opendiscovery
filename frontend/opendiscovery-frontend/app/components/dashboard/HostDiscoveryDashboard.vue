<script setup lang="ts">
import type { Options, SeriesBarOptions, SeriesColumnOptions } from 'highcharts'
import type { DiscoveredHost } from '~/composables/useOpenDiscoveryDashboard'

import HighchartsChart from './HighchartsChart.client.vue'

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

const totalOpenPorts = computed(() => props.hosts.reduce((sum, host) => sum + host.open_ports.length, 0))

const chartTextColor = '#64748b'
const chartGridColor = 'rgba(148, 163, 184, 0.22)'
const chartPrimaryColor = '#00A155'

const baseChartOptions: Options = {
  accessibility: {
    enabled: false
  },
  chart: {
    backgroundColor: 'transparent',
    spacing: [8, 8, 8, 8],
    style: {
      fontFamily: 'inherit'
    }
  },
  credits: {
    enabled: false
  },
  legend: {
    enabled: false
  },
  title: {
    text: undefined
  },
  tooltip: {
    backgroundColor: '#0f172a',
    borderColor: '#1e293b',
    borderRadius: 6,
    shadow: false,
    style: {
      color: '#f8fafc',
      fontSize: '12px'
    }
  }
}

const hostChartOptions = computed<Options>(() => {
  const series: SeriesColumnOptions = {
    type: 'column',
    name: 'Хосты',
    data: hostChartData.value.map(point => point.count),
    color: chartPrimaryColor
  }

  return {
    ...baseChartOptions,
    chart: {
      ...baseChartOptions.chart,
      type: 'column',
      height: 208
    },
    xAxis: {
      categories: hostChartData.value.map(point => point.label),
      crosshair: {
        color: 'rgba(0, 161, 85, 0.12)'
      },
      lineColor: chartGridColor,
      tickColor: chartGridColor,
      labels: {
        autoRotation: [-45],
        style: {
          color: chartTextColor,
          fontSize: '11px'
        }
      }
    },
    yAxis: {
      allowDecimals: false,
      gridLineColor: chartGridColor,
      min: 0,
      title: {
        text: undefined
      },
      labels: {
        style: {
          color: chartTextColor,
          fontSize: '11px'
        }
      }
    },
    plotOptions: {
      column: {
        borderWidth: 0,
        borderRadius: 4,
        groupPadding: 0.06,
        pointPadding: 0.08
      },
      series: {
        animation: {
          duration: 180
        },
        states: {
          inactive: {
            opacity: 1
          }
        }
      }
    },
    tooltip: {
      ...baseChartOptions.tooltip,
      headerFormat: '<span>{point.key}</span><br/>',
      pointFormat: '<b>{point.y}</b> хостов'
    },
    series: [series]
  }
})

const portChartOptions = computed<Options>(() => {
  const series: SeriesBarOptions = {
    type: 'bar',
    name: 'Хосты',
    data: portChartData.value.map(point => point.count),
    color: chartPrimaryColor
  }

  return {
    ...baseChartOptions,
    chart: {
      ...baseChartOptions.chart,
      type: 'bar',
      height: 208
    },
    xAxis: {
      categories: portChartData.value.map(point => point.label),
      lineColor: chartGridColor,
      tickColor: chartGridColor,
      labels: {
        style: {
          color: chartTextColor,
          fontSize: '12px',
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace'
        }
      }
    },
    yAxis: {
      allowDecimals: false,
      gridLineColor: chartGridColor,
      min: 0,
      title: {
        text: undefined
      },
      labels: {
        style: {
          color: chartTextColor,
          fontSize: '11px'
        }
      }
    },
    plotOptions: {
      bar: {
        borderWidth: 0,
        borderRadius: 4,
        groupPadding: 0.14,
        pointPadding: 0.08
      },
      series: {
        animation: {
          duration: 180
        },
        dataLabels: {
          enabled: true,
          allowOverlap: false,
          crop: false,
          overflow: 'allow',
          style: {
            color: chartTextColor,
            fontSize: '12px',
            fontWeight: '600',
            textOutline: 'none'
          }
        },
        states: {
          inactive: {
            opacity: 1
          }
        }
      }
    },
    tooltip: {
      ...baseChartOptions.tooltip,
      headerFormat: '<span>Порт {point.key}</span><br/>',
      pointFormat: '<b>{point.y}</b> хостов'
    },
    series: [series]
  }
})
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
          <HighchartsChart
            class="h-52 min-w-[720px]"
            :options="hostChartOptions"
          />
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
          <HighchartsChart
            v-if="portChartData.length"
            class="h-52"
            :options="portChartOptions"
          />

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

<script setup lang="ts">
import Highcharts from 'highcharts'
import type { Chart, Options } from 'highcharts'

const props = defineProps<{
  options: Options
}>()

const chartElement = ref<HTMLElement | null>(null)
let chart: Chart | null = null

function syncChart() {
  if (!chartElement.value) {
    return
  }

  if (chart) {
    chart.update(props.options, true, true)
    return
  }

  chart = Highcharts.chart(chartElement.value, props.options)
}

onMounted(syncChart)

watch(
  () => props.options,
  () => syncChart(),
  { deep: true }
)

onBeforeUnmount(() => {
  chart?.destroy()
  chart = null
})
</script>

<template>
  <div ref="chartElement" />
</template>

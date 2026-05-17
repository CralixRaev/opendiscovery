<script setup lang="ts">
useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

const title = 'OpenDiscovery'
const description = 'OpenDiscovery application'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description
})
</script>

<template>
  <UApp>
    <div class="min-h-dvh bg-default text-default">
      <header class="border-b border-default">
        <div class="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
          <NuxtLink
            to="/"
            class="flex items-center gap-3 font-semibold"
          >
            <AppLogo class="h-6 w-auto shrink-0" />
            <span>OpenDiscovery</span>
          </NuxtLink>

          <UColorModeButton />
        </div>
      </header>

      <NuxtPage />
    </div>
  </UApp>
</template>

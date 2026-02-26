<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  // Remove the static HTML boot loader once Vue has mounted
  const bootLoader = document.getElementById('gridlog-boot')
  if (bootLoader) {
    // Add a quick fade out transition
    bootLoader.style.transition = 'opacity 0.4s ease'
    bootLoader.style.opacity = '0'
    
    // Remove from DOM after fade completes
    setTimeout(() => {
      bootLoader.remove()
    }, 400)
  }
})
</script>
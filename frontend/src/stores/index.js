import { createPinia } from 'pinia'

export default function (/* { ssrContext } */) {
  const pinia = createPinia()

  return pinia
}
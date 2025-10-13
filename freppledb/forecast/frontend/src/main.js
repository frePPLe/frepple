import { createApp } from 'vue'
import App from './App.vue'
import { createPinia } from "pinia";
import { i18n } from '@/i18n/i18n.js'

const app = createApp(App);
app.use(i18n);
app.use(createPinia());
if (import.meta.env.DEV) {
  app.config.devtools = true;
  app.config.performance = true;
}
app.mount('#app');

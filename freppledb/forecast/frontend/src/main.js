import { createApp } from 'vue'
import App from './App.vue'
import { createPinia } from "pinia";
import { i18n } from '@/i18n/i18n.js'
import { tooltip } from '@common/directives/tooltip.js'

const app = createApp(App);
app.use(i18n);
app.use(createPinia());
app.directive('tooltip', tooltip);
if (import.meta.env.DEV) {
  app.config.devtools = true;
  app.config.performance = true;
}
app.mount('#app');

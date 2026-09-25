/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

import { createApp } from 'vue';
import App from './App.vue';
import { createPinia } from 'pinia';
import { i18n } from '@/i18n/i18n.js';
import { tooltip } from '@common/directives/tooltip.js';

const app = createApp(App);
app.use(i18n);
app.use(createPinia());
app.directive('tooltip', tooltip);
if (import.meta.env.DEV) {
  app.config.devtools = true;
  app.config.performance = true;
}
const mountApp = () => {
  const doMount = () => {
    // Favorite wrappers (grid.getGridConfig + favorite.open) are provided by
    // the grunt-built frepple-favoritewidgets bundle loaded by the template,
    // so there is nothing to install here.
    app.mount('#app');
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', doMount);
  } else {
    doMount();
  }
};

mountApp();

/*
 * Copyright (C) 2026 by frePPLe bv
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
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE* or in the form of compiled binaries.
 */

import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite';
import vueDevTools from 'vite-plugin-vue-devtools';
import { resolve, dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// https://vite.dev/config/
export default defineConfig({
  server: {
    // Allow any host to enable proper integration with Django
    host: '0.0.0.0',
    origin: 'http://localhost:5173', // Add this line
    // Enable CORS during development
    cors: true,
    hmr: {
      protocol: 'ws',
      host: 'localhost',
    },
  },
  build: {
    outDir: '../static',
    assetsDir: '../static',
    emptyOutDir: false,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
      output: {
        entryFileNames: 'input/[name].js',
        chunkFileNames: 'input/[name].js',
        assetFileNames: '[name].[ext]',
      },
    },
  },
  plugins: [
    vue(),
    VueI18nPlugin({
      include: resolve(__dirname, './src/i18n/translations/*.json'),
      runtimeOnly: false,
      fullInstall: true,
      forceStringify: false,
    }),
    process.env.NODE_ENV !== 'production' && vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@input': fileURLToPath(new URL('./src', import.meta.url)),
      vue: 'vue/dist/vue.esm-bundler.js',
      '@common': fileURLToPath(new URL('../../common/frontend/src', import.meta.url)),
      '@translations': fileURLToPath(new URL('src/translations', import.meta.url)),
    },
  },
  base: '/static/', // This ensures assets are loaded from the correct path
  css: {
    modules: {
      scopeBehaviour: 'local',
    },
  },
});

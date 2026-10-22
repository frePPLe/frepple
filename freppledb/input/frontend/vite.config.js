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
import { resolve, dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// https://vite.dev/config/
// The "debug" mode builds an unminified bundle, used when the DEBUG_JS
// setting is enabled. The minified bundle is used in all other cases.
export default defineConfig(({ mode }) => {
  const debug = mode === 'debug';
  const suffix = debug ? '.debug' : '';
  return {
    build: {
      outDir: '../static',
      assetsDir: '../static',
      // Don't delete the other variant of the bundle
      emptyOutDir: false,
      minify: !debug,
      sourcemap: debug,
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html'),
        },
        output: {
          entryFileNames: `input/[name]${suffix}.js`,
          chunkFileNames: `input/[name]${suffix}.js`,
          assetFileNames: `[name]${suffix}.[ext]`,
          // Wrap the debug bundle in a function, so its top level declarations
          // don't overwrite the globals of the page (window.addEventListener)
          // and don't collide with the variables of the inline scripts.
          // The bundle stays a classic script: d3 reads "this.document" and
          // needs the sloppy mode of a script, not the strict mode of a module.
          intro: debug ? '(function () {' : '',
          outro: debug ? '})();' : '',
          // Keep the debug bundle a single file, so the wrapper above encloses
          // all of the code.
          inlineDynamicImports: debug,
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
  };
});

import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite'
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
          main: resolve(__dirname, 'index.html')
        },
        output: {
          entryFileNames: `forecast/[name]${suffix}.js`,
          chunkFileNames: `forecast/[name]${suffix}.js`,
          assetFileNames: `[name]${suffix}.[ext]`
        }
      }
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
        '@common': fileURLToPath(new URL('../../common/frontend/src', import.meta.url)),
        '@translations': fileURLToPath(new URL('src/translations', import.meta.url))
      },
    },
    base: '/static/', // This ensures assets are loaded from the correct path
    css: {
      modules: {
        scopeBehaviour: 'local'
      }
    }
  }
})

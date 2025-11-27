import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import VueI18nPlugin from '@intlify/unplugin-vue-i18n/vite'
import vueDevTools from 'vite-plugin-vue-devtools'
import { resolve, dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// https://vite.dev/config/
export default defineConfig(
  {
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
      emptyOutDir: true,
      rollupOptions: {
        input: {
          main: resolve(__dirname, 'index.html')
        },
        output: {
          entryFileNames: 'input/[name].js',
          chunkFileNames: 'input/[name].js',
          assetFileNames: '[name].[ext]'
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
      vueDevTools(),
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
)




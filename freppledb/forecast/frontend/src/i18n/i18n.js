/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * All information contained herein is, and remains the property of frePPLe.
 * You are allowed to use and modify the source code, as long as the software is used
 * within your company.
 * You are not allowed to distribute the software, either in the form of source code
 * or in the form of compiled binaries.
 */

import { createI18n } from 'vue-i18n'
import messages from '@intlify/unplugin-vue-i18n/messages'

// Create i18n instance - IMPORTANT CHANGES HERE
export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: document.documentElement.lang,
  fallbackLocale: 'en',
  messages,
  missingWarn: false,
  fallbackWarn: false,
  silentTranslationWarn: true
})

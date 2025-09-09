// freppledb/quoting/frontend/src/i18n/i18n.js
import { createI18n } from 'vue-i18n'
import { getDjangoTemplateVariable } from '@common/utils.js'
import messages from '@intlify/unplugin-vue-i18n/messages'

// Get Django language using a more robust approach
function getCurrentLanguage() {
  // Try to get language from Django template variables first
  const djangoLanguageCode = getDjangoTemplateVariable('LANGUAGE_CODE')?.value

  // Next try the HTML lang attribute
  const htmlLang = document.documentElement.lang

  // Try to get language from cookie
  const getCookieValue = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }
  const cookieLang = getCookieValue('django_language')

  // Fallbacks
  const navLang = navigator.language

  // Log all detected languages for debugging
  console.log('Django LANGUAGE_CODE variable:', djangoLanguageCode)
  console.log('HTML lang attribute:', htmlLang)
  console.log('Django language cookie:', cookieLang)
  console.log('Browser language:', navLang)

  // Determine which language to use, in priority order
  const detectedLang = djangoLanguageCode || htmlLang || cookieLang || navLang || 'en-us'
  console.log('Detected language before normalization:', detectedLang)

  // Normalize the language code (convert fr_FR to fr-fr, FR to fr, etc.)
  let normalizedLang = detectedLang.toLowerCase().replace('_', '-')

  // If we have a language code like 'fr', check if we have 'fr.json' or need to fall back to 'fr-fr.json'
  const availableLocales = Object.keys(messages)
  console.log('64 Available locales:', availableLocales)

  if (!availableLocales.includes(normalizedLang)) {
    // For simple codes like 'fr', try to find a matching 'fr-*' variant
    if (normalizedLang.length === 2) {
      const matchingLocale = availableLocales.find(locale =>
        locale.startsWith(normalizedLang + '-')
      )

      if (matchingLocale) {
        console.log(`Found matching locale ${matchingLocale} for ${normalizedLang}`)
        normalizedLang = matchingLocale
      }
    }
    // For complex codes like 'fr-fr', try the simple variant 'fr'
    else if (normalizedLang.includes('-')) {
      const simpleCode = normalizedLang.split('-')[0]
      if (availableLocales.includes(simpleCode)) {
        console.log(`Falling back to simple locale ${simpleCode} from ${normalizedLang}`)
        normalizedLang = simpleCode
      }
    }
  }

  if (!availableLocales.includes(normalizedLang)) {
    console.warn(`No matching locale found for ${normalizedLang}, falling back to default`);
    normalizedLang = availableLocales[0] || 'en-us';
  }

  console.log('Final language for i18n:', normalizedLang);
  return normalizedLang
}

const detectedLocale = getCurrentLanguage();
console.log('Current language for i18n:', detectedLocale);

// Create i18n instance - IMPORTANT CHANGES HERE
export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: detectedLocale,
  fallbackLocale: 'en',
  messages,
  missingWarn: false,
  fallbackWarn: false,
  silentTranslationWarn: true
})


// Log the complete i18n instance config
console.log('i18n instance created with:', {
  locale: i18n.global.locale.value,
  availableLocales: i18n.global.availableLocales,
  fallbackLocale: i18n.global.fallbackLocale.value,
  messageCount: Object.keys(i18n.global.messages.value).length,
})

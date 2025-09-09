// extract-vue-translations.js
const fs = require('fs');
const path = require('path');
const glob = require('glob');

// Define Vue apps to extract translations from
const vueApps = [
  'quoting',
  // Add other Vue app names here
];

// Process each Vue app
vueApps.forEach(appName => {
  console.log(`Processing ${appName} app...`);

  // Create output directory if it doesn't exist
  const outputDir = path.resolve(__dirname, `freppledb/${appName}/static/${appName}/i18n`);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Find all Vue and JS files
  const vueFiles = glob.sync(`freppledb/${appName}/frontend/src/**/*.vue`);
  const jsFiles = glob.sync(`freppledb/${appName}/frontend/src/**/*.js`);

  if (vueFiles.length === 0 && jsFiles.length === 0) {
    console.log(`No Vue or JS files found in ${appName} app.`);
    return;
  }

  console.log(`Found ${vueFiles.length} Vue files and ${jsFiles.length} JS files in ${appName} app.`);

  // Extract translations manually using regex
  const translations = new Set();

  // Process function to extract $t calls
  const processFile = (file) => {
    try {
      const content = fs.readFileSync(file, 'utf8');

      // Find all $t('...') and $t("...") calls in the file
      const tSingleQuoteRegex = /\$t\(\s*'([^']+)'\s*\)/g;
      const tDoubleQuoteRegex = /\$t\(\s*"([^"]+)"\s*\)/g;

      let match;

      while ((match = tSingleQuoteRegex.exec(content)) !== null) {
        if (match[1]) {
          translations.add(match[1]);
        }
      }

      while ((match = tDoubleQuoteRegex.exec(content)) !== null) {
        if (match[1]) {
          translations.add(match[1]);
        }
      }
    } catch (e) {
      console.error(`Error processing file ${file}: ${e.message}`);
    }
  };

  // Process all Vue files
  vueFiles.forEach(processFile);

  // Process all JS files
  jsFiles.forEach(processFile);

  // Create POT file
  let potContent = `# Translations for ${appName} Vue app
msgid ""
msgstr ""
"Project-Id-Version: frepple-${appName}\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"MIME-Version: 1.0\\n"

`;

  // Add each translation string
  translations.forEach(text => {
    // Escape quotes in the msgid
    const escapedText = text.replace(/"/g, '\\"');
    potContent += `\nmsgid "${escapedText}"\nmsgstr ""\n`;
  });

  // Write the POT file
  fs.writeFileSync(`${outputDir}/vue-messages.pot`, potContent);

  console.log(`Extracted ${translations.size} strings from ${appName} app.`);
});
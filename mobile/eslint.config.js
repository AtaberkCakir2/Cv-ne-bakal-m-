// Expo'nun önerdiği kurallar (React, React Hooks, TypeScript). Üretilen API tipleri denetlenmez.
const { defineConfig } = require("eslint/config");
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([
  expoConfig,
  { ignores: ["dist/*", "src/api/schema.d.ts"] },
  // Türkçe metinlerde kesme işareti çok (CV'ni, Cv'ne Bakalım!); React Native metninde HTML kaçışı gerekmez.
  { rules: { "react/no-unescaped-entities": "off" } },
]);

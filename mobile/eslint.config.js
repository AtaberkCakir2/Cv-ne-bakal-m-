// Expo'nun önerdiği kurallar (React, React Hooks, TypeScript). Üretilen API tipleri denetlenmez.
const { defineConfig } = require("eslint/config");
const expoConfig = require("eslint-config-expo/flat");

module.exports = defineConfig([expoConfig, { ignores: ["dist/*", "src/api/schema.d.ts"] }]);

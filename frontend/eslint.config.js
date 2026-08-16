import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import { globalIgnores } from "eslint/config";

export default tseslint.config([
  globalIgnores(["dist", "dev-dist"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      // v7 moved the flat-config presets under `configs.flat`; the
      // top-level ones are still the legacy array format ESLint 10 rejects.
      reactHooks.configs.flat["recommended-latest"],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
    },
  },
  {
    // Routes must export a `Route` alongside their component, and these
    // directories deliberately co-locate helpers with the components that
    // use them — fast refresh granularity is not worth splitting them up.
    files: [
      "src/components/**/*.{ts,tsx}",
      "src/contexts/**/*.{ts,tsx}",
      "src/routes/**/*.{ts,tsx}",
    ],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
]);

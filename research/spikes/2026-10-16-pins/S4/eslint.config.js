import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { files: ["src/**/*.ts"] },
  eslint.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);

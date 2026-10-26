import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';

const pagesBase = process.env.PAGES_BASE_PATH ?? '/depi_gapAnalyzer/';

export default defineConfig({
  plugins: [react()],
  base: `${pagesBase.replace(/\/$/, '')}/`,
  build: {target: 'es2022'},
});

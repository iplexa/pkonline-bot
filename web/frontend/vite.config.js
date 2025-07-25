import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build', // чтобы совпадало с CRA и nginx
  },
  server: {
    port: 3000,
  },
}); 
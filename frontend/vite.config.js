import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/hiring': 'http://localhost:8000',
      '/ats': 'http://localhost:8000',
      '/jds': 'http://localhost:8000',
      '/resumes': 'http://localhost:8000',
      '/health': 'http://localhost:8000'
    }
  }
});

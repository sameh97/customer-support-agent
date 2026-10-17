import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev, forward API calls to the FastAPI server (uvicorn on :8000).
// In production FastAPI serves the built files itself, so no proxy is needed.
const api = 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/chat': api,
      '/info': api,
      '/health': api,
      '/reset': api,
    },
  },
})

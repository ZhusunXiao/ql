import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    vue(),
    // Custom plugin: serve any file via /file/ path
    {
      name: 'serve-file',
      configureServer(server) {
        server.middlewares.use('/file', (req, res, next) => {
          // URL format: /file/D:/path/to/file.json or /file//server/share/file.json (UNC)
          let filePath = decodeURIComponent(req.url || '').slice(1) // Remove leading /
          
          // Handle UNC paths: //server/share -> \\server\share
          if (filePath.startsWith('/')) {
            filePath = filePath.replace(/\//g, '\\')
          }
          
          if (fs.existsSync(filePath)) {
            const content = fs.readFileSync(filePath, 'utf-8')
            res.setHeader('Content-Type', 'application/json')
            res.setHeader('Access-Control-Allow-Origin', '*')
            res.end(content)
          } else {
            res.statusCode = 404
            res.end(`File not found: ${filePath}`)
          }
        })
      }
    }
  ],
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  server: {
    fs: {
      allow: ['..', '.']
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  },
  publicDir: 'public'
})

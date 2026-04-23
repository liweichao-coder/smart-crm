import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './assets/vendor/app.D-2dUJor.css'
import './assets/vendor/2.rN8r_Hzv.css'
import './assets/vendor/AppSidebar.4WoY9BJz.css'
import './assets/vendor/Pagination.CydPSkQ3.css'
import './assets/vendor/select-trigger.CV-KWLNP.css'
import './assets/vendor/KanbanBoard.CWwWJICF.css'
import './assets/vendor/16.B5NMJ2OG.css'
import './assets/vendor/5.ZjqlBAcF.css'
import './index.css'
import App from './App.jsx'

document.documentElement.classList.add('dark')
document.documentElement.lang = 'zh-CN'
document.documentElement.style.colorScheme = 'dark'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)

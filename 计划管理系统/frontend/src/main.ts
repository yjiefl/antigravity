import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// 安装 Pinia
app.use(createPinia())

// 安装 Router
app.use(router)

// 挂载应用
app.mount('#app')

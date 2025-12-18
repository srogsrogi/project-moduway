import { createApp } from 'vue'
import vue3GoogleLogin from 'vue3-google-login'
import App from './App.vue'
import router from './router'

import './assets/styles/main.css'

const app = createApp(App)

app.use(router)

// Google Login 설정
app.use(vue3GoogleLogin, {
  clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID
})

app.mount('#app')
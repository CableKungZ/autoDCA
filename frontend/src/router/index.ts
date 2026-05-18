import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Plans from '../views/Plans.vue'
import Orders from '../views/Orders.vue'
import Settings from '../views/Settings.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/plans', component: Plans },
    { path: '/orders', component: Orders },
    { path: '/settings', component: Settings },
  ],
})

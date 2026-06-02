import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',        component: () => import('./views/Dashboard.vue') },
    { path: '/plans',   component: () => import('./views/Plans.vue') },
    { path: '/orders',  component: () => import('./views/Orders.vue') },
    { path: '/settings', component: () => import('./views/Settings.vue') },
  ],
})

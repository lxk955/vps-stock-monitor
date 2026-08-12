import { createRouter, createWebHistory } from 'vue-router'
import StockView from '@/views/StockView.vue'
import MySubscriptions from '@/views/MySubscriptions.vue'

const routes = [
  {
    path: '/',
    name: 'Stock',
    component: StockView,
  },
  {
    path: '/my-subscriptions',
    name: 'MySubscriptions',
    component: MySubscriptions,
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

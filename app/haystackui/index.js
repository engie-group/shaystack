import store from './store.js'
import router from './router.js'
import MyCustomPlugin from './plugins/customPlugin.js'
Vue.use(MyCustomPlugin)


Vue.use(Vuetify, {
  iconfont: 'mdi'
})
const vuetify = new Vuetify({})
const App = {
  el: 'main',
  router,
  store,
  vuetify
}

window.addEventListener('load', () => {
  new Vue(App)
})

/* eslint-disable */
const MyCustomPlugin = {
  install(Vue) {
    Vue.prototype.isPluginInstance = true,
    Vue.mixin({ mounted() { console.log('VUE INSTANCE')}})
  },
}

export default MyCustomPlugin

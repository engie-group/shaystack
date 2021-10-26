const MyCustomPlugin = {
  install(Vue) {
    Vue.prototype.customFilter = () => ['site', 'equip', 'site or equip', 'his']
  },
}

export default MyCustomPlugin

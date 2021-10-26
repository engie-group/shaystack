import VMainLayout from './views/VMainLayout/VMainLayout.js'
import VSummaryContent from './views/VSummaryContent/VSummaryContent.js'

export default new VueRouter({
  mode: 'history',
  routes: [
    {
      path: '*/haystack/',
      component: VMainLayout,
      children: [
        {
          path: '',
          name: 'summary',
          component: VSummaryContent
        }
      ]
    },
  ]
})
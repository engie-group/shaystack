const template = `
    <div class="filter-api-block__box">
      <div class="filter-api-block__box-description">
        <h4 class="filter-api-block__box-description__title">{{ title }}</h4>
        <div class="filter-api-block__box-description__tooltip">
          <div v-if="hasTooltips">
            <v-tooltip v-model="showExistingApi" right v-if="isFromPlugin">
              <template v-slot:activator="{ attrs }">
                 <v-btn small icon color="rgba(0,0,0,.87)" @click="showExistingApi = !showExistingApi" v-if="existingApiEndPointFromPlugin">
                   <v-icon icon v-bind="attrs">info</v-icon>
                </v-btn>
               </template>
                <div v-html="tooltipText" />
            </v-tooltip>
            <v-tooltip right v-else>
              <template v-slot:activator="{ on, attrs }">
                <v-icon icon v-bind="attrs" v-on="on">info</v-icon>
              </template>
              <div v-html="tooltipText" />
            </v-tooltip>
          </div>
        </div>
      </div>
      <template>
        <slot></slot>
      </template>
    </div>
`
export default {
  template,
  name: 'CFilterApiBlock',
  props: {
     title: {
        type: String,
        default: ''
     },
     hasTooltips: {
       type: Boolean,
       default: false
     },
      tooltipText: {
       type: String,
       default: ''
     },
     isFromPlugin: {
       type: Boolean,
       default: false
     }
   },
  data() {
    return {
      showExistingApi: false
    }
  },
  computed: {
    existingApiEndPointFromPlugin() {
      return this.getExistingApiEndpoint ? true : false
    }
  }
}



const template = `
<div class="main-layout">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,700,900" />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Material+Icons" />
  <v-app-bar app>
    <div class="d-flex align-center main-layout__bar">
      <v-img
        alt="Vuetify Logo"
        class="shrink mr-2"
        contain
        transition="scale-transition"
        width="90"
        disabled
      />
      <h2 class="main-layout__title">Haystack</h2>
    </div>
    <v-combobox
      class="main-layout__combobox"
      v-model="comboboxInput"
      :items="getApiServers"
      label="Add or Remove a targeted Endpoint API"
      dense
      outlined
      v-on:keyup.enter="updateAPI()"
    >
      <template
        v-slot:item="{
          item
        }"
      >
        <div class="main-layout__combobox-row">
          <span class="circle" :style="circleApiClass(item)"></span>
          <span class="pr-2 main-layout__combobox-api-text">
            {{ item }}
          </span>
          <v-icon size="28" class="material-icons main-layout__combobox-image" @click="changeApiServers(item)"
            >delete</v-icon
          >
        </div>
      </template>
    </v-combobox>
    <v-text-field
      class="summary-content__text-field"
      label="Filter"
      outlined
      :value="filterApi"
      dense
      background-color="white"
      @change="updateFilter($event)"
    />
    <v-spacer></v-spacer>
  </v-app-bar>
  <main>
    <router-view class="router-view" />
  </main>
</div>
`
import { API_COLORS } from '../../services/index.js'

export default {
  template,
  data() {
    return {
      comboboxInput: ''
    }
  },
  computed: {
    filterApi() {
      return this.$store.getters.filterApi
    },
    getApiServers() {
      return this.$store.getters.apiServers.map(apiServer => apiServer.haystackApiHost)
    }
  },
  methods: {
    isApiServerAlreadyExists(host) {
      return Boolean(this.$store.getters.apiServers.find(apiServer => apiServer.haystackApiHost === host))
    },
    async changeApiServers(haystackApiHost) {
      this.$store.commit('DELETE_HAYSTACK_API', { haystackApiHost })
      await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
      await this.$router.replace({ query: null }).catch(() => {})
      this.$router.push({ query: { filterApi: this.filterApi, apiServers: `["${this.getApiServers.join('","')}"]` } })
      this.comboboxInput = ''
    },
    async updateAPI() {
      const haystackApiHost = this.comboboxInput
      if (!this.isApiServerAlreadyExists(haystackApiHost)) {
        this.$store.dispatch('createApiServer', { haystackApiHost })
        await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
        await this.$router.replace({ query: null }).catch(() => {})
        this.$router.push({ query: { filterApi: this.filterApi, apiServers: `["${this.getApiServers.join('","')}"]` } })
        this.comboboxInput = ''
      }
    },
    async updateFilter(newFilter) {
      if (newFilter !== this.$store.getters.filterApi) {
        this.$store.commit('SET_FILTER_API', { filterApi: newFilter })
        await this.$router.replace({ query: null }).catch(() => {})
        this.$router.push({ query: { filterApi: newFilter, apiServers: `["${this.getApiServers.join('","')}"]` } })
        await this.$store.dispatch('reloadAllData', { entity: newFilter })
      }
    },
    circleApiClass(apiHost) {
      const apiNumber = this.$store.getters.apiServers.findIndex(apiServer => apiServer.haystackApiHost === apiHost)
      return `background: ${API_COLORS[apiNumber]};`
    }
  }
}

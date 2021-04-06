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
    <v-text-field
      class="summary-content__text-field"
      label="Filter"
      outlined
      :value="filterApi"
      dense
      background-color="white"
      @change="updateFilter($event)"
    />
    <div class="main-layout__tootltips">
      <v-tooltip bottom>
        <template v-slot:activator="{ on, attrs }">
          <v-icon icon v-bind="attrs" v-on="on">info</v-icon>
        </template>
        <h3>Filter Example:</h3>
        <span
          ><h4>site or equip</h4>
          find site or equipment entities<br />
          <h4>(not his)</h4>
          find entities with no histories<br />
          <h4>curVal > 10</h4>
          find all entities with a curval > 10<br />
          <h4>occupiedEnd >= 18:00 and geoCity == "Richmond"</h4>
          find all entities that close after 6 p.m. in Richmond<br />
          <h4>point and siteRef->geoCountry == "US"</h4>
          find all the point based in US
        </span>
      </v-tooltip>
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
      class="summary-content__text-field__date"
      label="Select start date"
      outlined
      v-model="dateStartInput"
      :value="startDateRange"
      dense
      background-color="white"
      @change="updateStartDateRange($event)"
    />
    <v-text-field
      class="summary-content__text-field__date"
      label="Select end date"
      outlined
      v-model="dateEndInput"
      :value="endDateRange"
      dense
      background-color="white"
      @change="updateEndDateRange($event)"
    />
    <div class="main-layout__tootltips">
      <v-tooltip bottom>
        <template v-slot:activator="{ on, attrs }">
          <v-icon icon v-bind="attrs" v-on="on">info</v-icon>
        </template>
        <h4>
          Date Example:
        </h4>
        <span
          ><li>today</li>
          <li>yesterday</li>
          <li>2020-01-01</li>
          <li>2020/01/01</li>
          <li>2020-01-01T12:00:00.00Z</li>
        </span>
      </v-tooltip>
    </div>
    <v-spacer></v-spacer>
  </v-app-bar>
  <main>
    <router-view class="router-view" />
  </main>
</div>
`
import { API_COLORS, dataUtils, formatService } from '../../services/index.js'
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
    startDateRange() {
      const filterDateStart = this.$store.getters.dateRange.start === '' ? null : this.$store.getters.dateRange.start
      // eslint-disable-next-line
      this.dateStartInput = filterDateStart
      return filterDateStart
    },
    endDateRange() {
      const filterEndDate = this.$store.getters.dateRange.end === '' ? null : this.$store.getters.dateRange.end
      // eslint-disable-next-line
      this.dateEndInput = filterEndDate
      return filterEndDate
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
      if (this.getApiServers.length > 0) {
        await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
      }
      const { q } = this.$route.query
      if (this.getApiServers.length > 0) this.$router.push({ query: { q, a: `["${this.getApiServers.join('","')}"]` } })
      else this.$router.push({ query: { q } })
      this.comboboxInput = ''
    },
    async updateAPI() {
      const haystackApiHost = this.comboboxInput
      if (!this.isApiServerAlreadyExists(haystackApiHost)) {
        const apiServersBeforeAdd = this.getApiServers.slice()
        await this.$store.dispatch('createApiServer', { haystackApiHost })
        await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
        if (JSON.stringify(this.getApiServers) !== JSON.stringify(apiServersBeforeAdd)) {
          const { q } = this.$route.query
          const { hash } = this.$route
          this.$router.push({ hash, query: { q, a: `["${this.getApiServers.join('","')}"]` } })
        }
        this.comboboxInput = ''
      }
    },
    async updateFilter(newFilter) {
      if (newFilter !== this.$store.getters.filterApi) {
        this.$store.commit('SET_FILTER_API', { filterApi: newFilter })
        const { a, d } = this.$route.query
        this.$router.push({ query: { q: newFilter, a, d } })
        await this.$store.dispatch('reloadAllData', { entity: newFilter })
      }
    },
    async updateStartDateRange(newStartDate) {
      const startDateRange = !newStartDate || newStartDate === '' ? '' : dataUtils.checkDateFormat(newStartDate)
      if (newStartDate !== this.startDateRange) {
        if (startDateRange || startDateRange === '') {
          if (formatService.checkDateRangeIsCorrect(startDateRange, this.endDateRange)) {
            this.$store.commit('SET_START_DATE_RANGE', { startDateRange })
            const { a, q } = this.$route.query
            if ((!this.endDateRange || this.endDateRange === '') && startDateRange === '') {
              this.$router.push({ query: { q, a } })
            } else if ((startDateRange === 'today' || startDateRange === 'yesterday') && !this.endDateRange)
              this.$router.push({
                query: { q, a, d: `${startDateRange}` }
              })
            else
              this.$router.push({
                query: { q, a, d: `${startDateRange},${this.endDateRange ? this.endDateRange : ''}` }
              })
          } else alert('Begin Date should be smaller than end Date')
        } else {
          this.dateStartInput = this.startDateRange
          alert('Wrong format Date')
        }
      }
    },
    async updateEndDateRange(newEndDate) {
      const endDateRange = !newEndDate || newEndDate === '' ? '' : dataUtils.checkDateFormat(newEndDate)
      if (newEndDate !== this.endDateRange) {
        if (endDateRange || endDateRange === '') {
          if (formatService.checkDateRangeIsCorrect(this.startDateRange, endDateRange)) {
            this.$store.commit('SET_END_DATE_RANGE', { endDateRange })
            const { a, q } = this.$route.query
            if ((!this.startDateRange || this.startDateRange === '') && endDateRange === '')
              this.$router.push({ query: { q, a } })
            else if ((endDateRange === 'today' || endDateRange === 'yesterday') && !this.startDateRange)
              this.$router.push({
                query: { q, a, d: `${endDateRange}` }
              })
            else
              this.$router.push({
                query: { q, a, d: `${this.startDateRange ? this.startDateRange : ''},${endDateRange}` }
              })
          } else alert('Begin Date should be smaller than end Date')
        } else {
          this.dateEndInput = this.endDateRange
          alert('Wrong format Date')
        }
      }
    },
    circleApiClass(apiHost) {
      const apiNumber = this.$store.getters.apiServers.findIndex(apiServer => apiServer.haystackApiHost === apiHost)
      return `background: ${API_COLORS[apiNumber]};`
    }
  }
}

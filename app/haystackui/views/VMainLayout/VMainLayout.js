const template = `
    <div class="main-layout" :class="{ 'main-layout__extended': isExtended, 'main-layout__not-extended': !isExtended }">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,700,900" />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Material+Icons" />
    <v-app-bar app class="main-layout__headers" v-if="isExtended">
      <div class="main-layout__app-bar">
        <div class="d-flex align-center main-layout__bar">
          <v-img
            alt="Vuetify Logo"
            class="shrink mr-2"
            contain
            src="https://raw.githubusercontent.com/engie-group/shaystack/develop/docs/logo.png"
            transition="scale-transition"
            width="90"
            disabled
          />
          <h2 class="main-layout__title">Shift For Haystack</h2>
          <v-btn color="grey" icon dark @click.native="changeExtention()">
            <v-icon>mdi-format-list-bulleted-square</v-icon>
          </v-btn>
        </div>
        <c-filter-api-block
          title="Add a target API Endpoint"
          :hasTooltips="existingApiEndPointFromPlugin"
          :isFromPlugin=true
          :tooltipText=existingApiFromPluginText()
        >
          <div class="main-layout__input-combobox">
            <v-combobox
              class="main-layout__combobox"
              height="40px"
              width="30%"
              v-model="comboboxInput"
              :items="getApiServers"
              label="API Endpoint"
              dense
              outlined
              v-on:keyup.enter="updateAPI()"
              hide-details
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
          </div>
        </c-filter-api-block>
        <c-filter-api-block title="Query with filter" :hasTooltips=true :tooltipText=filterEntityTooltipText()>
          <v-combobox
            height="40px"
            width="80%"
            class="main-layout__text-field"
            label="Filter"
            outlined
            :value="filterApi"
            dense
            background-color="white"
            :items="getBasicFilter()"
            @change="updateFilter($event)"
            append-icon=""
            hide-details
          >
              <template
                v-slot:item="{
                  item
                }"
              >
                <div class="main-layout__combobox-row">
                  <span class="pr-2 main-layout__combobox-api-text">
                    {{ item }}
                  </span>
                </div>
              </template>
            </v-combobox>
        </c-filter-api-block>
        <c-filter-api-block title="Enable Navigation Mode">
            <v-switch
              v-model="isNavigationModeActivated"
              :label="getNavigationModeInformation" />
        </c-filter-api-block>
        <c-filter-api-block title="Select your date range" :hasTooltips=true :tooltipText=dateRangeTooltipsText()>
          <v-text-field
            height="40px"
            class="main-layout__text-field main-layout__text-field__date"
            label="Select start date"
            outlined
            v-model="dateStartInput"
            :value="startDateRange"
            dense
            background-color="white"
            @change="updateStartDateRange($event)"
            hide-details
          />
          <v-text-field
            height="40px"
            class="main-layout__text-field main-layout__text-field__date"
            label="Select end date"
            outlined
            v-model="dateEndInput"
            :value="endDateRange"
            dense
            background-color="white"
            @change="updateEndDateRange($event)"
            hide-details
          />
        </c-filter-api-block>
        <c-filter-api-block title="Enable link labels">
            <v-switch
              v-model="isLinkNameDisplayed"
              :label="getLinkNameDisplayedInformation" />
        </c-filter-api-block>
        <c-filter-api-block title="Select link types to display">
          <v-select
            v-model="activatedLinks"
            :items="linkEntities"
            multiple
            label="Select link types"
            hint="Select links between entities"
            :menu-props="{ bottom: true, offsetY: true }"
          >
            <template v-slot:selection="{ item, index }">
              <v-chip v-if="index === 0">
                <span>{{ item }}</span>
              </v-chip>
              <span
                v-if="index === 1"
                class="grey--text text-caption"
              >
                (+{{ activatedLinks.length - 1 }} others)
              </span>
            </template>
          </v-select>
        </c-filter-api-block>
        <c-filter-api-block title="Limit Number entities per page" :hasTooltips=false>
          <div class="main-layout__box__limit">
            <v-btn
              class="mx-2 main-layout__settings__buttons"
              color="grey"
              icon
              x-small
              dark
              @click.native="decreaseLimit()"
            >
              <v-icon dark>
                mdi-minus
              </v-icon>
            </v-btn>
            <v-text-field
              class="main-layout__settings__text-field__limit"
              outlined
              :value="limit"
              dense
              background-color="white"
              @change="updateLimit($event)"
              hide-details
            />
            <v-btn
              class="mx-2 main-layout__settings__buttons"
              color="grey"
              icon
              x-small
              dark
              @click.native="increaseLimit()"
            >
              <v-icon dark>
                mdi-plus
              </v-icon>
            </v-btn>
          </div>
        </c-filter-api-block>
        <c-filter-api-block title="Change version entities" :hasTooltips=false>
          <v-text-field
            class="main-layout__text-field"
            height="40px"
            outlined
            dense
            :value="version"
            background-color="white"
            @change="updateVersion($event)"
            label="Enter a version"
            hide-details
          />
        </c-filter-api-block>
        <c-filter-api-block title="Download entities as Haystack format" :hasTooltips=false>
          <div class="main-layout__button">
            <v-btn icon :href="convertData()" download="ontology.json"><v-icon>file_download</v-icon></v-btn>
          </div>
        </c-filter-api-block>
        <c-filter-api-block title="Clear your api tokens stored in navigator" :hasTooltips=false>
          <v-btn
            color="blue-grey"
            rounded
            class="main-layout__settings__cache-button white--text"
            @click.native="clearLocalStorage()"
          >
            Clear api keys
          </v-btn>
        </c-filter-api-block>
        <div class="main-layout__footer">
          <a href="https://github.com/engie-group/shaystack" class="main-layout__footer-links">
            Github Project
          </a>
          <a href="mailto:franck.SEUTIN@engie.com" class="main-layout__footer-links">
            Contact
          </a>
          <span>Haystack version: 3.0</span>
        </div>
      </div>
    </v-app-bar>
    <v-app-bar app class="main-layout__headers__not-extended" v-else>
      <div class="main-layout__headers__not-extended__buton">
        <v-btn color="grey" icon dark @click.native="changeExtention()">
          <v-icon>mdi-format-list-bulleted-square</v-icon>
        </v-btn>
      </div>
    </v-app-bar>
  <main>
    <router-view class="router-view" />
  </main>
</div>
`
import CFilterApiBlock from '../../components/CFilterApiBlock/CFilterApiBlock.js'
import { API_COLORS, dateUtils, formatEntityService, utils } from '../../services/index.js'
export default {
  template,
  components: { CFilterApiBlock },
  data() {
    return {
      comboboxInput: '',
      dateStartInput: this.startDateRange,
      dateEndInput: this.endDateRange,
      menu: false,
      isExtended: true
    }
  },
  computed: {
    linkEntities() {
      return this.$store.getters.linkEntities
    },
    getNavigationModeInformation() {
      return this.$store.getters.isNavigationModeActivated ? 'Navigation mode activated' : 'Navigation mode deactivated'
    },
    getLinkNameDisplayedInformation() {
      return this.$store.getters.isLinkNameDisplayed ? 'Link names displayed' : 'Link names not displayed'
    },
    activatedLinks: {
      get() {
        return this.$store.getters.activatedLinks;
      },
      set(activatedLinks) {
        this.$store.commit('SET_ACTIVATED_LINKS', { activatedLinks });
      }
    },
    isNavigationModeActivated: {
      get() {
        return this.$store.getters.isNavigationModeActivated;
      },
      set(isNavigationModeActivated) {
        this.$store.commit('SET_IS_NAVIGATION_MODE_ACTIVATED', { isNavigationModeActivated });
        let limit = isNavigationModeActivated ? 130 : 40
        this.$store.commit('SET_LIMIT', { limit })
      }
    },
    isLinkNameDisplayed: {
      get() {
        return this.$store.getters.isLinkNameDisplayed;
      },
      set(isLinkNameDisplayed) {
        this.$store.commit('SET_IS_LINK_NAME_DISPLAYED', { isLinkNameDisplayed });
      }
    },
    filterApi() {
      return this.$store.getters.filterApi
    },
    existingApiEndPointFromPlugin(){
       return this.getExistingApiEndpoint ? true : false
    },
    version() {
      return this.$store.getters.version
    },
    limit() {
      return this.$store.getters.limit
    },
    startDateRange() {
      const filterDateStart = this.$store.getters.dateRange.start === '' ? null : this.$store.getters.dateRange.start
      this.dateStartInput = filterDateStart
      return filterDateStart
    },
    endDateRange() {
      const filterEndDate = this.$store.getters.dateRange.end === '' ? null : this.$store.getters.dateRange.end
      this.dateEndInput = filterEndDate
      return filterEndDate
    },
    getApiServers() {
      return this.$store.getters.apiServers.map(apiServer => apiServer.haystackApiHost)
    }
  },
  methods: {
    getBasicFilter() {
      if (!this.customFilter) return []
      else return this.customFilter()
    },
    changeExtention() {
      this.isExtended = !this.isExtended
    },
    isApiServerAlreadyExists(host) {
      return Boolean(this.$store.getters.apiServers.find(apiServer => apiServer.haystackApiHost === host))
    },
    async changeApiServers(haystackApiHost) {
      await this.$store.dispatch('deleteHaystackApi', { haystackApiHost })
      // if (this.getApiServers.length > 0) {
      //   await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
      // }
      const { q, d, l, v } = this.$route.query
      if (this.getApiServers.length > 0)
        this.$router.push({ query: { q, d, l, v, a: `["${this.getApiServers.join('","')}"]` } })
      else this.$router.push({ query: { q } })
      this.comboboxInput = ''
    },
    async updateAPI() {
      const haystackApiHost = this.comboboxInput
      if (!this.isApiServerAlreadyExists(haystackApiHost)) {
        const apiServersBeforeAdd = this.getApiServers.slice()
        await this.$store.dispatch('createApiServer', { haystackApiHost, isStart: false })
        await this.$store.dispatch('reloadDataForOneApi', {
          entity: this.$store.getters.filterApi,
          apiNumber: this.getApiServers.length - 1
        })
        if (JSON.stringify(this.getApiServers) !== JSON.stringify(apiServersBeforeAdd)) {
          const { q, d, l, v } = this.$route.query
          const { hash } = this.$route
          this.$router.push({ hash, query: { q, d, l, v, a: `["${this.getApiServers.join('","')}"]` } })
        }
        this.comboboxInput = ''
      }
    },
    async updateFilter(newFilter) {
      if (newFilter !== this.$store.getters.filterApi) {
        this.$store.commit('SET_FILTER_API', { filterApi: newFilter })
        const { a, d, l, v } = this.$route.query
        this.$router.push({ query: { q: newFilter, a, d, l, v } })
      }
    },
    async updateLimit(newLimit) {
      if (newLimit !== this.$store.getters.limit) {
        if (formatEntityService.isNumber(newLimit)) {
          this.$store.commit('SET_LIMIT', { limit: newLimit })
          const { a, d, q, v } = this.$route.query
          this.$router.push({ query: { q, a, d, v, l: newLimit } })
          await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
        } else alert('Limit should be a number')
      }
    },
    async updateVersion(newVersion) {
      if (newVersion !== this.$store.getters.version) {
        if (dateUtils.checkDateFormat(newVersion) || newVersion === '') {
          this.$store.commit('SET_VERSION', { version: newVersion })
          const { a, d, q, l } = this.$route.query
          this.$router.push({ query: { q, a, d, l, v: newVersion } })
          await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
        } else {
          alert('Wrong format Date')
        }
      }
    },
    async increaseLimit() {
      const increasedLimit = Number(this.limit) + 1
      this.$store.commit('SET_LIMIT', { limit: increasedLimit })
      const { a, d, q, v } = this.$route.query
      this.$router.push({ query: { q, a, d, v, l: increasedLimit } })
      await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
    },
    async decreaseLimit() {
      const decreasedLimit = Number(this.limit) - 1
      this.$store.commit('SET_LIMIT', { limit: decreasedLimit })
      const { a, d, q, v } = this.$route.query
      this.$router.push({ query: { q, a, d, v, l: decreasedLimit } })
      await this.$store.dispatch('reloadAllData', { entity: this.$store.getters.filterApi })
    },
    async updateStartDateRange(newStartDate) {
      const startDateRange = !newStartDate || dateUtils.checkDateFormat(newStartDate)
      if (newStartDate !== this.startDateRange) {
        if (startDateRange || startDateRange === '') {
          if (dateUtils.checkDateRangeIsCorrect(startDateRange, this.endDateRange)) {
            this.$store.commit('SET_START_DATE_RANGE', { startDateRange })
            const { a, q, l, v } = this.$route.query
            if ((!this.endDateRange || this.endDateRange === '') && startDateRange === '') {
              this.$router.push({ query: { q, a, l, v } })
            } else if ((startDateRange === 'today' || startDateRange === 'yesterday') && !this.endDateRange)
              this.$router.push({
                query: { q, a, l, v, d: `${startDateRange}` }
              })
            else
              this.$router.push({
                query: { q, a, l, v, d: `${startDateRange},${this.endDateRange ? this.endDateRange : ''}` }
              })
          } else alert('Begin Date should be smaller than end Date')
        } else {
          this.dateStartInput = this.startDateRange
          alert('Wrong format Date')
        }
      }
    },
    async updateEndDateRange(newEndDate) {
      const endDateRange = !newEndDate || dateUtils.checkDateFormat(newEndDate)
      if (newEndDate !== this.endDateRange) {
        if (endDateRange || endDateRange === '') {
          if (dateUtils.checkDateRangeIsCorrect(this.startDateRange, endDateRange)) {
            this.$store.commit('SET_END_DATE_RANGE', { endDateRange })
            const { a, q, l, v } = this.$route.query
            if ((!this.startDateRange || this.startDateRange === '') && endDateRange === '')
              this.$router.push({ query: { q, a, l, v } })
            else if ((endDateRange === 'today' || endDateRange === 'yesterday') && !this.startDateRange)
              this.$router.push({
                query: { q, a, l, v, d: `${endDateRange}` }
              })
            else
              this.$router.push({
                query: { q, a, l, v, d: `${this.startDateRange ? this.startDateRange : ''},${endDateRange}` }
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
    },
    clearLocalStorage() {
      localStorage.clear()
    },
    convertData() {
      const entities = this.$store.getters.entities.slice()
      let data
      if (entities.length === 0) data = {}
      else {
        data = utils.formatEntitiesHayson(entities)
      }
      const contentType = 'application/json'
      const dData = JSON.stringify(data, null, 2)
      const blob = new Blob([dData], { type: contentType })
      return window.URL.createObjectURL(blob)
    },
    filterEntityTooltipText() {
      return  `
        <h3>Filter Example:</h3>
            <span>
                <h4>site or equip</h4>
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
        `
    },
    existingApiFromPluginText() {
    if (!this.existingApiEndPointFromPlugin) return null
      return `
       <h4> Api Endpoint Available: </h4>
         <span
           ><li> ` + this.getExistingApiEndpoint().join('</li><li>  ') + `</li>
         </span>
   `
   },
   dateRangeTooltipsText() {
   return `
     <h4>Date Example:</h4>
        <span
          ><li>today</li>
          <li>yesterday</li>
          <li>2020-01-01</li>
          <li>2020/01/01</li>
          <li>2020-01-01T12:00:00.00Z</li>
        </span>
        `
     }
  }
}

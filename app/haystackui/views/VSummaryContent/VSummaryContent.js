const template = `
  <div v-if="isAnyData && isDataLoaded" class="summary-content">
    <div class="summary-content__graph">
      <c-graph
        v-if="isDataLoaded"
        @pointClicked="onGraphClick"
        :dataEntities="getRelationGraphEntity(entities)"
        id="graph-entities"
        title="Entities links"
      ></c-graph>
    </div>
    <div v-if="isDataLoaded">
      <c-entity-row
        v-for="row in entitiesGroupedById"
        :ref="getEntityId(row)"
        :id="getEntityId(row)"
        :key="row.id.val"
        @onRefClick="onRefClick"
        @onExternalRefClick="onExternalRefClick"
        :idEntity="row.id.val"
        :dataEntity="row"
        :his="getHistories(row.id.val)"
        :isDataLoaded="isDataLoaded"
        class="summary-content__entity-row"
      />
    </div>
  </div>
  <div v-else-if="!isDataLoaded" class="summary-content__spinner">
    <v-progress-circular :size="100" :width="10" indeterminate></v-progress-circular>
  </div>
  <div v-else class="summary-content">
    <v-alert type="warning" class="summary-content__alert-no-data">Enter an API that contains data</v-alert>
  </div>
`
import { API_COLORS, dateUtils, formatEntityService } from '../../services/index.js'
import CEntityRow from '../../components/CEntityRow/CEntityRow.js'
import CGraph from '../../components/CGraph/CGraph.js'
export default {
  template,
  components: { CEntityRow, CGraph },
  data () {
    return {
      checkbox1: true,
      checkbox2: false,
    }
  },
  computed: {
    isAnyData() {
      return !(this.entities.length === 0 || (this.entities.length === 1 && this.entities[0].length === 0))
    },
    isActionApi() {
      return this.$store.getters.isActionApi
    },
    filterApi() {
      return this.$store.getters.filterApi
    },
    isDataLoaded() {
      return this.$store.getters.isDataLoaded
    },
    entities() {
      return this.$store.getters.entities.map(entities => entities.filter(entity => entity.id))
    },
    idsWithHis() {
      return this.entitiesGroupedById
        .filter(entity => entity.his)
    },
    histories() {
      return this.$store.getters.histories
    },
    apiServers() {
      return this.$store.getters.apiServers
    },
    getDefaultApiHost() {
      return this.$store.getters.apiServers[0].haystackApiHost
    },
    entitiesGroupedById() {
      // eslint-disable-next-line
      const entities = this.entities.slice()
      if (entities.length === 1) return entities[0]
      return this.groupByIdEntities(entities)
    }
  },
  methods: {
    async reloadPageFromQueryParameters() {
      if (Object.keys(this.$route.query).length > 0) {
        if (this.$route.query.a) {
          const defaultApiServers = JSON.parse(this.$route.query.a)
          await this.$store.dispatch('setHaystackApi', { apiServers: defaultApiServers })
        }
        if (this.$route.query.l) {
          await this.$store.commit('SET_LIMIT', { limit: this.$route.query.l })
        }
        if (this.$route.query.v) {
          await this.$store.commit('SET_VERSION', { version: this.$route.query.v })
        }
        if (this.$route.query.q) {
          await this.$store.commit('SET_FILTER_API', { filterApi: this.$route.query.q })
        } else this.$store.commit('SET_FILTER_API', { filterApi: '' })
        if (this.$route.query.d) {
          const splittedUrl = this.$route.query.d.split(',')
          if (splittedUrl.length > 1) {
            const startDate = dateUtils.checkDateFormat(this.$route.query.d.split(',')[0])
            const endDate = dateUtils.checkDateFormat(this.$route.query.d.split(',')[1])
            await this.$store.commit('SET_START_DATE_RANGE', { startDateRange: startDate })
            await this.$store.commit('SET_END_DATE_RANGE', { endDateRange: endDate || '' })
          } else {
            await this.$store.commit('SET_START_DATE_RANGE', { startDateRange: this.$route.query.d })
            await this.$store.commit('SET_END_DATE_RANGE', { endDateRange: '' })
          }
        }
        if (!this.$route.query.d) {
          await this.$store.commit('SET_START_DATE_RANGE', { startDateRange: '' })
          await this.$store.commit('SET_END_DATE_RANGE', { endDateRange: '' })
        }
      }
      await this.$store.dispatch('reloadAllData', { entity: this.filterApi })
    },
    handleScroll() {
      // eslint-disable-next-line
      this.entitiesGroupedById.find(entity => {
        const entityId = this.getEntityId(entity)
        const el = this.$refs[entityId][0] ? this.$refs[entityId][0].$el : null
        if (this.elementInViewport(el)) {
          const { query } = this.$route
          this.$router.replace({ hash: entityId, query }).catch(() => {})
        }
      })
    },
    elementInViewport(el) {
      if (!el) return false
      let top = el.offsetTop
      const height = el.offsetHeight

      while (el.offsetParent) {
        // eslint-disable-next-line
        el = el.offsetParent
        top += el.offsetTop
      }
      return top >= window.pageYOffset && top + height <= window.pageYOffset + window.innerHeight
    },
    isPointFromSource(pointName, colorEntities) {
      return colorEntities.find(entityColor => entityColor.id === pointName && API_COLORS.includes(entityColor.color))
    },
    async onRefClick(refId) {
      this.$refs[refId][0].$el.scrollIntoView(true)
      window.scrollBy(0, -70)
      const { query } = this.$route
      this.$router.push({ hash: refId, query }).catch(() => {})
    },
    async onExternalRefClick(refId) {
      const newApiFilter = `id==@${refId}`
      await this.$store.dispatch('reloadAllData', {
        entity: newApiFilter
      })
      this.$store.commit('SET_FILTER_API', { filterApi: newApiFilter })
      const { query } = this.$route
      this.$router.push({ hash: refId, query: { a: query.a, q: newApiFilter, d: query.d, l: query.l, v: query.v } }).catch(() => {})
    },
    async onGraphClick(pointName) {
      const linkBetweenEntities = this.getRelationGraphEntity(this.entities)
      const colorEntities = linkBetweenEntities[1]
      const entityNameToEntityId = linkBetweenEntities[2]
      const { query } = this.$route
      if (!this.isPointFromSource(pointName, colorEntities)) {
        const newApiFilter = `id==@${entityNameToEntityId[pointName] || pointName}`
        await this.$store.dispatch('reloadAllData', {
          entity: newApiFilter
        })
        this.$store.commit('SET_FILTER_API', { filterApi: newApiFilter })
        this.$router.push({ query: { a: query.a, q: newApiFilter, d: query.d, l: query.l, v: query.v } }).catch(() => {})
      } else {
        this.$refs[pointName][0].$el.scrollIntoView(true)
        window.scrollBy(0, -70)
        this.$router.push({ hash: pointName, query }).catch(() => {})
      }
    },
    getEntityName(entity) {
      return formatEntityService.formatEntityName(entity)
    },
    getEntityId(entity) {
      if (!entity.id) return 'NaN'
      return entity.id.val
    },
    groupByIdEntities(entities) {
      return formatEntityService.groupAllEntitiesById(entities)
    },
    getHistory(idEntity, sourceNumber) {
      if (!this.histories[sourceNumber][idEntity]) return null
      return this.histories[sourceNumber][idEntity]
    },
    getHistories(idEntity) {
      if (this.histories.length === 1) {
        const entityHis = this.getHistory(idEntity, 0)
        return entityHis ? [this.getHistory(idEntity, 0)] : []
      }
      // eslint-disable-next-line
      return this.histories.map((history, index) => {
          return this.getHistory(idEntity, index)
        })
        .filter(history => history)
    },
    async updateFilter(newFilter) {
      if (newFilter !== this.$store.getters.filterApi) {
        this.$store.commit('SET_FILTER_API', { filterApi: newFilter })
        await this.$store.dispatch('reloadAllData', { entity: newFilter })
      }
    },
    getRelationGraphEntity(entities) {
      return formatEntityService.getLinkBetweenEntities(entities)
    },
    redirectOnRightHash() {
      if (this.isAnyData) {
        if (this.entitiesGroupedById) {
          const entityNames = this.entitiesGroupedById.map(entity => this.getEntityId(entity))
          if (entityNames.indexOf(decodeURI(this.$route.hash).substring(1)) >= 0) {
            if (this.$refs[decodeURI(this.$route.hash).substring(1)]) {
              const elementRef = this.$refs[decodeURI(this.$route.hash).substring(1)][0]
              if (elementRef) {
                elementRef.$el.scrollIntoView()
                window.scrollBy(0, -70)
              }
            }
          }
        }
        window.addEventListener('scroll', this.handleScroll, { passive: true })
      }
    }
  },
  watch: {
    // eslint-disable-next-line
    async $route(to, from) {
      if (JSON.stringify(to.query) !== JSON.stringify(from.query) && !this.isActionApi) {
        await this.reloadPageFromQueryParameters()
      } else if (this.isActionApi) {
        this.$store.commit('SET_IS_ACTION_API', { isActionApi: false })
      }
    }
  },
  async beforeMount() {
    await this.reloadPageFromQueryParameters()
    if (this.apiServers.length === 0) {
      await this.$store.dispatch('createApiServer', {
        haystackApiHost: `${window.location.origin}${window.location.pathname}`,
        isStart: true
      })
      if (this.apiServers.length !== 0) {
        this.$router.push({ query: { a: `["${this.apiServers.map(api => api.haystackApiHost).join('","')}"]` } }).catch(() => {})
        this.$store.dispatch('reloadAllData', { entity: this.filterApi })
      }
    }
  },
  updated() {
    this.redirectOnRightHash()
  }
}


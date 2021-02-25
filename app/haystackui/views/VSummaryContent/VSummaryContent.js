const template = `
  <div class="summary-content">
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
        :ref="getEntityName(row)"
        :key="row.id.val"
        :id="row.id.val"
        :dataEntity="row"
        :his="getHistories(row.id.val)"
        :isDataLoaded="isDataLoaded"
        class="summary-content__entity-row"
      />
    </div>
  </div>
`
import formatService from '../../services/format.service.js'
import CEntityRow from '../../components/CEntityRow/CEntityRow.js'
import CGraph from '../../components/CGraph/CGraph.js'

export default {
  template,
  components: { CEntityRow, CGraph },
  computed: {
    filterApi() {
      return this.$store.getters.filterApi
    },
    isDataLoaded() {
      return this.$store.getters.isDataLoaded
    },
    entities() {
      return this.$store.getters.entities
    },
    idsWithHis() {
      return this.entitiesGroupedById
        .filter(entity => entity.his)
        .map(entity => formatService.formatIdEntity(entity.id.val))
    },
    histories() {
      return this.$store.getters.histories
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
    handleScroll() {
      // eslint-disable-next-line
      this.entitiesGroupedById.find(entity => {
        const entityName = this.getEntityName(entity)
        const el = this.$refs[entityName][0] ? this.$refs[entityName][0].$el : null
        if (this.elementInViewport(el)) {
          const { query } = this.$route
          this.$router.replace({ hash: entityName, query })
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
      return colorEntities.find(
        entityColor =>
          entityColor.id === pointName && ['#dc143c', '#0000ff', '#00a86b', '#cc5500'].includes(entityColor.color)
      )
    },
    async onGraphClick(pointName) {
      const linkBetweenEntities = this.getRelationGraphEntity(this.entities)
      const colorEntities = linkBetweenEntities[1]
      const entityNameToEntityId = linkBetweenEntities[2]
      if (!this.isPointFromSource(pointName, colorEntities)) {
        const newApiFilter = `id==@${entityNameToEntityId[pointName] || pointName}`
        await this.$store.dispatch('reloadAllData', {
          entity: newApiFilter
        })
        this.$store.commit('SET_FILTER_API', { filterApi: newApiFilter })
      } else {
        this.$refs[pointName][0].$el.scrollIntoView()
        window.scrollBy(0, -200)
      }
    },
    getEntityName(entity) {
      return formatService.formatEntityName(entity)
    },
    groupByIdEntities(entities) {
      return formatService.groupAllEntitiesById(entities)
    },
    getHistory(idEntity, sourceNumber) {
      const formattedId = formatService.formatIdEntity(idEntity)
      if (!this.histories[sourceNumber][formattedId]) return null
      return this.histories[sourceNumber][formattedId]
    },
    getHistories(idEntity) {
      if (this.histories.length === 1) return [this.getHistory(idEntity, 0)]
      // eslint-disable-next-line
      return this.histories.map((history, index) => this.getHistory(idEntity, index))
    },
    async updateFilter(newFilter) {
      if (newFilter !== this.$store.getters.filterApi) {
        this.$store.commit('SET_FILTER_API', { filterApi: newFilter })
        await this.$store.dispatch('reloadAllData', { entity: newFilter })
      }
    },
    getRelationGraphEntity(entities) {
      return formatService.getLinkBetweenEntities(entities)
    }
  },
  async beforeMount() {
    if (Object.keys(this.$route.query).length > 0) {
      if (this.$route.query.apiServers) {
        const defaultApiServers = JSON.parse(this.$route.query.apiServers)
        await this.$store.commit('SET_API_SERVERS', { apiServers: defaultApiServers })
      }
      if (this.$route.query.filterApi) {
        await this.$store.commit('SET_FILTER_API', { filterApi: this.$route.query.filterApi })
      }
    }
    await this.$store.dispatch('reloadAllData', { entity: this.filterApi })
  },
  updated() {
    const entityNames = this.entitiesGroupedById.map(entity => this.getEntityName(entity))
    if (entityNames.indexOf(decodeURI(this.$route.hash).substring(1)) >= 0) {
      this.$refs[decodeURI(this.$route.hash).substring(1)][0].$el.scrollIntoView()
      window.scrollBy(0, -200)
    }
    window.addEventListener('scroll', this.handleScroll, { passive: true })
  }
}


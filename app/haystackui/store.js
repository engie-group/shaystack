/* eslint-disable no-shadow */
import HaystackApiService from './services/haystackApi.service.js'
import { formatEntityService, dateUtils } from './services/index.js'

Vue.use(Vuex)
window.env = window.env || {}
const state = {
  entities: [[]],
  apiServers: [],
  linkEntities: [],
  entitiesWithHis: {},
  activatedLinks: [],
  isNavigationModeActivated: false,
  isLinkNameDisplayed: false,
  limit: 40,
  version: '',
  dateRange: { start: '', end: '' },
  isDataLoaded: false,
  filterApi: '',
  isActionApi: false
}
export const mutations = {
  SET_ACTIVATED_LINKS(state, { activatedLinks }) {
    state.activatedLinks = activatedLinks
  },
  SET_IS_LINK_NAME_DISPLAYED(state, {isLinkNameDisplayed}) {
    state.isLinkNameDisplayed = isLinkNameDisplayed
  },
  SET_IS_NAVIGATION_MODE_ACTIVATED(state, {isNavigationModeActivated}) {
    state.isNavigationModeActivated = isNavigationModeActivated
  },
  SET_LINK_ENTITIES(state, { linkEntities }) {
    state.linkEntities = linkEntities
  },
  SET_IS_ACTION_API(state, { isActionApi }) {
    state.isActionApi = isActionApi
  },
  SET_ENTITIES(state, { entities }) {
    state.entities = entities
  },
  SET_HISTORIES(state, { histories }) {
    state.histories = histories
  },
  ADD_NEW_ENTITIES(state, { entities, apiNumber }) {
    const newEntities = state.entities.slice()
    // eslint-disable-next-line
    newEntities.length < (apiNumber + 1) ? newEntities.push(entities) : (newEntities[apiNumber] = entities)
    state.entities = newEntities
  },
  SET_IS_DATA_LOADED(state, { isDataLoaded }) {
    state.isDataLoaded = isDataLoaded
  },
  SET_API_SERVERS(state, { apiServers }) {
    const newApiServers = []
    const newEntities = []
    const newHistories = []
    apiServers.map(apiServer => {
      newEntities.push([])
      newHistories.push({})
      const apiKey = localStorage.getItem(apiServer) ? localStorage.getItem(apiServer) : ''
      newApiServers.push(new HaystackApiService({ haystackApiHost: apiServer, apiKey }))
    })
    state.entities = newEntities
    state.histories = newHistories
    state.apiServers = newApiServers
  },
  SET_HAYSTACK_API(state, { haystackApiHost, apiKey }) {
    const newApiServers = state.apiServers.slice()
    newApiServers.push(new HaystackApiService({ haystackApiHost, apiKey }))
    localStorage.setItem(haystackApiHost, apiKey)
    state.apiServers = newApiServers
  },
  SET_FILTER_API(state, { filterApi }) {
    state.filterApi = filterApi
  },
  SET_START_DATE_RANGE(state, { startDateRange }) {
    const dateRange = { ...state.dateRange }
    dateRange.start = startDateRange
    state.dateRange = dateRange
  },
  SET_END_DATE_RANGE(state, { endDateRange }) {
    const dateRange = { ...state.dateRange }
    dateRange.end = endDateRange
    state.dateRange = dateRange
  },
  SET_LIMIT(state, { limit }) {
    state.limit = limit
  },
  SET_VERSION(state, { version }) {
    state.version = version
  },
  SET_ENTITIES_WITH_HIS(state, { entitiesWithHis }) {
    state.entitiesWithHis = entitiesWithHis
  },
  ADD_ENTITIES_WITH_HIS(state, {entityId, apiNumber}) {
    if (state.entitiesWithHis.hasOwnProperty(entityId)) {
      if (Array.isArray(apiNumber)) {
        apiNumber.map(number => {
          if (!state.entitiesWithHis[entityId].includes(number)) state.entitiesWithHis[entityId].push(number)
        })
      }
      else {
        if (!state.entitiesWithHis[entityId].includes(apiNumber)) state.entitiesWithHis[entityId].push(apiNumber)
      }
    }
    else {
      if (Array.isArray(apiNumber)) {
        state.entitiesWithHis[entityId] = apiNumber
        }
      else state.entitiesWithHis[entityId] = [apiNumber]
    }
  }
}
export const getters = {
  linkEntities(state) {
    return state.linkEntities
  },
  isNavigationModeActivated(state) {
    return state.isNavigationModeActivated
  },
  activatedLinks(state) {
    return state.activatedLinks
  },
  isLinkNameDisplayed(state) {
    return state.isLinkNameDisplayed
  },
  isActionApi(state) {
    return state.isActionApi
  },
  apiServers(state) {
    return state.apiServers
  },
  entities(state) {
    return state.entities
  },
  apiNumber(state) {
    return state.apiServers.length
  },
  isDataLoaded(state) {
    return state.isDataLoaded
  },
  filterApi(state) {
    return state.filterApi
  },
  dateRange(state) {
    return state.dateRange
  },
  limit(state) {
    return state.limit
  },
  version(state) {
    return state.version
  },
  entitiesWithHis(state) {
    return state.entitiesWithHis
  }
}
export const actions = {
  async setHaystackApi(context, { apiServers }) {
    const availableApiServers = await Promise.all(
      apiServers.filter(async apiServer => {
        const apiKey = localStorage.getItem(apiServer) ? localStorage.getItem(apiServer) : ''
        const newApiServer = new HaystackApiService({ haystackApiHost: apiServer, apiKey })
        const apiServerStatus = await newApiServer.isHaystackApi()
        return apiServerStatus === 'available'
      })
    )
    context.commit('SET_API_SERVERS', { apiServers: availableApiServers })
  },
  async createApiServer(context, { haystackApiHost, isStart }) {
    const apiKey = localStorage.getItem(haystackApiHost) ? localStorage.getItem(haystackApiHost) : ''
    const newApiServer = new HaystackApiService({ haystackApiHost, apiKey })
    const newServerStatus = await newApiServer.isHaystackApi(isStart)
    if (newServerStatus === 'available') {
      await context.commit('SET_HAYSTACK_API', { haystackApiHost, apiKey })
    } else if (newServerStatus === 'notAuthenticated') {
        const apiKey = prompt('You need to enter an api token', '')
        const newApiServerWithToken = new HaystackApiService({ haystackApiHost, apiKey })
        const newServerStatusWithToken = await newApiServerWithToken.isHaystackApi()
        if (newServerStatusWithToken === 'available') {
          await context.commit('SET_HAYSTACK_API', { haystackApiHost, apiKey })
        } else alert('wrong token')
    }
    context.commit('SET_IS_ACTION_API', { isActionApi: true })
  },
  async commitNewEntities(context, { entities, apiNumber }) {
    await context.commit('ADD_NEW_ENTITIES', { entities, apiNumber })
  },
  async fetchEntity(context, { entity, apiNumber }) {
    let entities = await context.getters.apiServers[apiNumber].getEntity(entity, state.limit, state.version)
    entities = entities['rows'].length ? formatEntityService.addApiSourceInformationToEntity(entities.rows, apiNumber + 1) : []
    await context.dispatch('commitNewEntities', {
      entities,
      apiNumber
    })
  },
  async fetchAllEntity(context, { entity }) {
    const { apiServers } = context.getters
    await Promise.all(
      await apiServers.map(async (apiServer, index) => {
        await context.dispatch('fetchEntity', { entity, apiNumber: index })
      })
    )
  },
  async fetchAllEntitiesWithHis(context) {
    const { entities } = context.getters
    const entitiesCopy = entities.slice()
    const groupEntities = entitiesCopy.length === 1 ? entitiesCopy[0] : formatEntityService.groupAllEntitiesById(entitiesCopy)
    const idsEntityWithHis = groupEntities
      .filter(entity => entity.his)
      .map(entity => {
        context.commit('ADD_ENTITIES_WITH_HIS', { entityId: entity.id.val, apiNumber: entity.his.apiSource})
        return { id: entity.id.val, apiSource: entity.his.apiSource }
      })
  },
  async reloadDataForOneApi(context, { entity, apiNumber }) {
    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: false })
    await context.dispatch('fetchEntity', { entity, apiNumber })
    const { entities } = context.getters
    const entitiesCopy = entities.slice()
    const groupEntities = entitiesCopy.length === 1 ? entitiesCopy[0] : formatEntityService.groupAllEntitiesById(entitiesCopy)
    const idsEntityWithHis = groupEntities
      .filter(entity => entity.his)
      .map(entity => {
        context.commit('ADD_ENTITIES_WITH_HIS', { entityId: entity.id.val, apiNumber: apiNumber+1 })
        return { id: formatEntityService.formatIdEntity(entity.id.val), apiSource: entity.his.apiSource }
      })

    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: true })
  },
  async reloadAllData(context, { entity }) {
    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: false })
    const { apiServers } = context.getters
    if (apiServers.length > 0) {
      await Promise.all([await context.dispatch('fetchAllEntity', { entity })]).finally(async () => {
        await context.dispatch('fetchAllEntitiesWithHis')
      })
    }
    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: true })
  },
  async deleteHaystackApi(context, { haystackApiHost }) {
    const { apiServers } = context.getters
    await context.commit('SET_IS_DATA_LOADED', { isDataLoaded: false })
    const newApiServers = state.apiServers.slice()
    let newEntities = state.entities.slice()
    let newEntitiesWithHis = Object.assign({}, state.entitiesWithHis)
    const indexOfApiServerToDelete = state.apiServers.findIndex(
      apiServer => apiServer.haystackApiHost === haystackApiHost
    )
    newEntities.splice(indexOfApiServerToDelete, 1)
    if (indexOfApiServerToDelete !== apiServers.length) {
      newEntitiesWithHis = formatEntityService.reajustHistoriesApiSource(newEntitiesWithHis, indexOfApiServerToDelete)
      newEntities = formatEntityService.reajustEntitiesApiSource(newEntities, indexOfApiServerToDelete)
    }
    context.commit('SET_ENTITIES', { entities: newEntities })
    context.commit('SET_ENTITIES_WITH_HIS', { entitiesWithHis: newEntitiesWithHis })
    state.apiServers = newApiServers.filter(apiServer => apiServer.haystackApiHost !== haystackApiHost)
    context.commit('SET_IS_ACTION_API', { isActionApi: true })
    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: true })
  }
}
export default new Vuex.Store({
  actions,
  getters,
  mutations,
  state
})

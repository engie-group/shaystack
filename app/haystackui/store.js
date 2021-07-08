/* eslint-disable no-shadow */
import HaystackApiService from './services/haystackApi.service.js'
import { formatEntityService, dateUtils } from './services/index.js'

Vue.use(Vuex)
window.env = window.env || {}
const state = {
  entities: [[]],
  histories: [{}],
  apiServers: [],
  linkEntities: [],
  activatedLinks: [],
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
  ADD_NEW_HISTORIES(state, { idHistories, apiNumber }) {
    const newHistories = state.histories.slice()
    // eslint-disable-next-line
    newHistories.length < apiNumber + 1 ? newHistories.push(idHistories) : (newHistories[apiNumber] = idHistories)
    state.histories = newHistories
  },
  SET_IS_DATA_LOADED(state, { isDataLoaded }) {
    state.isDataLoaded = isDataLoaded
  },
  SET_API_SERVERS(state, { apiServers }) {
    const newApiServers = []
    const newEntities = []
    const newHistories = []
    // eslint-disable-next-line
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
  }
}
export const getters = {
  linkEntities(state) {
    return state.linkEntities
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
  histories(state) {
    return state.histories
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
    const entities = await context.getters.apiServers[apiNumber].getEntity(entity, state.limit, state.version)
    await context.dispatch('commitNewEntities', {
      // eslint-disable-next-line
      entities: formatEntityService.addApiSourceInformationToEntity(entities.rows, apiNumber + 1),
      apiNumber
    })
  },
  async fetchHistories(context, { idsEntityWithHis, apiNumber }) {
    const isHisReadAvailable = await context.getters.apiServers[apiNumber].isHisReadAvailable()
    const dateRange = dateUtils.formatDateRangeUrl(state.dateRange)
    if (isHisReadAvailable) {
      const histories = await Promise.all(
        idsEntityWithHis.map(async entity => {
          if (typeof entity.apiSource === 'object') {
            if (entity.apiSource.find(apiSourceNumber => apiSourceNumber === apiNumber + 1)) {
              return context.getters.apiServers[apiNumber].getHistory(entity.id, dateRange)
            }
            return []
          }
          // eslint-disable-next-line
          if (entity.apiSource === apiNumber + 1) return context.getters.apiServers[apiNumber].getHistory(entity.id, dateRange)
          return []
        })
      )
      const idHistories = {}
      idsEntityWithHis.forEach(
        // eslint-disable-next-line no-return-assign
        (key, index) =>
          (idHistories[key.id] = histories[index].map(history => {
            return { ...history, apiSource: apiNumber }
          }))
      )
      await context.commit('ADD_NEW_HISTORIES', { idHistories, apiNumber })
    }
  },
  async fetchAllEntity(context, { entity }) {
    const { apiServers } = context.getters
    await Promise.all(
      // eslint-disable-next-line
      await apiServers.map(async (apiServer, index) => {
        await context.dispatch('fetchEntity', { entity, apiNumber: index })
      })
    )
  },
  async fetchAllHistories(context) {
    const { apiServers, entities } = context.getters
    const entitiesCopy = entities.slice()
    const groupEntities = entitiesCopy.length === 1 ? entitiesCopy[0] : formatEntityService.groupAllEntitiesById(entitiesCopy)
    const idsEntityWithHis = groupEntities
      .filter(entity => entity.his)
      .map(entity => {
        return { id: entity.id.val, apiSource: entity.his.apiSource }
      })
    await Promise.all(
      // eslint-disable-next-line
      await apiServers.map(async (apiServer, index) => {
        await context.dispatch('fetchHistories', { idsEntityWithHis, apiNumber: index })
      })
    )
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
        return { id: formatEntityService.formatIdEntity(entity.id.val), apiSource: entity.his.apiSource }
      })
    await context.dispatch('fetchHistories', { idsEntityWithHis, apiNumber })
    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: true })
  },
  async reloadAllData(context, { entity }) {
    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: false })
    const { apiServers } = context.getters
    if (apiServers.length > 0) {
      await Promise.all([await context.dispatch('fetchAllEntity', { entity })]).finally(async () => {
        await context.dispatch('fetchAllHistories')
      })
    }
    context.commit('SET_IS_DATA_LOADED', { isDataLoaded: true })
  },
  async deleteHaystackApi(context, { haystackApiHost }) {
    const { apiServers } = context.getters
    await context.commit('SET_IS_DATA_LOADED', { isDataLoaded: false })
    const newApiServers = state.apiServers.slice()
    let newHistories = state.histories.slice()
    let newEntities = state.entities.slice()
    const indexOfApiServerToDelete = state.apiServers.findIndex(
      apiServer => apiServer.haystackApiHost === haystackApiHost
    )
    newHistories.splice(indexOfApiServerToDelete, 1)
    newEntities.splice(indexOfApiServerToDelete, 1)
    if (indexOfApiServerToDelete !== apiServers.length) {
      newHistories = formatEntityService.reajustHistoriesApiSource(newHistories, indexOfApiServerToDelete)
      newEntities = formatEntityService.reajustEntitiespiSource(newEntities, indexOfApiServerToDelete)
    }
    context.commit('SET_ENTITIES', { entities: newEntities })
    context.commit('SET_HISTORIES', { histories: newHistories })
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

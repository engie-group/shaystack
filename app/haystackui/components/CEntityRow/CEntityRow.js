const template = `
  <div class="entity-row__container">
    <h2 data-test-entity-title class="entity-row__title">{{ entityName }}</h2>
    <div class="content-container">
      <div class="entity-row__table">
        <v-data-table
          :headers="headers"
          :items="tableValues"
          :hide-default-footer="true"
          :disable-pagination="true"
          :custom-sort="customSort"
          :dense="true"
          item-class="row_class"
        >
          <template v-slot:[\`item.value\`]="{ item }">
            <div v-if="isCoordinate(item.value)">
              <a :href="getUrlCoordinate(item.value)" target="_blank">{{ item.value.substring(2) }}</a>
              <v-icon v-if="isDuplicateKey(item.tag)" class="material-icons entity-row__click-button">warning</v-icon>
            </div>
            <div v-else-if="isRef(item.value)">
              <span>{{ getRefName(item) }}</span>
              <v-icon class="material-icons entity-row__click-button" @click="copyText(item)">content_copy</v-icon>
            </div>
            <div v-else-if="isDuplicateKey(item.tag)">
              <span>{{ item.value }}</span>
              <v-icon v-if="hisUri(item.tag)" class="material-icons entity-row__click-button">warning</v-icon>
            </div>
            <span v-else>{{ item.value }}</span>
          </template>
        </v-data-table>
      </div>
      <div class="entity-row__chart">
        <c-chart
          data-test-history-chart
          v-if="displayChart"
          :id="chartId"
          :data="sortDataChart(data)"
          :unit="unit"
          title="Historical values"
        />
      </div>
    </div>
  </div>
`

import formatService from '../../services/format.service.js'
import dataUtils from '../../services/data.utils.js'
import CChart from '../CChart/CChart.js'

export default {
  template,
  name: 'CEntityRow',
  components: { CChart },
  props: {
    idEntity: {
      type: String,
      default: ''
    },
    his: {
      type: Array,
      default: () => []
    },
    dataEntity: {
      type: Object,
      default: () => {}
    },
    isFromExternalSource: {
      type: Boolean,
      default: false
    },
    isDataLoaded: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      headers: [
        {
          text: 'Tag',
          align: 'start',
          sortable: false,
          value: 'tag'
        },
        { text: 'Value', value: 'value', sortable: false }
      ]
    }
  },
  computed: {
    tableValues() {
      return Object.keys(this.dataEntity).map(key => {
        const result = this.getEntityValue(key)
        // eslint-disable-next-line
        return { tag: key.split('_')[0], value: result.val, row_class: [result.val === '✓' ? `${key} haystack-marker` : key, `apiSource_${result.apiSource}` ] }
      })
    },
    entityId() {
      return this.idEntity.split(' ')[0]
    },
    displayChart() {
      return this.his.filter(his => (his ? his.length > 0 : his)).length > 0 && this.isDataLoaded
    },
    chartId() {
      return this.isFromExternalSource ? `${this.idEntity}-external` : this.idEntity
    },
    entityName() {
      return formatService.formatEntityName(this.dataEntity)
    },
    data() {
      return this.his.map(historic => (historic ? formatService.formatCharts(historic) : null))
    },
    dataEntityKeys() {
      return Object.keys(this.dataEntity)
    },
    unit() {
      return this.dataEntity.unit ? this.dataEntity.unit.val.substring(2) : ''
    }
  },
  methods: {
    sortDataChart(dataChart) {
      return dataUtils.sortChartDataByDate(dataChart)
    },
    getRefName(item) {
      if (item.tag === 'id') {
        const entityName = item.value.substring(2).split(' ')
        if (entityName.length === 1) {
          if (this.dataEntity.dis) return this.dataEntity.dis.val.substring(2)
          return `@${entityName[0]}`
        }
        entityName.shift()
        return entityName.join(' ')
      }
      const entityName = item.value.substring(2).split(' ')
      if (entityName.length === 1) return `@${entityName[0]}`
      entityName.shift()
      return entityName.join(' ')
    },
    hisUri(tag) {
      if (tag === 'hisURI') return false
      return true
    },
    isRef(item) {
      if (typeof item !== 'string') return false
      return item.substring(0, 2) === 'r:'
    },
    isDuplicateKey(item) {
      const keysDuplicated = Object.keys(this.dataEntity).filter(key => key.split('_')[0] === item)
      // const itemSplitted = item.split('_')
      return keysDuplicated.length > 1
      // return itemSplitted.length > 1 && Number(itemSplitted[1])
    },
    isCoordinate(item) {
      if (typeof item !== 'string') return false
      // if (item.value.length < 4) return false
      return item.substring(0, 2) === 'c:'
    },
    customSort(items) {
      const copyItems = items.slice()
      const sortedItems = copyItems
        .sort((item1, item2) => item1.tag.localeCompare(item2.tag))
        .sort((item1, item2) => {
          if (item1.tag === 'id') return -1
          if (item2.tag === 'id') return 1
          return 0
        })
      return sortedItems
    },
    copyText(item) {
      const id = `@${item.value.split(' ')[0].substring(2)}`
      const virtualElement = document.createElement('textarea')
      document.body.appendChild(virtualElement)
      virtualElement.value = id
      virtualElement.select()
      document.execCommand('copy')
      document.body.removeChild(virtualElement)
    },
    getNumberValue(dataEntityKey) {
      const numberStringValue = this.dataEntity[dataEntityKey].val.substring(2).split(' ')
      const numberValue =
        numberStringValue.length > 1
          ? `${Number(numberStringValue[0])} ${numberStringValue[1]}`
          : Number(numberStringValue[0])
      return { val: numberValue, apiSource: this.dataEntity[dataEntityKey].apiSource }
    },
    getUrlCoordinate(coordinate) {
      return `http://www.google.com/maps/place/${coordinate.substring(2)}`
    },
    getEntityValue(dataEntityKey) {
      const value = this.dataEntity[dataEntityKey].val
      if (value === 'm:') return { val: '✓', apiSource: this.dataEntity[dataEntityKey].apiSource }
      if (value.substring(0, 2) === 'c:') return { val: value, apiSource: this.dataEntity[dataEntityKey].apiSource }
      if (value.substring(0, 2) === 'r:') return { val: value, apiSource: this.dataEntity[dataEntityKey].apiSource }
      if (value.substring(0, 2) === 'n:') return this.getNumberValue(dataEntityKey)
      if (value.substring(0, 2) === 'r:') return { val: value, apiSource: this.dataEntity[dataEntityKey].apiSource }
      if (value === '') return { val: '', apiSource: this.dataEntity[dataEntityKey].apiSource }
      return { val: value.substring(2), apiSource: this.dataEntity[dataEntityKey].apiSource }
    }
  }
}


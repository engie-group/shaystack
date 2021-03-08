const template = `
  <v-data-table
    :headers="headers"
    :items="dataTables"
    :hide-default-footer="true"
    :disable-pagination="true"
    :custom-sort="customSort"
    item-class="row_class"
    :dense="true"
  >
    <template v-slot:[\`item.value\`]="{ item }">
      <div v-if="isCoordinate(item.value)">
        <a :href="getUrlCoordinate(item.value)" target="_blank">{{ item.value.substring(2) }}</a>
        <v-icon v-if="isDuplicateKey(item.attribute)" class="material-icons entity-row__click-button">warning</v-icon>
      </div>
      <div v-else-if="isRef(item.value)">
        <span v-if="isRefClickable(item)" class="entity-row__ref-row" @click="refClicked(getRefId(item))">{{
          getRefName(item)
        }}</span>
        <span
          v-else-if="isExternalRef(item)"
          class="entity-row__external-ref-row"
          @click="externalRefClicked(getRefId(item))"
          >{{ getRefName(item) }}</span
        >
        <span v-else>{{ getRefName(item) }}</span>
        <v-icon class="material-icons entity-row__click-button" @click="copyText(item)">content_copy</v-icon>
      </div>
      <div v-else-if="isDuplicateKey(item.attribute)">
        <span>{{ item.value }}</span>
        <v-icon v-if="hisUri(item.attribute)" class="material-icons entity-row__click-button">warning</v-icon>
      </div>
      <span v-else>{{ item.value }}</span>
    </template>
  </v-data-table>
`

import formatService from '../../services/format.service.js'

export default {
  template,
  props: {
    isEntityData: {
      type: Boolean
    },
    dataHisTable: {
      type: Array,
      default: () => []
    },
    dataEntity: {
      type: Object,
      default: () => {}
    },
    allEntities: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      headers: [
        {
          text: this.isEntityData ? 'Tag' : 'Date',
          align: 'start',
          sortable: false,
          value: 'attribute'
        },
        { text: 'Value', value: 'value', sortable: false }
      ]
    }
  },
  computed: {
    dataTables() {
      return this.dataHisTable.map(row => {
        if (this.isEntityData) return this.replaceKeyObject({ ...row }, 'tag', 'attribute')

        return this.replaceKeyObject({ ...row }, 'ts', 'attribute')
      })
    }
  },

  methods: {
    replaceKeyObject(object, oldKey, newKey) {
      return formatService.renameObjectKey(object, oldKey, newKey)
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
    customSort(items) {
      if (this.isEntityData) {
        const copyItems = items.slice()
        const sortedItems = copyItems
          .sort((item1, item2) => item1.attribute.localeCompare(item2.attribute))
          .sort((item1, item2) => {
            if (item1.attribute === 'id') return -1
            if (item2.attribute === 'id') return 1
            return 0
          })
        return sortedItems
      }
      return items.slice()
    },
    getRefId(item) {
      return item.value.split(' ')[0].substring(2)
    },
    isRef(item) {
      if (typeof item !== 'string') return false
      return item.substring(0, 2) === 'r:'
    },
    isExternalRef(item) {
      return item.attribute !== 'id'
    },
    refClicked(refId) {
      this.$emit('onRefClick', refId)
    },
    externalRefClicked(refId) {
      this.$emit('onExternalRefClick', refId)
    },
    isRefClickable(item) {
      let isClickable = false
      if (item.attribute === 'id') return false
      // eslint-disable-next-line
      this.allEntities.map(entities => {
        // eslint-disable-next-line
        entities.map(entity => {
          if (this.getEntityId(entity) === this.getRefId(item)) {
            isClickable = true
          }
        })
      })
      return isClickable
    },
    isCoordinate(item) {
      if (typeof item !== 'string') return false
      // if (item.value.length < 4) return false
      return item.substring(0, 2) === 'c:'
    },
    getUrlCoordinate(coordinate) {
      return `http://www.google.com/maps/place/${coordinate.substring(2)}`
    },
    isDuplicateKey(item) {
      const keysDuplicated = Object.keys(this.dataEntity).filter(key => key.split('_')[0] === item)
      // const itemSplitted = item.split('_')
      return keysDuplicated.length > 1
      // return itemSplitted.length > 1 && Number(itemSplitted[1])
    },
    getEntityId(entity) {
      return entity.id.val.split(' ')[0].substring(2)
    },
    getRefName(item) {
      if (item.attribute === 'id') {
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
    }
  }
}

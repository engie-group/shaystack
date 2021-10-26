const template = `
  <v-card>
    <div style="margin: 5px;">
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
            <a :href="getUrlCoordinate(item.value)" target="_blank">{{ getCoordinate(item.value) }}</a>
            <v-icon v-if="isDuplicateKey(item.attribute)" class="material-icons entity-row__click-button"
              >warning</v-icon
            >
          </div>
          <div v-else-if="isRef(item.value)" style="display:flex;">
            <span v-if="isRefClickable(item)" style="width:90%;" class="entity-row__ref-row" @click="refClicked(getRefId(item))">{{
              getRefName(item.value)
            }}</span>
            <span
              v-else-if="isExternalRef(item)"
              class="entity-row__external-ref-row"
              style="width:90%;"
              @click="externalRefClicked(getRefId(item))"
              >{{ getRefName(item.value) }}</span
            >
            <span style="width:90%;" v-else>{{ getRefName(item.value) }}</span>
            <v-icon v-if="isDuplicateKey(item.attribute)" class="material-icons entity-row__click-button">warning</v-icon>
            <v-icon class="material-icons entity-row__click-button" @click="copyText(item)" style="width=10%;">content_copy</v-icon>
          </div>
          <div v-else-if="isDuplicateKey(item.attribute)">
            <span>{{ item.value.val }}</span>
            <v-icon v-if="hisUri(item.attribute)" class="material-icons entity-row__click-button">warning</v-icon>
          </div>
          <span v-else-if="isTag(item.value)"> ✓ </span>
          <span v-else-if="isNumber(item.value)">{{ getNumberValue(item.value) }}</span>
          <span v-else>{{ item.value.val }}</span>
        </template>
      </v-data-table>
    </div>
  </v-card>
`

import { utils } from '../../services/index.js'

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
      return utils.renameObjectKey(object, oldKey, newKey)
    },
    copyText(item) {
      const id = `@${item.value.val}`
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
        return copyItems
          .sort((item1, item2) => item1.attribute.localeCompare(item2.attribute))
          .sort((item1, item2) => {
            if (item1.attribute === 'id') return -1
            if (item2.attribute === 'id') return 1
            return 0
          })
      }
      return items.slice()
    },
    getRefId(item) {
      return item.value.val
    },
    isRef(item) {
      return item._kind === 'Ref'
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
      this.allEntities.map(entities => {
        entities.map(entity => {
          if (entity.id.val === this.getRefId(item)) {
            isClickable = true
          }
        })
      })
      return isClickable
    },
    isCoordinate(item) {
      if (!item.hasOwnProperty('_kind')) return false
      return item._kind === 'Coord'
    },
    getUrlCoordinate(coordinate) {
      return `http://www.google.com/maps/place/${this.getCoordinate(coordinate)}`
    },
    getCoordinate(coordinate) {
      return `${coordinate.lat},${coordinate.lng}`
    },
    isDuplicateKey(item) {
      const keysDuplicated = Object.keys(this.dataEntity).filter(key => key.split('^')[0] === item)
      return keysDuplicated.length > 1
    },
    getRefName(item) {
      return item.dis ? item.dis : item.val
    },
    hisUri(tag) {
      if (tag === 'hisURI') return false
      return true
    },
    isTag(item) {
      return item._kind === 'Marker'
    },
    isNumber(item) {
      return item._kind === 'Num'
    },
    getNumberValue(item) {
      return item.unit ? `${item.val} ${item.unit}`: str(item.val)
    }
  }
}

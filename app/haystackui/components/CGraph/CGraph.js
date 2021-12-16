const template = `
  <v-card style="height: 100%;" ref="graph-container">
    <div style="height: 100%;" :id="id" class="bar-chart__chart"></div>
  </v-card>
`
import { formatEntityService } from '../../services/index.js'

export default {
  template,
  name: 'CGraph',
  props: {
    id: {
      type: String,
      default: ''
    },
    title: {
      type: String,
      default: ''
    },
    subtitle: {
      type: String,
      default: ''
    },
    keys: {
      type: Array,
      default: () => ['from', 'to', 'relation']
    },
    dataEntities: {
      type: Array,
      default: () => []
    }
  },
  computed: {
    getUniqueLinkRefBetweenEntities() {
      return formatEntityService.getUniquesRelationsBetweenEntities(this.dataEntities[0])
    },
    isLinkNameDisplayed() {
      return this.$store.getters.isLinkNameDisplayed
    },
    activatedLinks() {
      return this.$store.getters.activatedLinks
    }
  },
  beforeMount() {
    const linkEntities = this.getUniqueLinkRefBetweenEntities
    this.$store.commit('SET_LINK_ENTITIES', { linkEntities })
    if (this.activatedLinks.length === 0) this.$store.commit('SET_ACTIVATED_LINKS', { activatedLinks: linkEntities })
  },
  watch: {
    isLinkNameDisplayed(newValue) {
      const newDataLabels = { dataLabels: {
        enabled: true,
        allowOverlap: true,
        linkFormat: newValue ? '{point.relation}' : ''
      }}
      this.chart.series[0].update(newDataLabels)
    },
    activatedLinks(newActivatedLinks) {
      const linkDisabled = this.getUniqueLinkRefBetweenEntities.filter(link => !this.activatedLinks.includes(link))
      const dataWithoutDeactivedLinks = this.dataEntities[0].filter(dataNode => !linkDisabled.includes(dataNode[2]))
      const correctedDataWithoutDeactivedLinks = this.deactiveSiteRefLinkWhenSeveralLinks(dataWithoutDeactivedLinks)
      this.chart.series[0].setData(correctedDataWithoutDeactivedLinks)
    }
  },
  methods: {
    updateChartWithRightLinks() {
      const linkDisabled = this.getUniqueLinkRefBetweenEntities.filter(link => !this.activatedLinks.includes(link))
      const dataWithoutDeactivedLinks = this.dataEntities[0].filter(dataNode => !linkDisabled.includes(dataNode[2]))
      const correctedDataWithoutDeactivedLinks = this.deactiveSiteRefLinkWhenSeveralLinks(dataWithoutDeactivedLinks)
      this.chart.series[0].setData(correctedDataWithoutDeactivedLinks)
    },
    createChart(data, nodes) {
      const height = (this.$refs['graph-container'].$el.clientHeight - 5);
      const width = this.$refs['graph-container'].$el.clientWidth;
      return Highcharts.chart(this.id, {
        title: {
          text: this.title
        },
        chart: {
          type: 'networkgraph',
          width: width,
          height: height
        },
        plotOptions: {
          networkgraph: {
            keys: this.keys,
            point: {
              events: {
                click: function emitEvent(event) {
                  this.$emit('pointClicked', event.point.id)
                }.bind(this)
              }
            }
          }
        },
        credits: {
          enabled: false
        },
        tooltip : {
          enabled : true,
          formatter : function() {
            return `<div> <span> ${this.point.id} </span> </div>`
          }
        },
        series: [
          {
            dataLabels: {
              enabled: true,
              allowOverlap: true,
              linkFormat: this.isLinkNameDisplayed ? '{point.relation}' : '',
            },
            id: 'lang-tree',
            data,
            nodes,
        }
        ]
      })
    },
    deactiveSiteRefLinkWhenSeveralLinks(links) {
        return links.filter(link => !((links.filter(link2 => link[0]===link2[0]).length>1)&&(link[2]==='siteRef')))
  }
  },
  mounted() {
    (function(H) {
  H.wrap(H.seriesTypes.networkgraph.prototype.pointClass.prototype, 'getLinkPath', function(p) {
    const left = this.fromNode
    const right = this.toNode

    const angle = Math.atan((left.plotX - right.plotX) / (left.plotY - right.plotY))

    if (angle) {
      const path = ['M', left.plotX, left.plotY, right.plotX, right.plotY]
      const lastPoint = left
      const nextLastPoint = right
      const pointRadius = 40
      const arrowLength = 5
      const arrowWidth = 5

      if (left.plotY < right.plotY) {
        path.push(
          nextLastPoint.plotX - pointRadius * Math.sin(angle),
          nextLastPoint.plotY - pointRadius * Math.cos(angle)
        )
        path.push(
          nextLastPoint.plotX -
            pointRadius * Math.sin(angle) -
            arrowLength * Math.sin(angle) -
            arrowWidth * Math.cos(angle),
          nextLastPoint.plotY -
            pointRadius * Math.cos(angle) -
            arrowLength * Math.cos(angle) +
            arrowWidth * Math.sin(angle)
        )

        path.push(
          nextLastPoint.plotX - pointRadius * Math.sin(angle),
          nextLastPoint.plotY - pointRadius * Math.cos(angle)
        )
        path.push(
          nextLastPoint.plotX -
            pointRadius * Math.sin(angle) -
            arrowLength * Math.sin(angle) +
            arrowWidth * Math.cos(angle),
          nextLastPoint.plotY -
            pointRadius * Math.cos(angle) -
            arrowLength * Math.cos(angle) -
            arrowWidth * Math.sin(angle)
        )
      } else {
        path.push(
          nextLastPoint.plotX + pointRadius * Math.sin(angle),
          nextLastPoint.plotY + pointRadius * Math.cos(angle)
        )
        path.push(
          nextLastPoint.plotX +
            pointRadius * Math.sin(angle) +
            arrowLength * Math.sin(angle) -
            arrowWidth * Math.cos(angle),
          nextLastPoint.plotY +
            pointRadius * Math.cos(angle) +
            arrowLength * Math.cos(angle) +
            arrowWidth * Math.sin(angle)
        )
        path.push(
          nextLastPoint.plotX + pointRadius * Math.sin(angle),
          nextLastPoint.plotY + pointRadius * Math.cos(angle)
        )
        path.push(
          nextLastPoint.plotX +
            pointRadius * Math.sin(angle) +
            arrowLength * Math.sin(angle) +
            arrowWidth * Math.cos(angle),
          nextLastPoint.plotY +
            pointRadius * Math.cos(angle) +
            arrowLength * Math.cos(angle) -
            arrowWidth * Math.sin(angle)
        )
      }

      return path
    }
    return [
      ['M', left.plotX || 0, left.plotY || 0],
      ['L', right.plotX || 0, right.plotY || 0]
    ]
  })
})(Highcharts)
    this.chart = this.createChart(this.dataEntities[0], this.dataEntities[1])
    this.updateChartWithRightLinks()
  },
 //updated()
}

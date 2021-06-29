const template = `
  <v-card style="height: 100%;" ref="graph-container">
    <div :id="id" class="bar-chart__chart"></div>
  </v-card>
`

/* eslint-disable */
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

    const height = this.$refs['graph-container'].$el.clientHeight;
    const width = this.$refs['graph-container'].$el.clientWidth;
    this.chart = Highcharts.chart(this.id, {
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
          layoutAlgorithm: {
            enableSimulation: true,
            friction: -0.98,
            linkLength: 35
            },
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
            linkFormat: '',
          },
          id: 'lang-tree',
          data: this.dataEntities[0],
          nodes: this.dataEntities[1]
        }
      ]
    })
  }
}

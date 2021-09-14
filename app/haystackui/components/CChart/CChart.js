const template = `
  <v-card>
    <div :id="id" style="margin: 30px;" class="bar-chart__chart"></div>
  </v-card>
`
import { API_COLORS } from '../../services/index.js'
import formatChartService from '../../services/formatChartService.js'
export default {
  template,
  name: 'CChart',
    props: {
    id: {
      type: String,
      default: ''
    },
    entityId: {
      type: String,
      default: ''
    },
    title: {
      type: String,
      default: ''
    },
    data: {
      type: Array,
      default: () => []
    },
    unit: {
      type: String,
      default: ''
    },
  },
  data() {
    return {
      colors: API_COLORS,
    }
  },
  mounted() {
    this.chart = Highcharts.chart(this.id, {
      title: {
        text: this.title
      },
      chart: {
        width: '700',
        height: '400'
      },
      xAxis: {
        type: 'datetime'
      },
      legend: {
        enabled: false
      },
      credits: {
        enabled: false
      },
      tooltip: {
        valueSuffix: this.unit
      },
      series: this.data.map(data => ({ data: data.his, color: this.colors[data.apiNumber - 1] }))
    })
  }
}


import dateUtils from './dateUtils.js'

const formatChartService = {
  formatVal: value => {
    if (typeof value === 'object') {
        return Number(value.val)
    }
    return Number(value)
  },
  isNumberTypeChart(dataChart) {
    if (!dataChart) return false
    const dataChartCopy = dataChart.slice()
    const dataChartType = Array.from(
      new Set(
        dataChartCopy.map(data => {
          if (typeof data.val === 'string') return 's'
          if (typeof data.val === 'number') return 'n'
          if (typeof data.val === 'object') {
            if (data.val._kind === 'Num') return 'n'
          }
          return null
        })
      )
    )
    return dataChartType.length === 1 && dataChartType[0] === 'n'
  },
  sortChartDataByDate(dataChart) {
    const dataChartSorted = dataChart.slice()
    return dataChartSorted.map(dataApi => {
      return {
        apiNumber: dataApi.apiNumber,
        his: dataApi.his.sort((firstData, secondData) => secondData[0] - firstData[0])
      }
    })
  },
  formatCharts(historic) {
    return historic.map(point => {
      return [dateUtils.formatDate(point.ts.val),  formatChartService.formatVal(point.val)]
    })
  },
  formatYAxis: histories => {
    return histories.map(history => formatChartService.formatVal(history.val))
  }
}

export default formatChartService

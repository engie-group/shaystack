const dataUtils = {
    checkDateFormat: dateString => {
    if (dateString === 'today') return dateString
    if (dateString === 'yesterday') return dateString
    const dateObject = new Date(dateString)
    if (dateObject.toString() === 'Invalid Date') return null
    return dateString
  },
  formatDate: dateString => {
    const date = new Date(dateString.substring(2).split(' ')[0])
    return date.getTime()
  },
  formatVal: valueString => {
    if (valueString.split(' ').length > 1) {
      return Number(valueString.split(' ')[0].substring(2))
    }
    return Number(valueString.substring(2))
  },
  isNumberTypeChart(dataChart) {
    if (!dataChart) return false
    const dataChartCopy = dataChart.slice()
    const dataChartType = Array.from(
      new Set(
        dataChartCopy.map(data => {
          if (typeof data.val === 'string') {
            if (data.val.substring(0, 2) === 'n:') return 'n'
            return 's'
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
  }
}

export default dataUtils

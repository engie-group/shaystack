const dataUtils = {
  checkDateFormat: dateString => {
    const splittedDate = dateString.split('-')
    if (splittedDate.length !== 3) return false
    const year = splittedDate[0]
    const month = splittedDate[1]
    const day = splittedDate[2]
    if (year.length === 4 && month.length === 2 && day.length === 2) return dateString
    return false
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
    return dataChartSorted.map(dataApi => dataApi.sort((firstData, secondData) => secondData[0] - firstData[0]))
  }
}

export default dataUtils

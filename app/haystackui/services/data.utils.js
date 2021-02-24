const dataUtils = {
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
  sortChartDataByDate(dataChart) {
    const dataChartSorted = dataChart.slice()
    return dataChartSorted.map(dataApi => dataApi.sort((firstData, secondData) => secondData[0] - firstData[0]))
  }
}

export default dataUtils

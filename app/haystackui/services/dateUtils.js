const dateUtils = {
    checkDateFormat: dateString => {
    if (dateString === '') return dateString
    if (dateString === 'today') return dateString
    if (dateString === 'yesterday') return dateString
    const dateObject = new Date(dateString)
    if (dateObject.toString() === 'Invalid Date') return null
    return dateString
  },
  formatDate: dateString => {
    const date = new Date(dateString)
    return date.getTime()
  },
    formatDateRangeUrl(dateRange) {
    if (dateRange.start === 'today' || dateRange.start === 'yesterday') {
      if (dateRange.end === '' || !dateRange.end) return dateRange.start
      else return `${dateUtils.dateConvertor(dateRange.start).toISOString()},${dateUtils.dateConvertor(dateRange.end, false).toISOString()}`
    }
    else if (dateRange.end === 'today' || dateRange.end === 'yesterday') {
      if (dateRange.start === '') return dateRange.end
      else return `${dateUtils.dateConvertor(dateRange.start).toISOString()},${dateUtils.dateConvertor(dateRange.end).toISOString()}`
    }
    else
      return `${dateRange.start === '' ? '' : dateUtils.dateConvertor(dateRange.start).toISOString()},${dateRange.end === '' ? '' : dateUtils.dateConvertor(dateRange.end).toISOString()}`
  },
  dateConvertor(date, isStartDate=true) { // Same Type
    if (date === 'today') return isStartDate ? new Date() : new Date(new Date().setDate(new Date().getDate() + 1))
    else if (date === 'yesterday') return isStartDate ? new Date(new Date().setDate(new Date().getDate() - 1)) : new Date()
    else if (!date) return ''
    else return new Date(date)
  },
  checkDateRangeIsCorrect(dateStart, dateEnd) {
    const dateStartObject = dateUtils.dateConvertor(dateStart)
    const dateEndObject = dateUtils.dateConvertor(dateEnd)
    if (dateStartObject === '' || dateEndObject === '') return true
    else return dateStartObject < dateEndObject
  }
}

export default dateUtils

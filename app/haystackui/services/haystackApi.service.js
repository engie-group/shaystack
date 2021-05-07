class HaystackApiService {
  constructor({ haystackApiHost, apiKey }) {
    this.haystackApiHost = haystackApiHost
    this.apiKey = apiKey
  }
  get api() {
    const headers = this.apiKey ?
    {
      'Content-Type': 'application/json',
      'KeyId': this.apiKey
    } :
    {
      'Content-Type': 'application/json'
    }
    return axios.create({
      baseURL: `${this.haystackApiHost}`,
      timeout: 20000,
      withCredentials: false,
      headers
    })
  }

  async isHaystackApi() {
    try {
      const opsResponse = await this.api.get(`/ops`)
      const formatResponse = await this.api.get(`/formats`)
      const isHaystackApiAvailable =
        opsResponse.data.rows.find(row => row.name === 's:read') &&
        formatResponse.data.rows.find(row => row.mime === 's:application/json' && row.receive === 'm:')
      if (isHaystackApiAvailable) return true
      alert('API not available for')
      return false
    } catch {
      alert('Not an Haystack API')
      return false
    }
  }

  async isHisReadAvailable() {
    try {
      const response = await this.api.get(`/ops`)
      if (response.data.rows.find(row => row.name === 's:hisRead')) return true
      return false
    } catch {
      return false
    }
  }

  async getEntity(entity, limit, version = '') {
    const versionParam = version === '' ? '' : `&version=${new Date(version).toISOString()}`
    try {
      const response = await this.api.get(`/read?filter=${entity}&limit=${limit}${versionParam}`)
      return response.data
    } catch {
      return []
    }
  }
  async getHistory(id, range = '2020-01-01,2022-12-31') {
    try {
      const response =
        range === ','
          ? await this.api.get(`/hisRead?id=@${id}`)
          : await this.api.get(`/hisRead?id=@${id}&range=${range}`)
      return response.data.rows
    } catch {
      return []
    }
  }

}

export default HaystackApiService

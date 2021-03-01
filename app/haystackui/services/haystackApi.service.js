class HaystackApiService {
  constructor({ haystackApiHost }) {
    this.haystackApiHost = haystackApiHost
  }
  // Invoquer ops pour savoir les méthodes qui sont disponibles
  // Invoquer format pour savoir si l'api est compatible avec le format JSON

  get api() {
    return axios.create({
      baseURL: `${this.haystackApiHost}`,
      timeout: 20000,
      withCredentials: false,
      headers: {
        'Content-Type': 'application/json'
      }
    })
  }

  async isHaystackApi() {
    try {
      const response = await this.api.get(`/ops`)
      if (response.data.rows.find(row => row.name === 's:read')) return true
      return false
    } catch {
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

  // getEntity => read  and entity => filter
  async getEntity(entity) {
    try {
      const response = await this.api.get(`/read?filter=${entity}&limit=40`)
      return response.data
    } catch {
      return []
    }
  }

  // getHistory => hisRead
  async getHistory(id, range = 'today') {
    try {
      const response = await this.api.get(`/hisRead?id=@${id}&range=${range}`)
      return response.data.rows
    } catch {
      return []
    }
  }
}

export default HaystackApiService

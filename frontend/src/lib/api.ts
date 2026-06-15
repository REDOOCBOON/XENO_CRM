


const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_V1 = `${API_BASE}/api/v1`

async function fetchAPI(path: string, options: RequestInit = {}) {
  const url = `${API_V1}${path}`
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!res.ok) {
    
    const error = await res.text()
    throw new Error(error || `HTTP error ${res.status}`)
  }

  
  const text = await res.text()
  if (!text) return null
  return JSON.parse(text)
}


export const getCustomers = () => fetchAPI('/customers')
export const createCustomer = (data: any) => fetchAPI('/customers', { method: 'POST', body: JSON.stringify(data) })


export const getOrders = () => fetchAPI('/orders')
export const createOrder = (data: any) => fetchAPI('/orders', { method: 'POST', body: JSON.stringify(data) })


export const getSegments = () => fetchAPI('/segments')
export const createSegment = (data: any) => fetchAPI('/segments', { method: 'POST', body: JSON.stringify(data) })
export const previewSegment = (definition: any) => fetchAPI('/segments/preview', { method: 'POST', body: JSON.stringify(definition) })
export const parseNLSegment = (prompt: string) => fetchAPI('/segments/nlp', {
  method: 'POST',
  body: JSON.stringify({ prompt })
})


export const getCampaigns = () => fetchAPI('/campaigns')
export const createCampaign = (data: any) => fetchAPI('/campaigns', { method: 'POST', body: JSON.stringify(data) })
export const sendCampaign = (id: string) => fetchAPI(`/campaigns/${id}/send`, { method: 'POST' })
export const getCampaignAnalytics = (id: string) => fetchAPI(`/campaigns/${id}/analytics`)


export const submitGoal = (goal: string) => fetchAPI('/agent/goal', {
  method: 'POST',
  body: JSON.stringify({ goal })
})
export const executeGoalCampaign = (data: any) => fetchAPI('/agent/goal/execute', {
  method: 'POST',
  body: JSON.stringify(data)
})


export const getOpportunities = () => fetchAPI('/opportunities')
export const scanOpportunities = () => fetchAPI('/opportunities/scan', { method: 'POST' })
export const executeOpportunity = (id: string) => fetchAPI(`/opportunities/${id}/execute`, { method: 'POST' })


export const getCustomerIntelligence = (id: string) => fetchAPI(`/customers/${id}/intelligence`)
export const recalculateIntelligence = () => fetchAPI('/customers/intelligence/recalculate', { method: 'POST' })


export const getDashboardKPIs = () => fetchAPI('/dashboard/kpis')


export const seedMockData = () => fetchAPI('/admin/seed-mock-data', { method: 'POST' })


export const generateCampaignContent = (name: string, audienceDesc: string, goal: string) =>
  fetchAPI('/campaigns/nlp-content', {
    method: 'POST',
    body: JSON.stringify({ name, audience_description: audienceDesc, goal })
  })

export const getAIRecommendations = () => fetchAPI('/ai/recommendations')

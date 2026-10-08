const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

function getAuthHeader() {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchWithAuth(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
    ...options.headers,
  };
  
  if (options.body instanceof FormData) {
    delete headers['Content-Type']; // Let browser set boundary
  }

  const response = await fetch(`${API_URL}${url}`, {
    ...options,
    headers,
  });
  
  if (response.status === 401) {
    localStorage.removeItem('access_token');
    // Optional: trigger logout event or redirect
  }
  
  if (!response.ok) {
    let errorMsg = 'An error occurred';
    try {
      const errorData = await response.json();
      if (Array.isArray(errorData.detail)) {
        // FastAPI 422 Validation Error array
        errorMsg = errorData.detail.map(err => `${err.loc[err.loc.length - 1]}: ${err.msg}`).join(', ');
      } else if (errorData.detail && typeof errorData.detail === 'object' && errorData.detail.message) {
         // Custom ErrorDetail format
         if (errorData.detail.errors && Array.isArray(errorData.detail.errors)) {
           errorMsg = errorData.detail.errors.map(err => `${err.loc[err.loc.length - 1]}: ${err.message}`).join(', ');
         } else {
           errorMsg = errorData.detail.message;
         }
      } else {
        errorMsg = errorData.detail || errorData.message || errorMsg;
      }
    } catch (e) {
      // Ignored
    }
    throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
  }
  
  const data = await response.json();
  return data && data.items ? data.items : data;
}

export const authAPI = {
  login: (data) => fetchWithAuth('/auth/login', { 
    method: 'POST', 
    body: JSON.stringify(data)
  }),
  register: (data) => fetchWithAuth('/auth/register', { 
    method: 'POST', 
    body: JSON.stringify(data)
  }),
  getMe: () => fetchWithAuth('/auth/me')
};

export const eventsAPI = {
  getEvents: (params) => {
    const qs = new URLSearchParams(params).toString();
    return fetchWithAuth(`/events${qs ? '?' + qs : ''}`);
  },
  getEvent: (id) => fetchWithAuth(`/events/${id}`),
  createEvent: (data) => fetchWithAuth('/events', { 
    method: 'POST', 
    body: JSON.stringify(data)
  }),
  updateEvent: (id, data) => fetchWithAuth(`/events/${id}`, { 
    method: 'PATCH', 
    body: JSON.stringify(data) 
  }),
  deleteEvent: (id) => fetchWithAuth(`/events/${id}`, { method: 'DELETE' }),
  publishEvent: (id) => fetchWithAuth(`/events/${id}/publish`, { method: 'POST' }),
  registerForEvent: (id) => fetchWithAuth(`/events/${id}/register`, { method: 'POST' }),
  uploadPoster: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchWithAuth('/events/poster', {
      method: 'POST',
      body: formData
    });
  }
};

export const registrationsAPI = {
  getMyRegistrations: () => fetchWithAuth('/registrations/me'),
  cancelRegistration: (id) => fetchWithAuth(`/registrations/${id}/cancel`, { method: 'POST' }),
  getTicket: (id) => fetchWithAuth(`/registrations/${id}/ticket`),
};

export const managerAPI = {
  getDashboard: () => fetchWithAuth('/manager/dashboard'),
  getEvents: () => fetchWithAuth('/manager/events'),
  getEventRegistrations: (id) => fetchWithAuth(`/manager/events/${id}/registrations`),
  getEventAttendance: (id) => fetchWithAuth(`/manager/events/${id}/attendance`),
  verifyTicket: (data) => fetchWithAuth('/tickets/verify', { method: 'POST', body: JSON.stringify(data) })
};

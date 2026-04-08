import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

export const getTasks   = ()         => api.get('/tasks');
export const createTask = (data)     => api.post('/tasks', data);
export const updateTask = (id, data) => api.put(`/tasks/${id}`, data);
export const deleteTask = (id)       => api.delete(`/tasks/${id}`);

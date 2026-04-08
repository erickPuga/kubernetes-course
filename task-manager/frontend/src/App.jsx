import { useState, useEffect } from 'react';
import { getTasks, createTask, updateTask, deleteTask } from './api';

const STATUS_LABELS = {
  pending:     { label: 'Pendiente',   color: '#f59e0b' },
  in_progress: { label: 'En progreso', color: '#3b82f6' },
  done:        { label: 'Completada',  color: '#10b981' },
};

export default function App() {
  const [tasks,   setTasks]   = useState([]);
  const [title,   setTitle]   = useState('');
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState('');

  const loadTasks = async () => {
    try {
      const { data } = await getTasks();
      setTasks(data);
    } catch (e) {
      setError('Error al cargar tareas: ' + e.message);
    }
  };

  useEffect(() => { loadTasks(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      await createTask({ title: title.trim() });
      setTitle('');
      await loadTasks();
    } catch (e) {
      setError('Error al crear: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStatus = async (id, status) => {
    try {
      await updateTask(id, { status });
      await loadTasks();
    } catch (e) {
      setError('Error al actualizar: ' + e.message);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Eliminar esta tarea?')) return;
    try {
      await deleteTask(id);
      await loadTasks();
    } catch (e) {
      setError('Error al eliminar: ' + e.message);
    }
  };

  return (
    <div style={{ fontFamily: 'system-ui', maxWidth: 700, margin: '40px auto', padding: '0 20px' }}>
      <h1 style={{ color: '#1e293b' }}>Task Manager</h1>
      <p style={{ color: '#64748b', marginBottom: 24 }}>
        API: {import.meta.env.VITE_API_URL}
      </p>

      {error && (
        <div style={{ background: '#fee2e2', color: '#991b1b', padding: '10px 14px',
                      borderRadius: 6, marginBottom: 16 }}>
          {error}
          <button onClick={() => setError('')} style={{ float: 'right', background: 'none',
                  border: 'none', cursor: 'pointer', fontSize: 16 }}>×</button>
        </div>
      )}

      <form onSubmit={handleCreate} style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Nueva tarea..."
          style={{ flex: 1, padding: '10px 14px', border: '1px solid #e2e8f0',
                   borderRadius: 6, fontSize: 15 }}
        />
        <button disabled={loading}
          style={{ padding: '10px 20px', background: '#3b82f6', color: 'white',
                   border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14 }}>
          {loading ? '...' : 'Agregar'}
        </button>
      </form>

      {tasks.length === 0 ? (
        <p style={{ color: '#94a3b8', textAlign: 'center', padding: 40 }}>
          No hay tareas. Crea una arriba.
        </p>
      ) : (
        tasks.map(task => {
          const s = STATUS_LABELS[task.status] || STATUS_LABELS.pending;
          return (
            <div key={task.id} style={{ background: 'white', border: '1px solid #e2e8f0',
                borderRadius: 8, padding: '14px 16px', marginBottom: 10,
                display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ flex: 1, textDecoration: task.status === 'done' ? 'line-through' : 'none',
                             color: task.status === 'done' ? '#94a3b8' : '#1e293b' }}>
                {task.title}
              </span>
              <span style={{ background: s.color + '22', color: s.color,
                             padding: '2px 10px', borderRadius: 20, fontSize: 12 }}>
                {s.label}
              </span>
              <select value={task.status}
                onChange={e => handleStatus(task.id, e.target.value)}
                style={{ padding: '4px 8px', border: '1px solid #e2e8f0', borderRadius: 4 }}>
                <option value="pending">Pendiente</option>
                <option value="in_progress">En progreso</option>
                <option value="done">Completada</option>
              </select>
              <button onClick={() => handleDelete(task.id)}
                style={{ padding: '4px 12px', background: '#ef4444', color: 'white',
                         border: 'none', borderRadius: 4, cursor: 'pointer' }}>
                Eliminar
              </button>
            </div>
          );
        })
      )}
    </div>
  );
}

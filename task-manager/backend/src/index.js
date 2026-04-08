require('dotenv').config();
const express = require('express');
const cors = require('cors');
const tasksRouter = require('./routes/tasks');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Health checks
app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

app.get('/health/ready', async (req, res) => {
  const db = require('./db');
  try {
    await db.query('SELECT 1');
    res.json({ status: 'ready', db: 'connected' });
  } catch (e) {
    res.status(503).json({ status: 'not ready', error: e.message });
  }
});

// Rutas de la API
app.use('/api/tasks', tasksRouter);

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: `Ruta ${req.path} no encontrada` });
});

app.listen(PORT, () => {
  console.log(`[Server] Backend corriendo en http://localhost:${PORT}`);
});

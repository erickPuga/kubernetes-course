const express = require('express');
const app = express();
const PORT = 3000;

app.use(express.json());

// CORS para el frontend
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  next();
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'backend' });
});

app.get('/api/info', (req, res) => {
  res.json({
    service: 'backend-api',
    version: '1.0.0',
    hostname: require('os').hostname(),
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));

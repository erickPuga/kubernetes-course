const express = require('express');
const app = express();
const PORT = 3000;

let isReady = false;
// Simular startup de 10 segundos
setTimeout(() => { isReady = true; }, 10000);

app.get('/health/live', (req, res) => {
  res.json({ status: 'alive', uptime: process.uptime() });
});

app.get('/health/ready', (req, res) => {
  if (isReady) {
    res.json({ status: 'ready' });
  } else {
    res.status(503).json({ status: 'starting...' });
  }
});

app.get('/api/data', (req, res) => {
  res.json({ data: [1, 2, 3], timestamp: Date.now() });
});

app.listen(PORT, () => console.log(`App on port ${PORT}`));

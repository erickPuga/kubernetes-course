const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const VERSION = process.env.VERSION || 'v1';

app.get('/', (req, res) => {
  res.json({
    message: 'Hola desde Kubernetes! Version 2! Vas a quedar prrro!!! :v',
    version: VERSION,
    hostname: require('os').hostname(),
    timestamp: new Date().toISOString()
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(PORT, () => {
  console.log(`App ${VERSION} corriendo en puerto ${PORT}`);
});

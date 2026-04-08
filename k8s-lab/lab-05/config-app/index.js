const express = require('express');
const fs = require('fs');
const app = express();
const PORT = process.env.APP_PORT || 3000;

app.get('/config', (req, res) => {
  // Leer variables de entorno
  const config = {
    fromEnv: {
      APP_ENV: process.env.APP_ENV,
      APP_PORT: process.env.APP_PORT,
      LOG_LEVEL: process.env.LOG_LEVEL,
      DB_HOST: process.env.DB_HOST,
      DB_PORT: process.env.DB_PORT,
      DB_NAME: process.env.DB_NAME,
      // Secrets (ocultar valor real por seguridad)
      DB_USER: process.env.DB_USER ? '***' : 'NOT SET',
      DB_PASSWORD: process.env.DB_PASSWORD ? '***' : 'NOT SET',
      JWT_SECRET: process.env.JWT_SECRET ? '***' : 'NOT SET',
    },
    fromFile: {}
  };

  // Leer configuración desde archivo montado
  try {
    const appJson = fs.readFileSync('/app/config/app.json', 'utf8');
    config.fromFile = JSON.parse(appJson);
  } catch (e) {
    config.fromFile = { error: 'File not found: ' + e.message };
  }

  res.json(config);
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(PORT, () => console.log(`Config demo app on port ${PORT}`));

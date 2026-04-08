const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  host:     process.env.DB_HOST     || 'localhost',
  port:     parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME     || 'tasksdb',
  user:     process.env.DB_USER     || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

// Probar conexion al iniciar
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('[DB] Error de conexion:', err.message);
  } else {
    console.log('[DB] Conectado a PostgreSQL:', res.rows[0].now);
  }
});

module.exports = pool;

const express = require('express');
const router = express.Router();
const db = require('../db');

// GET /api/tasks
router.get('/', async (req, res) => {
  try {
    const result = await db.query(
      'SELECT id, title, description, status, created_at FROM tasks ORDER BY created_at DESC'
    );
    res.json(result.rows);
  } catch (err) {
    console.error('[GET /tasks]', err.message);
    res.status(500).json({ error: 'Error al obtener tareas' });
  }
});

// GET /api/tasks/:id
router.get('/:id', async (req, res) => {
  try {
    const result = await db.query(
      'SELECT * FROM tasks WHERE id = $1',
      [req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Tarea no encontrada' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/tasks
router.post('/', async (req, res) => {
  const { title, description = '', status = 'pending' } = req.body;
  if (!title || title.trim() === '') {
    return res.status(400).json({ error: 'El campo title es obligatorio' });
  }
  try {
    const result = await db.query(
      'INSERT INTO tasks (title, description, status) VALUES ($1, $2, $3) RETURNING *',
      [title.trim(), description, status]
    );
    res.status(201).json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/tasks/:id
router.put('/:id', async (req, res) => {
  const { title, description, status } = req.body;
  try {
    const result = await db.query(
      `UPDATE tasks
       SET title = COALESCE($1, title),
           description = COALESCE($2, description),
           status = COALESCE($3, status),
           updated_at = NOW()
       WHERE id = $4
       RETURNING *`,
      [title, description, status, req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Tarea no encontrada' });
    }
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/tasks/:id
router.delete('/:id', async (req, res) => {
  try {
    const result = await db.query(
      'DELETE FROM tasks WHERE id = $1 RETURNING id',
      [req.params.id]
    );
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Tarea no encontrada' });
    }
    res.status(204).send();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;

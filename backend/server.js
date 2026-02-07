import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import { loadData, saveData, upsertBotConnection } from './storage.js';
import { createBotSession, stopBotSession } from './telegram.js';

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/api/bot/status/:clientId', (req, res) => {
  const data = loadData();
  const connection = data.botConnections[req.params.clientId];
  if (!connection) {
    res.status(404).json({ status: 'not_found' });
    return;
  }
  res.json({ status: connection.status, connectedAt: connection.connectedAt });
});

app.post('/api/bot/connect', async (req, res) => {
  const { clientId, token } = req.body;
  if (!token || token.length < 30) {
    res.status(400).json({ error: 'invalid_token' });
    return;
  }
  const id = clientId || uuidv4();
  const connection = upsertBotConnection(id, token);

  try {
    await createBotSession(id, token);
    connection.status = 'connected';
    connection.connectedAt = new Date().toISOString();
  } catch (error) {
    connection.status = 'error';
    connection.error = error.message;
  }

  saveData();
  res.json({ clientId: id, status: connection.status });
});

app.post('/api/bot/disconnect', (req, res) => {
  const { clientId } = req.body;
  if (!clientId) {
    res.status(400).json({ error: 'client_id_required' });
    return;
  }
  stopBotSession(clientId);
  const data = loadData();
  if (data.botConnections[clientId]) {
    data.botConnections[clientId].status = 'disconnected';
    data.botConnections[clientId].disconnectedAt = new Date().toISOString();
    saveData();
  }
  res.json({ status: 'disconnected' });
});

app.listen(PORT, () => {
  console.log(`Deliverybot_pro backend running on http://localhost:${PORT}`);
});

import fs from 'fs';
import path from 'path';

const dataPath = path.resolve('backend/data/store.json');
const baseData = {
  botConnections: {},
};

const ensureFile = () => {
  const dir = path.dirname(dataPath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  if (!fs.existsSync(dataPath)) {
    fs.writeFileSync(dataPath, JSON.stringify(baseData, null, 2));
  }
};

export const loadData = () => {
  ensureFile();
  return JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
};

export const saveData = (data) => {
  const payload = data || currentData;
  fs.writeFileSync(dataPath, JSON.stringify(payload, null, 2));
};

export const upsertBotConnection = (clientId, token) => {
  currentData = loadData();
  if (!currentData.botConnections[clientId]) {
    currentData.botConnections[clientId] = {
      status: 'pending',
      createdAt: new Date().toISOString(),
    };
  }
  currentData.botConnections[clientId].token = token;
  saveData(currentData);
  return currentData.botConnections[clientId];
};

let currentData = baseData;

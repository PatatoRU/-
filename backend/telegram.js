import TelegramBot from 'node-telegram-bot-api';

const sessions = new Map();

export const createBotSession = async (clientId, token) => {
  if (sessions.has(clientId)) {
    return sessions.get(clientId);
  }
  const bot = new TelegramBot(token, { polling: false });
  await bot.getMe();
  sessions.set(clientId, bot);
  return bot;
};

export const stopBotSession = (clientId) => {
  const bot = sessions.get(clientId);
  if (!bot) return;
  bot.stopPolling();
  sessions.delete(clientId);
};

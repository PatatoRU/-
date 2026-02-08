const tabs = document.querySelectorAll('.tab-button');
const panels = document.querySelectorAll('.panel');

const categoryForm = document.querySelector('#category-form');
const categoryList = document.querySelector('#category-list');
const menuForm = document.querySelector('#menu-form');
const menuList = document.querySelector('#menu-list');
const modifierForm = document.querySelector('#modifier-form');
const modifierList = document.querySelector('#modifier-list');
const modifierSelectList = document.querySelector('#modifier-select-list');
const botForm = document.querySelector('#bot-form');
const botStatus = document.querySelector('#bot-status');
const categorySelect = document.querySelector('#menu-form select[name="category"]');

const state = {
  categories: [],
  menuItems: [],
  modifiers: [],
};

const storageKey = 'deliverybot-pro-demo';
const clientKey = 'deliverybot-pro-client';

const saveState = () => {
  localStorage.setItem(storageKey, JSON.stringify(state));
};

const getClientId = () => {
  const existing = localStorage.getItem(clientKey);
  if (existing) return existing;
  const newId = `client_${Math.random().toString(36).slice(2, 10)}`;
  localStorage.setItem(clientKey, newId);
  return newId;
};

const updateBotStatus = (message) => {
  if (!botStatus) return;
  botStatus.textContent = message;
};

const seedDefaults = () => {
  state.categories = ['Пицца', 'Роллы', 'Закуски'];
  state.modifiers = [
    { title: 'Размер пиццы', options: ['25 см', '30 см', '35 см'], priceDelta: ['+0', '+120', '+240'] },
    { title: 'Роллы', options: ['6 шт', '8 шт', '12 шт'], priceDelta: ['+0', '+90', '+180'] },
    { title: 'Закуски', options: ['3 шт', '6 шт', '9 шт', '12 шт'], priceDelta: ['+0', '+70', '+140', '+210'] },
  ];
  state.menuItems = [];
};

const loadState = () => {
  const saved = localStorage.getItem(storageKey);
  if (!saved) {
    seedDefaults();
    saveState();
    return;
  }
  const parsed = JSON.parse(saved);
  state.categories = parsed.categories || [];
  state.menuItems = parsed.menuItems || [];
  state.modifiers = parsed.modifiers || [];
  if (state.categories.length === 0 && state.modifiers.length === 0) {
    seedDefaults();
    saveState();
  }
};

const renderCategories = () => {
  categoryList.innerHTML = '';
  categorySelect.innerHTML = '<option value="">Выберите категорию</option>';

  state.categories.forEach((category) => {
    const item = document.createElement('li');
    item.textContent = category;
    categoryList.appendChild(item);

    const option = document.createElement('option');
    option.value = category;
    option.textContent = category;
    categorySelect.appendChild(option);
  });
};

const renderMenuItems = () => {
  menuList.innerHTML = '';
  state.menuItems.forEach((menuItem) => {
    const item = document.createElement('li');
    const modifiers = menuItem.modifiers?.length
      ? `Модификаторы: ${menuItem.modifiers.join(', ')}`
      : 'Модификаторы: не выбраны';
    item.innerHTML = `
      <strong>${menuItem.name}</strong>
      <span>${menuItem.category}</span>
      <span>${menuItem.price} ₽</span>
      <span class="hint">${modifiers}</span>
      <span class="hint">${menuItem.description || 'Без описания'}</span>
    `;
    menuList.appendChild(item);
  });
};

const renderModifierOptions = () => {
  modifierSelectList.innerHTML = '';
  state.modifiers.forEach((modifier, index) => {
    const label = document.createElement('label');
    label.className = 'pill checkbox-pill';
    label.innerHTML = `
      <input type="checkbox" name="menuModifier" value="${index}" />
      ${modifier.title}
    `;
    modifierSelectList.appendChild(label);
  });
};

const renderModifiers = () => {
  modifierList.innerHTML = '';
  state.modifiers.forEach((modifier) => {
    const item = document.createElement('li');
    item.innerHTML = `
      <strong>${modifier.title}</strong>
      <span>${modifier.options.join(', ')}</span>
      <span class="hint">${modifier.priceDelta.join(', ') || 'Без доплат'}</span>
    `;
    modifierList.appendChild(item);
  });
};

const renderAll = () => {
  renderCategories();
  renderMenuItems();
  renderModifiers();
  renderModifierOptions();
};

const handleTabClick = (event) => {
  const target = event.currentTarget.dataset.tab;
  tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.tab === target));
  panels.forEach((panel) => panel.classList.toggle('active', panel.id === target));
};

tabs.forEach((tab) => {
  tab.addEventListener('click', handleTabClick);
});

categoryForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(categoryForm);
  const category = formData.get('category').trim();
  if (!category || state.categories.includes(category)) return;
  state.categories.push(category);
  saveState();
  renderAll();
  categoryForm.reset();
});

menuForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(menuForm);
  const name = formData.get('name').trim();
  const category = formData.get('category');
  const price = Number(formData.get('price'));
  const description = formData.get('description').trim();
  const selectedModifiers = Array.from(
    menuForm.querySelectorAll('input[name="menuModifier"]:checked'),
  ).map((input) => state.modifiers[Number(input.value)]?.title);

  if (!name || !category || Number.isNaN(price)) return;

  state.menuItems.push({
    name,
    category,
    price,
    description,
    modifiers: selectedModifiers.filter(Boolean),
  });
  saveState();
  renderMenuItems();
  menuForm.reset();
});

modifierForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const formData = new FormData(modifierForm);
  const title = formData.get('title').trim();
  const options = formData
    .get('options')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
  const priceDelta = formData
    .get('priceDelta')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

  if (!title || options.length === 0) return;

  state.modifiers.push({
    title,
    options,
    priceDelta,
  });
  saveState();
  renderModifiers();
  renderModifierOptions();
  modifierForm.reset();
});

loadState();
renderAll();

if (botForm) {
  botForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(botForm);
    const token = formData.get('botToken').trim();
    if (!token) return;
    updateBotStatus('Подключаем бота…');
    try {
      const response = await fetch('/api/bot/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId: getClientId(), token }),
      });
      const result = await response.json();
      if (!response.ok) {
        updateBotStatus('Ошибка подключения. Проверьте токен.');
        return;
      }
      updateBotStatus(`Статус: ${result.status}`);
    } catch (error) {
      updateBotStatus('Не удалось связаться с сервером.');
    }
  });
}

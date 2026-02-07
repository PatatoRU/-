const tabs = document.querySelectorAll('.tab-button');
const panels = document.querySelectorAll('.panel');

const handleTabClick = (event) => {
  const target = event.currentTarget.dataset.tab;
  tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.tab === target));
  panels.forEach((panel) => panel.classList.toggle('active', panel.id === target));
};

tabs.forEach((tab) => {
  tab.addEventListener('click', handleTabClick);
});

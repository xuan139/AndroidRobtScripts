const prices = [99, 35, 45, 150];

function updateTotalPrice() {
  let total = 0;
  for (let i = 1; i <= prices.length; i++) {
    const qty = parseInt(document.getElementById(`quantity${i}`).value);
    total += prices[i - 1] * qty;
  }
  document.getElementById("totalPrice").innerText = `총 금액: ${total}원`;
}

// 地图
const map = L.map('map').setView([25.0523, 121.5325], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);
L.marker([25.0523, 121.5325]).addTo(map)
  .bindPopup('台北市中山区 餐厅位置')
  .openPopup();

// 语言切换（示意）
document.getElementById('languageToggle').addEventListener('click', () => {
  alert("语言切换功能暂未实现完整，仅为演示按钮。");
});

// 自动语音播报推荐内容
function speak(text) {
  if (!window.speechSynthesis) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'zh-CN';
  window.speechSynthesis.cancel(); // 取消正在播报的
  window.speechSynthesis.speak(utterance);
}

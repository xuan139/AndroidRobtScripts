// const menuUrl = 'https://raw.githubusercontent.com/xuan139/AndroidRobtScripts/main/menu.json'

let cart = [];
let menuItems = [];
let currentLanguage = 'ko'; // 默认韩语

// https://raw.githubusercontent.com/xuan139/AndroidRobtScripts/main/menu.json
// 获取菜单数据
  fetch("../static/db/menu.json")
    .then(response => response.json())
    .then(data => {
      menuItems = data;
      renderMenu(menuItems);
    })
    .catch(error => console.error("Error fetching menu:", error));

  // 监听语言切换
  document.getElementById('languageSelector').addEventListener('change', function (event) {
    updateMenuLanguage(event.target.value);
  });

  // 切换语言，仅控制 currentLanguage 不修改原始数据
  function updateMenuLanguage(lang) {
    currentLanguage = lang;
    renderMenu(menuItems);
  }


    function renderMenu(items) {
      const menuSection = document.getElementById('menuContainer');
      menuSection.innerHTML = '';

      items.forEach((item, index) => {
        const name = item[`name_${currentLanguage}`] || item.name_ko;
        const id = item.id || `00${index + 1}`;
        const existing = cart.find(ci => ci.id === id);
        const quantity = existing ? existing.quantity : 0;

        const cardHtml = `
          <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm">
              <img src="${item.image}" class="card-img-top" alt="dish">
              <div class="card-body">
                <h5 class="text-muted">${id}</h5>
                <h5 class="card-title">${name}</h5>
                <p><strong>₩${item.price}</strong></p>
              </div>
              <div class="card-footer d-flex justify-content-between align-items-center">
                <div>
                  <button class="btn btn-sm btn-outline-secondary" onclick="decreaseQuantity('${id}')">-</button>
                  <span id="quantity-${id}" class="mx-2">${quantity}</span>
                  <button class="btn btn-sm btn-outline-secondary" onclick="increaseQuantity('${id}')">+</button>
                </div>
              </div>
            </div>
          </div>
        `;

        menuSection.innerHTML += cardHtml;
      });
    }



    function increaseQuantity(id) {
      const item = menuItems.find(it => it.id === id);
      if (!item) return;
    
      const existing = cart.find(ci => ci.id === id);
    
      if (existing) {
        existing.quantity++;
      } else {
        cart.push({ id, name: item.name_ko, price: item.price, quantity: 1 });
      }
    
      document.getElementById(`quantity-${id}`).textContent = existing ? existing.quantity : 1;
      renderCartSummary();
    }
    
    function decreaseQuantity(id) {
      const existing = cart.find(ci => ci.id === id);
      if (existing) {
        existing.quantity--;
        if (existing.quantity <= 0) {
          cart = cart.filter(ci => ci.id !== id);
          document.getElementById(`quantity-${id}`).textContent = 0;
        } else {
          document.getElementById(`quantity-${id}`).textContent = existing.quantity;
        }
      }
      renderCartSummary();
    }
  
    function renderCartSummary() {
      const cartItemsContainer = document.getElementById('cartItems');
      const cartTotalElement = document.getElementById('subtotal');
      cartItemsContainer.innerHTML = '';

      let total = 0;

      cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;

        const li = document.createElement('li');
        li.className = 'list-group-item d-flex justify-content-between align-items-center';
        li.innerHTML = `${item.id} : ${item.name} x ${item.quantity} <span>₩${itemTotal}</span>`;
        cartItemsContainer.appendChild(li);
      });

      cartTotalElement.textContent = `₩${total}`;
    }



  function cancelOrder() {
    // 清空购物车
    cart = [];
    resetCart();
    // 清空订单条目
    document.getElementById('cartItems').innerHTML = '';
    document.getElementById('subtotal').textContent = '₩0';

    // 清空小票内容
    document.getElementById('receiptContent').textContent = '';

    // 隐藏小票区域
    const receiptSection = document.getElementById('receiptSection');
    receiptSection.classList.add('d-none');  // 隐藏小票区
    receiptSection.style.display = 'none';  // 确保强制隐藏
  }


  // 清空购物车并更新界面
  function resetCart() {
    // 清空购物车数组
    cart = [];

    menuItems.forEach(item => {
      const qtyEl = document.getElementById(`quantity-${item.id}`);
      if (qtyEl) qtyEl.innerText = "0";
    });

    // 清空订单摘要和金额
    const cartItemsContainer = document.getElementById('cartItems');
    cartItemsContainer.innerHTML = '';
    
    const cartTotalElement = document.getElementById('subtotal');
    cartTotalElement.textContent = '₩0';
  }

  // 确认订单并清空购物车
  // function confirmOrder() {
  //   alert("🧾 Sent Orders！");
  //   resetCart();  // 调用清空购物车功能
  // }

  function dedent(str) {
    return str.replace(/^[ \t]+/gm, '');
  }


  function confirmOrder() {
    // 固定收银员名字为 "wang"
    const cashierName = "wang";

    // 获取当前时间
    const orderTime = new Date().toLocaleString(); // 获取当前时间（格式化）

    // 更新订单摘要
    let receiptContent = dedent(`
      🧾 Receipt
      -----------------------
      Table: 1
      -----------------------
      Date: ${orderTime}
      Cashier: ${cashierName}
      -----------------------
      Order Details:
      -----------------------
    `);

    // 添加每个菜品
    cart.forEach(item => {
      const itemTotal = item.price * item.quantity;
      receiptContent += `${item.id}:${item.name} x ${item.quantity} = ₩${itemTotal}\n`;
    });

    // 总计
    const totalAmount = cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    receiptContent += `-----------------------\nTotal: ₩${totalAmount}\n\n\n`;
    receiptContent += `Address: 서울 송파구 석촌호수로 110\n`;
    receiptContent += `Tel: 050714181022\n`;
    // 显示小票内容
    document.getElementById('receiptContent').textContent = receiptContent;

    // 显示小票区
    const receiptSection = document.getElementById('receiptSection');
    receiptSection.classList.remove('d-none');  // 显示小票区
    receiptSection.style.display = 'block'; // 确保小票显示

    const tableNumber = 1; // 可以改成动态选择的桌号
    submitOrder(tableNumber);
  }

  // 取消订单并清空购物车
  function cancelOrder() {
    resetCart();  // 调用清空购物车功能
    clearReceipt(); // 清除小票内容并隐藏区域
  }

  // 发送订单
  function sendOrder() {
    alert("📤 订单已发送到餐馆！");
  }

  function submitOrder(tableNumber) {
    const orderData = {
      table: tableNumber,
      orders: cart.map(item => ({
        name: item.name,
        quantity: item.quantity,
        price: item.price
      })),
      total: cart.reduce((acc, item) => acc + item.price * item.quantity, 0),
      timestamp: new Date().toLocaleString(), // 获取当前时间
      cashier: "wang" // 假设收银员固定为"wang"
    };

    // 将订单数据保存到 localStorage 中
    localStorage.setItem(`table-${tableNumber}`, JSON.stringify(orderData));
  }


  function showReceipt() {
    let receipt = "🧾 Table 1 Receipt\n\n";
    let total = 0;

    cart.forEach(item => {
      const lineTotal = item.price * item.quantity;
      total += lineTotal;

      // 名称加上规格（如 小/大），用 padEnd 补齐长度
      const name = (item.name + (item.spec || '')).padEnd(18, ' ');
      const qty = `x ${item.quantity}`.padEnd(6, ' ');
      const price = `= ₩${lineTotal}`;

      receipt += `${name}${qty}${price}\n`;
    });

    receipt += `\nTotal: ₩${total}`;
    document.getElementById('receiptContent').textContent = receipt;

    // 👉 取消隐藏
    document.getElementById('receiptSection').classList.remove('d-none');
  }

  function clearReceipt() {
    document.getElementById('receiptContent').textContent = '';
    document.getElementById('receiptSection').classList.add('d-none');
  }

  function printReceipt() {
    const receiptText = document.getElementById('receiptContent').textContent;
    const printWindow = window.open('', '', 'width=400,height=600');
    printWindow.document.write('<pre>' + receiptText + '</pre>');
    printWindow.document.close();
    printWindow.print();
  }
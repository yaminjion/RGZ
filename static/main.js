window.isLoggedIn = document.body.innerHTML.includes('Привет,');

async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
    };
    if (data) options.body = JSON.stringify(data);
    const res = await fetch(url, options);
    if (!res.ok) {
        throw new Error(`Ошибка: ${res.status}`);
    }
    return await res.json();
}

// Главная страница
if (document.getElementById('product-list')) {
    loadProducts();

    async function loadProducts() {
        try {
            const productsRes = await apiCall('/api/products');
            let cartIds = new Map();
            if (window.isLoggedIn) {
                const cartRes = await apiCall('/api/cart/items');
                for (const item of cartRes.items) {
                    cartIds.set(item.product_id, item.quantity);
                }
            }
            const list = document.getElementById('product-list');
            list.innerHTML = productsRes.map(p => `
                <div class="product-card">
                    <img src="/static/${p.image_filename}" class="product-image" alt="${p.name}">
                    <div class="product-card-content">
                        <div class="product-name">${p.name}</div>
                        <div class="product-price">${p.price.toFixed(2)} ₽</div>
                        ${window.isLoggedIn ? (
                            cartIds.has(p.id)
                                ? `<div class="in-cart">в корзине</div>
                                   <div class="qty-container">
                                       <button class="qty-btn" onclick="changeQty(${p.id}, -1)">–</button>
                                       <span style="font-weight: bold;">${cartIds.get(p.id)}</span>
                                       <button class="qty-btn" onclick="changeQty(${p.id}, 1)">+</button>
                                   </div>`
                                : `<button onclick="addToCart(${p.id})">в корзину</button>`
                        ) : ''}
                    </div>
                </div>
            `).join('');
        } catch (e) {
            console.error(e);
            const list = document.getElementById('product-list');
            if (list) {
                list.innerHTML = '<p style="grid-column:1/-1;text-align:center;">Ошибка загрузки товаров (>_<)</p>';
            }
        }
    }

    window.addToCart = async (id) => {
        if (!window.isLoggedIn) {
            alert('Требуется авторизация! (>_<)');
            return;
        }
        try {
            await apiCall('/api/cart/add', 'POST', { product_id: id });
            loadProducts();
        } catch (e) {
            alert('Ошибка добавления в корзину (>_<)');
        }
    };

    window.changeQty = async (id, delta) => {
        try {
            await apiCall('/api/cart/change', 'POST', { product_id: id, delta });
            loadProducts();
        } catch (e) {
            alert('Ошибка изменения количества (>_<)');
        }
    };
}

// Вход
if (document.getElementById('login-form')) {
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const login = document.getElementById('login-input').value;
        const password = document.getElementById('password-input').value;
        try {
            const res = await apiCall('/api/auth/login', 'POST', { login, password });
            if (res.status === 'ok') {
                window.location.href = '/';
            } else {
                alert(res.message + ' (>_<)');
            }
        } catch (e) {
            alert('Ошибка входа (>_<)');
        }
    });
}

// Регистрация
if (document.getElementById('register-form')) {
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const login = document.getElementById('reg-login').value;
        const password = document.getElementById('reg-password').value;
        try {
            const res = await apiCall('/api/auth/register', 'POST', { login, password });
            if (res.status === 'ok') {
                window.location.href = '/';
            } else {
                alert(res.message + ' (>_<)');
            }
        } catch (e) {
            alert('Ошибка регистрации (>_<)');
        }
    });
}

// Корзина
if (document.getElementById('cart-items')) {
    loadCart();

    async function loadCart() {
        try {
            const res = await apiCall('/api/cart/items');
            const list = document.getElementById('cart-items');
            const totalEl = document.getElementById('total');
            const checkoutBtn = document.getElementById('checkout-btn');
            if (res.items.length === 0) {
                list.innerHTML = '<tr><td colspan="5" style="text-align:center;">Корзина пуста... (｡•́︿•̀｡)</td></tr>';
                totalEl.textContent = '0.00';
                checkoutBtn.style.display = 'none';
            } else {
                list.innerHTML = res.items.map(i => `
                    <tr>
                        <td>${i.name}</td>
                        <td>${i.price.toFixed(2)} ₽</td>
                        <td>${i.quantity}</td>
                        <td>${i.total.toFixed(2)} ₽</td>
                        <td><button onclick="removeFromCart(${i.product_id})">Удалить</button></td>
                    </tr>
                `).join('');
                totalEl.textContent = res.total.toFixed(2);
                checkoutBtn.style.display = 'inline-block';
            }
        } catch (e) {
            console.error(e);
            document.getElementById('cart-items').innerHTML = '<tr><td colspan="5" style="text-align:center;">Ошибка загрузки корзины (>_<)</td></tr>';
        }
    }

    window.removeFromCart = async (id) => {
        try {
            await apiCall('/api/cart/remove', 'POST', { product_id: id });
            loadCart();
        } catch (e) {
            alert('Ошибка удаления (>_<)');
        }
    };
}

// Оформление заказа
if (document.getElementById('checkout-form')) {
    document.getElementById('checkout-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = {
            name: formData.get('name'),
            card: formData.get('card'),
            cvv: formData.get('cvv'),
            city: formData.get('city'),
            street: formData.get('street'),
            house: formData.get('house'),
            apartment: formData.get('apartment')
        };
        try {
            const res = await apiCall('/api/checkout', 'POST', data);
            if (res.status === 'ok') {
                const resultDiv = document.getElementById('checkout-result');
                resultDiv.style.display = 'block';
                resultDiv.textContent = 'Заказ оформлен! (◕‿◕)';
                e.target.reset();
                setTimeout(() => {
                    window.location.href = '/';
                }, 3000);
            } else {
                document.getElementById('checkout-result').style.display = 'block';
                document.getElementById('checkout-result').textContent = res.message + ' (>_<)';
            }
        } catch (e) {
            document.getElementById('checkout-result').style.display = 'block';
            document.getElementById('checkout-result').textContent = 'Ошибка оформления (>_<)';
        }
    });
}

// Выход
window.logout = async () => {
    try {
        await apiCall('/api/auth/logout', 'POST');
        window.location.href = '/';
    } catch (e) {
        alert('Ошибка выхода (>_<)');
    }
};
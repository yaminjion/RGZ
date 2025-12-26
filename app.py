# app.py
import os
import re
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'RGZ-mebel-2025'

dir_path = Path(__file__).parent
db_path = dir_path / 'furniture_shop.db'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(100), nullable=False)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def is_valid_login(login):
    return bool(re.match(r'^[a-zA-Z0-9_-]{3,30}$', login))

@app.before_request
def init_db():
    if not hasattr(app, '_db_initialized'):
        with app.app_context():
            db.create_all()
            if Product.query.count() == 0:
                products_data = [
                    # Детская мебель
                    ("FLINTAN", "Удобный и безопасный стул для ребёнка.", 8900, "детскийстул.jpg"),
                    ("SMÅSTOK", "Модный стул с эргономичной формой.", 9500, "детскийстул2.jpg"),

                    # Диваны
                    ("MILLBERGET", "Современный диван с хромированными ножками.", 42900, "диван.jpg"),
                    ("KIVIK", "Компактный диван для малогабаритных квартир.", 38500, "диван3.jpg"),
                    ("SÖDERHAMN", "Просторный диван для гостиной.", 52000, "диванбольшой.jpg"),
                    ("POÄNG ROUND", "Необычный диван-кокон для уютного отдыха.", 65000, "диванкруг.jpg"),

                    # Зеркала
                    ("HOVET SET", "Набор из 5 зеркал в серебряных рамах.", 12000, "зеркала круглые.jpg"),
                    ("LILLÅNGEN", "Овальное зеркало в форме капли воды.", 15800, "зеркало капля.jpg"),
                    ("NISSEDAL", "Прямоугольное зеркало с тонкой рамой.", 11200, "зеркало1.jpg"),

                    # Кресла
                    ("POÄNG", "Кресло-качалка с эффектом «облака».", 18500, "качалка.jpg"),
                    ("EKTORP", "Элегантное кресло для кабинета.", 22000, "кресло2.jpg"),
                    ("KARLANDA", "Роскошное кресло в стиле ар-нуво.", 28000, "кресло3.jpg"),
                    ("STRANDMON", "Подвесное кресло-шар из прозрачного акрила.", 35000, "креслошар.jpg"),
                    ("TARVA", "Шаровое кресло с подушкой.", 37000, "креслошар2.jpg"),
                    ("VIKARE", "Гигантское шаровое кресло.", 45000, "креслошар3.jpg"),
                    ("LÖVBACKEN", "Розовое кресло-шар для романтиков.", 42000, "креслошар4.jpg"),

                    # Комоды
                    ("MALM", "Комод с 5 ящиками и зеркалом.", 25000, "комод.jpg"),
                    ("HEMNES", "Роскошный комод в стиле барокко.", 32000, "комод2.jpg"),

                    # Лампы
                    ("HEKTAR", "Лампа с розовым абажуром и металлической основой.", 9800, "лампа.jpg"),

                    # Столы
                    ("INGATORP", "Обеденный стол + 4 стула.", 48000, "стол со стульями.jpg"),
                    ("LACK", "Журнальный столик с матовым стеклом.", 12000, "столжурнал.jpg"),
                    ("NORDVIKEN", "Столик на ножках в виде ангелов.", 18000, "столик ангелы.jpg"),
                    ("RANARP", "Мини-столик для чая или книг.", 8500, "столик.jpg"),
                    ("BRIMNES", "Набор из 3 столиков разного размера.", 22000, "столы3.jpg"),

                    # Стулья
                    ("ADDE", "Барский стул с высокой спинкой.", 15000, "стул барский.jpg"),
                    ("JOKKMOKK", "Стул из прозрачного акрила.", 13000, "стул голубой.jpg"),
                    ("TÖRNVIKEN", "Минималистичный стул с изогнутыми ножками.", 11000, "стул.jpg"),
                    ("SKRUVSTA", "Современный стул с хромированными ножками.", 14000, "стул4.jpg"),

                    # Табуреты
                    ("PALL", "Табурет с мягким сиденьем.", 7500, "табурет.jpg"),
                    ("ÖRFJÄLL", "Дизайнерская табуретка в форме куба.", 9000, "табуретка.jpg"),

                    # Пуфики и остальное
                    ("KALLAX", "Пуфики-трансформеры.", 9800, "серебро_пуфики.jpg"),
                    ("APPLARÖ", "Садовая лавка с алюминиевым каркасом.", 15200, "серебро_лавка.jpg"),
                    ("SÖDERHAMN CHAIR", "Удобное кресло с эффектом «облака».", 18500, "серебро_кресло.jpg"),
                    ("MARKUS", "Эргономичное кресло с поддержкой поясницы.", 21400, "серебро_кресло2.jpg"),
                ]
                for name, desc, price, img in products_data:
                    db.session.add(Product(name=name, description=desc, price=price, image_filename=img))
                db.session.commit()
        app._db_initialized = True

# === Страницы ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/cart')
@login_required
def cart():
    return render_template('cart.html')

@app.route('/checkout')
@login_required
def checkout():
    return render_template('checkout.html')

# === API ===
@app.route('/api/products')
def api_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'price': p.price,
        'image_filename': p.image_filename
    } for p in products])

@app.route('/api/cart/items')
@login_required
def api_cart_items():
    items = db.session.query(CartItem, Product).join(Product).filter(CartItem.user_id == current_user.id).all()
    total = sum(item.Product.price * item.CartItem.quantity for item in items)
    return jsonify({
        'items': [{
            'product_id': item.Product.id,
            'name': item.Product.name,
            'price': item.Product.price,
            'quantity': item.CartItem.quantity,
            'total': item.Product.price * item.CartItem.quantity
        } for item in items],
        'total': total
    })

@app.route('/api/cart/add', methods=['POST'])
@login_required
def api_add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'status': 'error', 'message': 'Не указан товар.'})
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        item.quantity += 1
    else:
        item = CartItem(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(item)
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/cart/remove', methods=['POST'])
@login_required
def api_remove_from_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).delete()
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/cart/change', methods=['POST'])
@login_required
def api_change_cart_qty():
    data = request.get_json()
    product_id = data.get('product_id')
    delta = data.get('delta', 0)
    try:
        delta = int(delta)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Неверное количество.'})
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        item.quantity += delta
        if item.quantity <= 0:
            db.session.delete(item)
        db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    login = data.get('login', '').strip()
    password = data.get('password', '')
    if not login or not password:
        return jsonify({'status': 'error', 'message': 'Логин и пароль обязательны.'})
    if not is_valid_login(login):
        return jsonify({'status': 'error', 'message': 'Логин: латиница, цифры, _ и -, от 3 до 30 символов.'})
    if User.query.filter_by(login=login).first():
        return jsonify({'status': 'error', 'message': 'Такой логин уже существует.'})
    user = User(login=login, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'status': 'ok'})

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    login = data.get('login', '').strip()
    password = data.get('password', '')
    user = User.query.filter_by(login=login).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error', 'message': 'Неверный логин или пароль.'})

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    logout_user()
    return jsonify({'status': 'ok'})

# Валидация адреса
def validate_address(city, street, house, apartment):
    errors = []

    # Город: только буквы, пробелы, дефисы, апострофы
    if not city or not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-']+$", city):
        errors.append("Город должен содержать только буквы, пробелы, дефисы или апострофы.")
    
    # Улица: буквы, цифры, пробелы, дефисы, точки
    if not street or not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-.'/#]+$", street):
        errors.append("Улица может содержать буквы, цифры, пробелы, дефисы, точки, # и /.")

    # Дом: цифры, слэш, дефис, буквы в конце (например: 33, 33/1, 12-А)
    if not house or not re.match(r"^\d+[/\-]?\d*[А-Яа-яA-Za-z]?$", house):
        errors.append("Номер дома должен быть числом (например: 33, 33/1, 12-А).")

    # Квартира: цифры, слэш, дефис (опционально)
    if apartment and not re.match(r"^\d+[/\-]?\d*$", apartment):
        errors.append("Номер квартиры должен быть числом (например: 15, 15/2).")

    return errors

@app.route('/api/checkout', methods=['POST'])
@login_required
def api_checkout():
    data = request.get_json()
    card = re.sub(r'\D', '', data.get('card', ''))
    cvv = data.get('cvv', '')
    name = data.get('name', '').strip()
    city = data.get('city', '').strip()
    street = data.get('street', '').strip()
    house = data.get('house', '').strip()
    apartment = data.get('apartment', '').strip()

    # Валидация карты
    if len(card) != 16:
        return jsonify({'status': 'error', 'message': 'Неверный номер карты (должно быть 16 цифр).'})
    if len(cvv) != 3 or not cvv.isdigit():
        return jsonify({'status': 'error', 'message': 'Неверный CVV (3 цифры).'})
    if not name:
        return jsonify({'status': 'error', 'message': 'Укажите имя на карте.'})

    # Валидация адреса
    address_errors = validate_address(city, street, house, apartment)
    if address_errors:
        return jsonify({'status': 'error', 'message': ' '.join(address_errors)})

    # Сохранение заказа
    CartItem.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)
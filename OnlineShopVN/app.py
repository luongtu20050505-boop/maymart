from __future__ import annotations

import os
import re
import sqlite3
import secrets
from datetime import datetime
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
DB_PATH = INSTANCE_DIR / "shop.db"

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key"),
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

CATEGORIES = ["Điện thoại & Công nghệ", "Thời trang", "Nhà cửa & Đời sống", "Làm đẹp", "Thể thao"]
SHIPPING_FEE = 30000
FREE_SHIP_THRESHOLD = 500000
COUPONS = {
    "WELCOME10": {"type": "percent", "value": 10, "min": 100000, "label": "Giảm 10% cho đơn từ 100.000đ"},
    "FREESHIP": {"type": "shipping", "value": SHIPPING_FEE, "min": 150000, "label": "Miễn phí vận chuyển cho đơn từ 150.000đ"},
    "SAVE50K": {"type": "fixed", "value": 50000, "min": 500000, "label": "Giảm 50.000đ cho đơn từ 500.000đ"},
}

PRODUCT_SEEDS = [
    ("Tai nghe không dây AirBeat Pro", "Điện thoại & Công nghệ", "Âm thanh sống động, chống ồn chủ động, pin đến 30 giờ. Thiết kế gọn nhẹ cho công việc và giải trí.", 1290000, 1690000, 36, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=1000&q=85", "BÁN CHẠY"),
    ("Đồng hồ thông minh Active S", "Điện thoại & Công nghệ", "Theo dõi vận động, nhịp tim và giấc ngủ. Màn hình sáng rõ, kháng nước khi tập luyện.", 890000, 1190000, 24, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1000&q=85", "GIẢM GIÁ"),
    ("Áo thun cotton Premium", "Thời trang", "Chất cotton mềm thoáng, phom dáng hiện đại, dễ phối đồ hằng ngày. Có nhiều màu sắc.", 189000, 259000, 80, "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=1000&q=85", "YÊU THÍCH"),
    ("Túi đeo chéo Urban Daily", "Thời trang", "Túi gọn nhẹ với nhiều ngăn tiện dụng, chất liệu bền đẹp phù hợp đi học và đi làm.", 329000, 429000, 42, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1000&q=85", "HOT"),
    ("Đèn bàn LED Minimal", "Nhà cửa & Đời sống", "Ánh sáng dịu, điều chỉnh nhiều mức sáng, kiểu dáng tối giản cho góc học tập và làm việc.", 249000, 349000, 31, "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=1000&q=85", "MỚI"),
    ("Bình giữ nhiệt Eco 600ml", "Nhà cửa & Đời sống", "Giữ nóng và lạnh hiệu quả, thiết kế dễ mang theo. Vật liệu bền bỉ cho nhu cầu mỗi ngày.", 179000, 239000, 65, "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=1000&q=85", "BÁN CHẠY"),
    ("Serum dưỡng da Glow", "Làm đẹp", "Kết cấu mỏng nhẹ, hỗ trợ cấp ẩm và giúp da trông tươi sáng. Dùng theo hướng dẫn trên bao bì.", 289000, 369000, 27, "https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=1000&q=85", "ƯU ĐÃI"),
    ("Bộ chăm sóc da Daily Care", "Làm đẹp", "Bộ chăm sóc cơ bản dành cho quy trình hằng ngày, đóng gói chỉn chu, tiện làm quà tặng.", 459000, 599000, 19, "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=1000&q=85", "QUÀ TẶNG"),
    ("Giày chạy bộ FlexRun", "Thể thao", "Đế êm, trọng lượng nhẹ, hỗ trợ vận động hằng ngày và các buổi chạy nhẹ nhàng.", 690000, 890000, 22, "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=1000&q=85", "HOT"),
    ("Thảm yoga Comfort", "Thể thao", "Bề mặt bám tốt, dễ cuộn và mang theo, phù hợp tập yoga, giãn cơ tại nhà.", 259000, 329000, 38, "https://images.unsplash.com/photo-1592432678016-e910b452f9a2?auto=format&fit=crop&w=1000&q=85", "MỚI"),
    ("Bàn phím cơ Nova 87", "Điện thoại & Công nghệ", "Bàn phím cơ layout gọn, cảm giác gõ rõ ràng, phù hợp làm việc và chơi game.", 799000, 990000, 18, "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=1000&q=85", "GIẢM GIÁ"),
    ("Balo laptop WorkMate", "Thời trang", "Ngăn laptop riêng, nhiều ngăn tiện dụng và quai đeo êm, phù hợp đi học hoặc công sở.", 549000, 699000, 26, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1000&q=85", "BÁN CHẠY"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  phone TEXT DEFAULT '',
  address TEXT DEFAULT '',
  role TEXT NOT NULL DEFAULT 'customer',
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  price INTEGER NOT NULL CHECK(price >= 0),
  original_price INTEGER NOT NULL DEFAULT 0,
  stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
  image TEXT NOT NULL DEFAULT '',
  badge TEXT DEFAULT '',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_code TEXT NOT NULL UNIQUE,
  user_id INTEGER NOT NULL,
  receiver_name TEXT NOT NULL,
  phone TEXT NOT NULL,
  address TEXT NOT NULL,
  payment_method TEXT NOT NULL,
  subtotal INTEGER NOT NULL,
  shipping_fee INTEGER NOT NULL,
  discount INTEGER NOT NULL DEFAULT 0,
  total INTEGER NOT NULL,
  coupon_code TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'Chờ xác nhận',
  note TEXT DEFAULT '',
  created_at TEXT NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS order_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  product_id INTEGER,
  product_name TEXT NOT NULL,
  product_image TEXT DEFAULT '',
  price INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  FOREIGN KEY(order_id) REFERENCES orders(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
  comment TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  UNIQUE(user_id, product_id),
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE TABLE IF NOT EXISTS wishlists (
  user_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(user_id, product_id),
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(product_id) REFERENCES products(id)
);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
"""


def connect_db():
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def get_db():
    if "db" not in g:
        g.db = connect_db()
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def make_slug(name: str) -> str:
    import unicodedata
    value = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "san-pham"
    return f"{value}-{secrets.token_hex(3)}"


def init_db():
    db = connect_db()
    db.executescript(SCHEMA)
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        for name, category, desc, price, original, stock, image, badge in PRODUCT_SEEDS:
            db.execute(
                "INSERT INTO products(name,slug,category,description,price,original_price,stock,image,badge,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (name, make_slug(name), category, desc, price, original, stock, image, badge, now_text()),
            )
    if not db.execute("SELECT 1 FROM users WHERE email=?", ("admin@shopdemo.vn",)).fetchone():
        db.execute(
            "INSERT INTO users(name,email,password_hash,phone,address,role,created_at) VALUES(?,?,?,?,?,?,?)",
            ("Quản trị viên", "admin@shopdemo.vn", generate_password_hash("Admin@123"), "", "", "admin", now_text()),
        )
    db.commit()
    db.close()


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return get_db().execute("SELECT id,name,email,phone,address,role,created_at FROM users WHERE id=?", (user_id,)).fetchone()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            flash("Vui lòng đăng nhập để tiếp tục nhé.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Hãy đăng nhập bằng tài khoản quản trị.", "info")
            return redirect(url_for("login", next=request.path))
        if user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def price_text(value):
    return f"{int(value or 0):,}".replace(",", ".") + "₫"


@app.template_filter("money")
def money_filter(value):
    return price_text(value)


@app.context_processor
def inject_globals():
    user = get_current_user()
    cart = session.get("cart", {})
    try:
        cart_count = sum(max(0, int(v)) for v in cart.values())
    except (AttributeError, TypeError, ValueError):
        cart_count = 0
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)
    return {"current_user": user, "cart_count": cart_count, "csrf_token": session["csrf_token"],
            "categories": CATEGORIES, "now_year": datetime.now().year}


@app.before_request
def protect_post_forms():
    if request.method == "POST":
        expected = session.get("csrf_token")
        submitted = request.form.get("csrf_token")
        if not expected or not submitted or not secrets.compare_digest(expected, submitted):
            abort(400, description="Phiên biểu mẫu đã hết hạn. Vui lòng tải lại trang rồi thử lại.")


def cart_rows():
    db = get_db()
    cart = session.get("cart", {})
    ids = []
    for key in cart:
        try:
            ids.append(int(key))
        except (TypeError, ValueError):
            continue
    if not ids:
        return [], 0
    placeholders = ",".join("?" for _ in ids)
    products = db.execute(f"SELECT * FROM products WHERE id IN ({placeholders}) AND active=1", ids).fetchall()
    rows = []
    total = 0
    for product in products:
        qty = max(1, min(99, int(cart.get(str(product["id"]), 1))))
        line_total = product["price"] * qty
        rows.append({"product": product, "quantity": qty, "line_total": line_total})
        total += line_total
    return rows, total


def checkout_math(subtotal, coupon_code=""):
    shipping = 0 if subtotal >= FREE_SHIP_THRESHOLD else SHIPPING_FEE
    discount = 0
    coupon_code = (coupon_code or "").strip().upper()
    coupon = COUPONS.get(coupon_code)
    if coupon and subtotal >= coupon["min"]:
        if coupon["type"] == "percent":
            discount = int(subtotal * coupon["value"] / 100)
        elif coupon["type"] == "fixed":
            discount = min(coupon["value"], subtotal)
        elif coupon["type"] == "shipping":
            shipping = 0
    else:
        coupon = None
    total = max(0, subtotal + shipping - discount)
    return shipping, discount, total, coupon


def safe_external_image(value):
    parsed = urlparse((value or "").strip())
    return parsed.scheme in ("https", "http") and bool(parsed.netloc)


@app.route("/")
def index():
    db = get_db()
    featured = db.execute("SELECT p.*, COALESCE(AVG(r.rating),0) AS avg_rating, COUNT(r.id) AS review_count FROM products p LEFT JOIN reviews r ON r.product_id=p.id WHERE p.active=1 GROUP BY p.id ORDER BY p.id DESC LIMIT 8").fetchall()
    popular = db.execute("SELECT p.*, COALESCE(AVG(r.rating),0) AS avg_rating, COUNT(r.id) AS review_count FROM products p LEFT JOIN reviews r ON r.product_id=p.id WHERE p.active=1 GROUP BY p.id ORDER BY p.badge='BÁN CHẠY' DESC, p.id ASC LIMIT 8").fetchall()
    category_counts = {r["category"]: r["n"] for r in db.execute("SELECT category,COUNT(*) AS n FROM products WHERE active=1 GROUP BY category").fetchall()}
    return render_template("index.html", featured=featured, popular=popular, category_counts=category_counts)


@app.route("/san-pham")
def catalog():
    db = get_db()
    q = request.args.get("q", "").strip()[:100]
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "popular")
    where = ["p.active=1"]
    params = []
    if q:
        where.append("(p.name LIKE ? OR p.description LIKE ? OR p.category LIKE ?)")
        params.extend([f"%{q}%"] * 3)
    if category in CATEGORIES:
        where.append("p.category=?")
        params.append(category)
    order_by = {
        "price_asc": "p.price ASC", "price_desc": "p.price DESC", "newest": "p.id DESC",
        "name": "p.name COLLATE NOCASE ASC", "popular": "p.badge='BÁN CHẠY' DESC, p.id DESC"
    }.get(sort, "p.badge='BÁN CHẠY' DESC, p.id DESC")
    rows = db.execute(f"SELECT p.*, COALESCE(AVG(r.rating),0) AS avg_rating, COUNT(r.id) AS review_count FROM products p LEFT JOIN reviews r ON r.product_id=p.id WHERE {' AND '.join(where)} GROUP BY p.id ORDER BY {order_by}", params).fetchall()
    return render_template("catalog.html", products=rows, q=q, selected_category=category, sort=sort)


@app.route("/san-pham/<slug>")
def product_detail(slug):
    db = get_db()
    product = db.execute("SELECT p.*, COALESCE(AVG(r.rating),0) AS avg_rating, COUNT(r.id) AS review_count FROM products p LEFT JOIN reviews r ON r.product_id=p.id WHERE p.slug=? AND p.active=1 GROUP BY p.id", (slug,)).fetchone()
    if not product:
        abort(404)
    reviews = db.execute("SELECT r.*, u.name AS user_name FROM reviews r JOIN users u ON u.id=r.user_id WHERE r.product_id=? ORDER BY r.created_at DESC", (product["id"],)).fetchall()
    favorite = False
    user = get_current_user()
    if user:
        favorite = bool(db.execute("SELECT 1 FROM wishlists WHERE user_id=? AND product_id=?", (user["id"], product["id"])).fetchone())
    related = db.execute("SELECT * FROM products WHERE active=1 AND category=? AND id<>? ORDER BY id DESC LIMIT 4", (product["category"], product["id"])).fetchall()
    can_review = False
    if user:
        can_review = bool(db.execute("SELECT 1 FROM order_items oi JOIN orders o ON o.id=oi.order_id WHERE o.user_id=? AND oi.product_id=? AND o.status IN ('Đã giao hàng','Hoàn thành') LIMIT 1", (user["id"], product["id"])).fetchone())
    return render_template("product_detail.html", product=product, reviews=reviews, favorite=favorite, related=related, can_review=can_review)


@app.post("/gio-hang/them/<int:product_id>")
def add_to_cart(product_id):
    product = get_db().execute("SELECT id,name,stock FROM products WHERE id=? AND active=1", (product_id,)).fetchone()
    if not product:
        flash("Sản phẩm không tồn tại hoặc đã ngừng bán.", "error")
        return redirect(url_for("catalog"))
    if product["stock"] <= 0:
        flash("Sản phẩm hiện đã hết hàng.", "error")
        return redirect(request.referrer or url_for("catalog"))
    try:
        qty = max(1, min(99, int(request.form.get("quantity", 1))))
    except ValueError:
        qty = 1
    cart = session.get("cart", {})
    new_qty = min(product["stock"], int(cart.get(str(product_id), 0)) + qty)
    cart[str(product_id)] = new_qty
    session["cart"] = cart
    session.modified = True
    flash(f"Đã thêm {product['name']} vào giỏ hàng.", "success")
    next_url = request.form.get("redirect_to", "")
    if next_url.startswith("/") and not next_url.startswith("//"):
        return redirect(next_url)
    return redirect(request.referrer or url_for("cart"))


@app.route("/gio-hang")
def cart():
    rows, subtotal = cart_rows()
    shipping, discount, total, coupon = checkout_math(subtotal, session.get("coupon", ""))
    return render_template("cart.html", rows=rows, subtotal=subtotal, shipping=shipping, discount=discount, total=total, coupon=coupon, coupon_code=session.get("coupon", ""))


@app.post("/gio-hang/cap-nhat")
def update_cart():
    cart_data = session.get("cart", {})
    db = get_db()
    for key in list(cart_data.keys()):
        try:
            product_id = int(key)
            qty = int(request.form.get(f"qty_{key}", cart_data[key]))
        except (TypeError, ValueError):
            continue
        product = db.execute("SELECT stock FROM products WHERE id=? AND active=1", (product_id,)).fetchone()
        if not product or qty <= 0 or product["stock"] <= 0:
            cart_data.pop(key, None)
        else:
            cart_data[key] = min(99, product["stock"], max(1, qty))
    session["cart"] = cart_data
    session.modified = True
    flash("Giỏ hàng đã được cập nhật.", "success")
    return redirect(url_for("cart"))


@app.post("/gio-hang/xoa/<int:product_id>")
def remove_from_cart(product_id):
    cart_data = session.get("cart", {})
    cart_data.pop(str(product_id), None)
    session["cart"] = cart_data
    session.modified = True
    flash("Đã xóa sản phẩm khỏi giỏ hàng.", "info")
    return redirect(url_for("cart"))


@app.post("/ma-giam-gia")
def apply_coupon():
    rows, subtotal = cart_rows()
    code = request.form.get("coupon_code", "").strip().upper()
    _, _, _, coupon = checkout_math(subtotal, code)
    if coupon:
        session["coupon"] = code
        flash(f"Áp dụng mã {code} thành công: {coupon['label']}.", "success")
    else:
        session.pop("coupon", None)
        flash("Mã giảm giá không hợp lệ hoặc đơn hàng chưa đạt giá trị tối thiểu.", "error")
    return redirect(url_for("cart"))


@app.route("/thanh-toan", methods=["GET", "POST"])
@login_required
def checkout():
    user = get_current_user()
    rows, subtotal = cart_rows()
    if not rows:
        flash("Giỏ hàng đang trống. Hãy chọn sản phẩm trước nhé.", "info")
        return redirect(url_for("catalog"))
    shipping, discount, total, coupon = checkout_math(subtotal, session.get("coupon", ""))
    if request.method == "POST":
        receiver = request.form.get("receiver_name", "").strip()[:100]
        phone = request.form.get("phone", "").strip()[:25]
        address = request.form.get("address", "").strip()[:500]
        payment = request.form.get("payment_method", "cod")
        note = request.form.get("note", "").strip()[:500]
        if not receiver or not phone or not address:
            flash("Vui lòng nhập đầy đủ tên người nhận, số điện thoại và địa chỉ.", "error")
            return render_template("checkout.html", rows=rows, subtotal=subtotal, shipping=shipping, discount=discount, total=total, coupon=coupon, user=user)
        if not re.fullmatch(r"[0-9+() .-]{8,25}", phone):
            flash("Số điện thoại chưa đúng định dạng.", "error")
            return render_template("checkout.html", rows=rows, subtotal=subtotal, shipping=shipping, discount=discount, total=total, coupon=coupon, user=user)
        if payment not in ("cod", "bank"):
            payment = "cod"
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            # Re-check stock inside the transaction to avoid ordering more than available.
            fresh_rows = []
            for row in rows:
                product = db.execute("SELECT * FROM products WHERE id=? AND active=1", (row["product"]["id"],)).fetchone()
                if not product or product["stock"] < row["quantity"]:
                    raise ValueError(f"Sản phẩm {row['product']['name']} không đủ tồn kho. Vui lòng cập nhật giỏ hàng.")
                fresh_rows.append((product, row["quantity"]))
            # Recalculate from the current database prices while stock is locked.
            actual_subtotal = sum(product["price"] * qty for product, qty in fresh_rows)
            actual_shipping, actual_discount, actual_total, actual_coupon = checkout_math(actual_subtotal, session.get("coupon", ""))
            code = "DH" + datetime.now().strftime("%y%m%d%H%M%S") + secrets.token_hex(2).upper()
            db.execute("INSERT INTO orders(order_code,user_id,receiver_name,phone,address,payment_method,subtotal,shipping_fee,discount,total,coupon_code,status,note,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (code, user["id"], receiver, phone, address, payment, actual_subtotal, actual_shipping, actual_discount, actual_total, (session.get("coupon", "") if actual_coupon else ""), "Chờ xác nhận", note, now_text()))
            order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            for product, qty in fresh_rows:
                db.execute("INSERT INTO order_items(order_id,product_id,product_name,product_image,price,quantity) VALUES(?,?,?,?,?,?)",
                           (order_id, product["id"], product["name"], product["image"], product["price"], qty))
                db.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, product["id"]))
            db.commit()
        except ValueError as exc:
            db.rollback()
            flash(str(exc), "error")
            return redirect(url_for("cart"))
        except sqlite3.Error:
            db.rollback()
            app.logger.exception("Checkout failed")
            flash("Chưa thể tạo đơn hàng do lỗi hệ thống. Vui lòng thử lại.", "error")
            return redirect(url_for("checkout"))
        session["cart"] = {}
        session.pop("coupon", None)
        flash("Đặt hàng thành công! Bạn có thể theo dõi trạng thái trong mục Đơn hàng của tôi.", "success")
        return redirect(url_for("order_detail", order_id=order_id))
    return render_template("checkout.html", rows=rows, subtotal=subtotal, shipping=shipping, discount=discount, total=total, coupon=coupon, user=user)


@app.route("/dang-ky", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:100]
        email = request.form.get("email", "").strip().lower()[:160]
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(name) < 2 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Vui lòng nhập họ tên và email hợp lệ.", "error")
        elif len(password) < 8:
            flash("Mật khẩu cần có ít nhất 8 ký tự.", "error")
        elif password != confirm:
            flash("Mật khẩu xác nhận không khớp.", "error")
        else:
            db = get_db()
            try:
                cursor = db.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)", (name, email, generate_password_hash(password), now_text()))
                db.commit()
                cart_before_login = session.get("cart", {})
                coupon_before_login = session.get("coupon", "")
                session.clear()
                session["user_id"] = cursor.lastrowid
                if cart_before_login:
                    session["cart"] = cart_before_login
                if coupon_before_login:
                    session["coupon"] = coupon_before_login
                session["csrf_token"] = secrets.token_urlsafe(24)
                flash("Tạo tài khoản thành công. Chào mừng bạn đến với Mây Mart!", "success")
                return redirect(url_for("index"))
            except sqlite3.IntegrityError:
                flash("Email này đã được sử dụng. Hãy đăng nhập hoặc dùng email khác.", "error")
    return render_template("auth.html", mode="register")


@app.route("/dang-nhap", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            cart_before_login = session.get("cart", {})
            coupon_before_login = session.get("coupon", "")
            session.clear()
            session["user_id"] = user["id"]
            if cart_before_login:
                session["cart"] = cart_before_login
            if coupon_before_login:
                session["coupon"] = coupon_before_login
            session["csrf_token"] = secrets.token_urlsafe(24)
            flash("Đăng nhập thành công.", "success")
            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect(url_for("admin_dashboard") if user["role"] == "admin" else url_for("index"))
        flash("Email hoặc mật khẩu chưa chính xác.", "error")
    return render_template("auth.html", mode="login")


@app.post("/dang-xuat")
def logout():
    cart_before_logout = session.get("cart", {})
    coupon_before_logout = session.get("coupon", "")
    session.clear()
    if cart_before_logout:
        session["cart"] = cart_before_logout
    if coupon_before_logout:
        session["coupon"] = coupon_before_logout
    session["csrf_token"] = secrets.token_urlsafe(24)
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("index"))


@app.route("/tai-khoan", methods=["GET", "POST"])
@login_required
def account():
    db = get_db()
    user = get_current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()[:100]
        phone = request.form.get("phone", "").strip()[:25]
        address = request.form.get("address", "").strip()[:500]
        if len(name) < 2:
            flash("Họ tên cần có ít nhất 2 ký tự.", "error")
        else:
            db.execute("UPDATE users SET name=?,phone=?,address=? WHERE id=?", (name, phone, address, user["id"]))
            db.commit()
            flash("Thông tin tài khoản đã được cập nhật.", "success")
            return redirect(url_for("account"))
    user = get_current_user()
    orders_count = db.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (user["id"],)).fetchone()[0]
    wishlist_count = db.execute("SELECT COUNT(*) FROM wishlists WHERE user_id=?", (user["id"],)).fetchone()[0]
    return render_template("account.html", user=user, orders_count=orders_count, wishlist_count=wishlist_count)


@app.route("/yeu-thich")
@login_required
def wishlist():
    user = get_current_user()
    products = get_db().execute("SELECT p.* FROM wishlists w JOIN products p ON p.id=w.product_id WHERE w.user_id=? AND p.active=1 ORDER BY w.created_at DESC", (user["id"],)).fetchall()
    return render_template("wishlist.html", products=products)


@app.post("/yeu-thich/<int:product_id>")
@login_required
def toggle_wishlist(product_id):
    user = get_current_user()
    db = get_db()
    product = db.execute("SELECT id,slug FROM products WHERE id=? AND active=1", (product_id,)).fetchone()
    if not product:
        abort(404)
    existing = db.execute("SELECT 1 FROM wishlists WHERE user_id=? AND product_id=?", (user["id"], product_id)).fetchone()
    if existing:
        db.execute("DELETE FROM wishlists WHERE user_id=? AND product_id=?", (user["id"], product_id))
        flash("Đã xóa khỏi danh sách yêu thích.", "info")
    else:
        db.execute("INSERT OR IGNORE INTO wishlists(user_id,product_id,created_at) VALUES(?,?,?)", (user["id"], product_id, now_text()))
        flash("Đã thêm vào danh sách yêu thích.", "success")
    db.commit()
    return redirect(request.referrer or url_for("wishlist"))


@app.post("/san-pham/<int:product_id>/danh-gia")
@login_required
def add_review(product_id):
    user = get_current_user()
    db = get_db()
    eligible = db.execute("SELECT 1 FROM order_items oi JOIN orders o ON o.id=oi.order_id WHERE o.user_id=? AND oi.product_id=? AND o.status IN ('Đã giao hàng','Hoàn thành') LIMIT 1", (user["id"], product_id)).fetchone()
    if not eligible:
        flash("Bạn cần mua và nhận sản phẩm trước khi đánh giá.", "error")
        return redirect(request.referrer or url_for("catalog"))
    try:
        rating = int(request.form.get("rating", 5))
    except ValueError:
        rating = 5
    rating = min(5, max(1, rating))
    comment = request.form.get("comment", "").strip()[:1000]
    db.execute("INSERT INTO reviews(user_id,product_id,rating,comment,created_at) VALUES(?,?,?,?,?) ON CONFLICT(user_id,product_id) DO UPDATE SET rating=excluded.rating, comment=excluded.comment, created_at=excluded.created_at", (user["id"], product_id, rating, comment, now_text()))
    db.commit()
    flash("Cảm ơn bạn đã chia sẻ đánh giá!", "success")
    product = db.execute("SELECT slug FROM products WHERE id=?", (product_id,)).fetchone()
    return redirect(url_for("product_detail", slug=product["slug"]))


@app.route("/don-hang")
@login_required
def orders():
    user = get_current_user()
    rows = get_db().execute("SELECT o.*, (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id=o.id) AS items_count FROM orders o WHERE o.user_id=? ORDER BY o.id DESC", (user["id"],)).fetchall()
    return render_template("orders.html", orders=rows)


@app.route("/don-hang/<int:order_id>")
@login_required
def order_detail(order_id):
    user = get_current_user()
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, user["id"])).fetchone()
    if not order:
        abort(404)
    items = db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    return render_template("order_detail.html", order=order, items=items)


@app.post("/don-hang/<int:order_id>/huy")
@login_required
def cancel_order(order_id):
    user = get_current_user()
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, user["id"])).fetchone()
        if not order or order["status"] != "Chờ xác nhận":
            db.rollback()
            flash("Chỉ đơn hàng đang chờ xác nhận mới có thể hủy.", "error")
            return redirect(url_for("order_detail", order_id=order_id))
        items = db.execute("SELECT product_id,quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall()
        for item in items:
            if item["product_id"]:
                db.execute("UPDATE products SET stock=stock+? WHERE id=?", (item["quantity"], item["product_id"]))
        db.execute("UPDATE orders SET status='Đã hủy' WHERE id=?", (order_id,))
        db.commit()
        flash("Đơn hàng đã được hủy.", "success")
    except sqlite3.Error:
        db.rollback()
        flash("Không thể hủy đơn hàng lúc này.", "error")
    return redirect(url_for("order_detail", order_id=order_id))


# ---------------- Admin ----------------
@app.route("/quan-tri")
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        "products": db.execute("SELECT COUNT(*) FROM products WHERE active=1").fetchone()[0],
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "customers": db.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0],
        "revenue": db.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE status IN ('Đã giao hàng','Hoàn thành')").fetchone()[0],
        "pending": db.execute("SELECT COUNT(*) FROM orders WHERE status='Chờ xác nhận'").fetchone()[0],
        "low_stock": db.execute("SELECT COUNT(*) FROM products WHERE active=1 AND stock<=5").fetchone()[0],
    }
    recent_orders = db.execute("SELECT o.*,u.name AS customer_name FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC LIMIT 8").fetchall()
    low_stock = db.execute("SELECT * FROM products WHERE active=1 AND stock<=5 ORDER BY stock ASC LIMIT 6").fetchall()
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders, low_stock=low_stock)


def product_form_values(form):
    name = form.get("name", "").strip()[:160]
    category = form.get("category", "").strip()
    description = form.get("description", "").strip()[:5000]
    image = form.get("image", "").strip()[:1000]
    badge = form.get("badge", "").strip()[:30]
    try:
        price = int(form.get("price", 0))
        original_price = int(form.get("original_price", 0) or 0)
        stock = int(form.get("stock", 0))
    except ValueError:
        raise ValueError("Giá và tồn kho phải là số nguyên hợp lệ.")
    if len(name) < 2:
        raise ValueError("Tên sản phẩm cần có ít nhất 2 ký tự.")
    if category not in CATEGORIES:
        raise ValueError("Vui lòng chọn danh mục hợp lệ.")
    if price < 0 or original_price < 0 or stock < 0:
        raise ValueError("Giá và tồn kho không được âm.")
    if not safe_external_image(image):
        raise ValueError("Ảnh sản phẩm cần là đường dẫn HTTP hoặc HTTPS hợp lệ.")
    return name, category, description, price, max(price, original_price), stock, image, badge


@app.route("/quan-tri/san-pham")
@admin_required
def admin_products():
    products = get_db().execute("SELECT * FROM products ORDER BY active DESC, id DESC").fetchall()
    return render_template("admin/products.html", products=products)


@app.route("/quan-tri/san-pham/them", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    if request.method == "POST":
        try:
            values = product_form_values(request.form)
            db = get_db()
            db.execute("INSERT INTO products(name,slug,category,description,price,original_price,stock,image,badge,active,created_at) VALUES(?,?,?,?,?,?,?,?,?,1,?)", (values[0], make_slug(values[0]), *values[1:], now_text()))
            db.commit()
            flash("Đã thêm sản phẩm mới.", "success")
            return redirect(url_for("admin_products"))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("admin/product_form.html", product=None, page_title="Thêm sản phẩm")


@app.route("/quan-tri/san-pham/<int:product_id>/sua", methods=["GET", "POST"])
@admin_required
def admin_product_edit(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if not product:
        abort(404)
    if request.method == "POST":
        try:
            values = product_form_values(request.form)
            db.execute("UPDATE products SET name=?,category=?,description=?,price=?,original_price=?,stock=?,image=?,badge=? WHERE id=?", (*values, product_id))
            db.commit()
            flash("Đã cập nhật sản phẩm.", "success")
            return redirect(url_for("admin_products"))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("admin/product_form.html", product=product, page_title="Sửa sản phẩm")


@app.post("/quan-tri/san-pham/<int:product_id>/an")
@admin_required
def admin_product_toggle(product_id):
    db = get_db()
    db.execute("UPDATE products SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (product_id,))
    db.commit()
    flash("Đã cập nhật trạng thái hiển thị sản phẩm.", "success")
    return redirect(url_for("admin_products"))


@app.route("/quan-tri/don-hang")
@admin_required
def admin_orders():
    status = request.args.get("status", "").strip()
    statuses = ["Chờ xác nhận", "Đã xác nhận", "Đang giao hàng", "Đã giao hàng", "Hoàn thành", "Đã hủy"]
    db = get_db()
    if status in statuses:
        rows = db.execute("SELECT o.*,u.name AS customer_name,u.email FROM orders o JOIN users u ON u.id=o.user_id WHERE o.status=? ORDER BY o.id DESC", (status,)).fetchall()
    else:
        rows = db.execute("SELECT o.*,u.name AS customer_name,u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC").fetchall()
    return render_template("admin/orders.html", orders=rows, selected_status=status, statuses=statuses)


@app.route("/quan-tri/don-hang/<int:order_id>", methods=["GET", "POST"])
@admin_required
def admin_order_detail(order_id):
    db = get_db()
    order = db.execute("SELECT o.*,u.email AS customer_email FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=?", (order_id,)).fetchone()
    if not order:
        abort(404)
    if request.method == "POST":
        status = request.form.get("status", "")
        statuses = ["Chờ xác nhận", "Đã xác nhận", "Đang giao hàng", "Đã giao hàng", "Hoàn thành", "Đã hủy"]
        if status not in statuses:
            flash("Trạng thái đơn hàng không hợp lệ.", "error")
        elif order["status"] == "Đã hủy" and status != "Đã hủy":
            flash("Đơn đã hủy không thể khôi phục tự động. Hãy tạo đơn hàng mới.", "error")
        elif status == "Đã hủy" and order["status"] not in ("Chờ xác nhận", "Đã xác nhận"):
            flash("Chỉ có thể hủy đơn trước khi chuyển sang giao hàng.", "error")
        elif status == "Đã hủy" and order["status"] != "Đã hủy":
            try:
                db.execute("BEGIN IMMEDIATE")
                items = db.execute("SELECT product_id,quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall()
                for item in items:
                    if item["product_id"]:
                        db.execute("UPDATE products SET stock=stock+? WHERE id=?", (item["quantity"], item["product_id"]))
                db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
                db.commit()
                flash("Đã hủy đơn và hoàn tồn kho.", "success")
            except sqlite3.Error:
                db.rollback()
                flash("Không thể cập nhật đơn hàng.", "error")
        else:
            db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
            db.commit()
            flash("Đã cập nhật trạng thái đơn hàng.", "success")
        return redirect(url_for("admin_order_detail", order_id=order_id))
    items = db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    statuses = ["Chờ xác nhận", "Đã xác nhận", "Đang giao hàng", "Đã giao hàng", "Hoàn thành", "Đã hủy"]
    return render_template("admin/order_detail.html", order=order, items=items, statuses=statuses)


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, title="Yêu cầu chưa hợp lệ", message=getattr(error, "description", "Vui lòng thử lại.")), 400


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", code=403, title="Bạn chưa có quyền truy cập", message="Trang này chỉ dành cho tài khoản quản trị."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, title="Không tìm thấy trang", message="Trang bạn tìm không tồn tại hoặc sản phẩm đã ngừng bán."), 404


with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))

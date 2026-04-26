from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = 'super_secret_telor_key'

# MySQL Configuration
db_config = {
    'user': 'root',
    'password': 'Risha@123',
    'host': 'localhost',
    'database': 'telor_db'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None

def get_products_by_category(category):
    conn = get_db_connection()
    products = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE category = %s", (category,))
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    return products

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/men')
def men():
    products = get_products_by_category('men')
    return render_template('men.html', products=products)

@app.route('/women')
def women():
    products = get_products_by_category('women')
    return render_template('women.html', products=products)

@app.route('/access')
def access():
    products = get_products_by_category('access')
    return render_template('access.html', products=products)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total_price = sum(float(item['price']) for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    product_image = request.form.get('product_image')
    
    if 'cart' not in session:
        session['cart'] = []
        
    session['cart'].append({
        'id': product_id,
        'name': product_name,
        'price': product_price,
        'image_url': product_image
    })
    session.modified = True
    
    return jsonify({"status": "success", "message": f"{product_name} added to cart!"})

@app.route('/remove_from_cart/<int:index>')
def remove_from_cart(index):
    if 'cart' in session and 0 <= index < len(session['cart']):
        session['cart'].pop(index)
        session.modified = True
        flash('Item removed from cart.', 'success')
    return redirect(url_for('cart'))

@app.route('/buy', methods=['POST'])
def buy():
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        product_price = request.form.get('product_price', 0)
        customer_name = request.form.get('customer_name')
        customer_email = request.form.get('customer_email')
        customer_address = request.form.get('customer_address')
        
        # If checking out from cart, combine names and get total
        if product_name == 'Cart Checkout':
            cart_items = session.get('cart', [])
            product_name = ", ".join([item['name'] for item in cart_items])
            product_price = sum(float(item['price']) for item in cart_items)
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO orders (product_name, customer_name, customer_email, customer_address, price) VALUES (%s, %s, %s, %s, %s)",
                    (product_name, customer_name, customer_email, customer_address, product_price)
                )
                conn.commit()
                # Clear cart if it was a cart checkout
                if request.form.get('product_name') == 'Cart Checkout':
                    session.pop('cart', None)
                flash('Order placed successfully!', 'success')
            except mysql.connector.Error as err:
                print(f"Error: {err}")
                flash('An error occurred while placing your order.', 'danger')
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Database connection failed. Please try again later.', 'danger')
            
        return redirect(request.referrer or url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

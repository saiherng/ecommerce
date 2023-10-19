from flask import *
from flask_sqlalchemy import SQLAlchemy


from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import requests
from functools import wraps

# create the extension
db = SQLAlchemy()

# create the app
app = Flask(__name__)

#app.register_blueprint(swaggerui_blueprint)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///saiherng.db"
app.config["SECRET_KEY"] = "secret_key"



jwt = JWTManager(app)
db.init_app(app)


#SCHEMA -----------------------------------------------------------------------
class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    img_url = db.Column(db.String(200))
    price = db.Column(db.Float)
    description = db.Column(db.String(200))
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))

    order_item = db.relationship('OrderItem', back_populates='product')
    vendor = db.relationship('Vendor', back_populates='product')

    def __repr__(self):
        return f'<Product: {self.name}, {self.price}, {self.description}>'


class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    total_price = db.Column(db.Float)
    
    customer = db.relationship('Customer', back_populates='order')
    order_item = db.relationship('OrderItem', back_populates='order')
    vendor = db.relationship('Vendor', back_populates='order')
    

class OrderItem(db.Model):

    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)
    
    order = db.relationship('Order', back_populates='order_item')
    product = db.relationship('Product', back_populates='order_item')


class Customer(db.Model):
    __tablename__ = 'customer'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    phone = db.Column(db.String)
    address = db.Column(db.String)

    order = db.relationship('Order', back_populates='customer')

    def __repr__(self):
        return f'<Customer: {self.name}>'
    
class Vendor(db.Model):
    __tablename__ = 'vendor'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String)
    password = db.Column(db.String)
    phone = db.Column(db.String)
    address = db.Column(db.String)

    product = db.relationship('Product', back_populates='vendor')
    order = db.relationship('Order', back_populates='vendor')

    def __repr__(self):
        return f'<Vendor: {self.name}>'


with app.app_context():     
   db.create_all()


#login--------------------------------------------------
@app.route('/login', methods=['GET','POST'])
def login():

    username = 'testuser'
    password = 'test123'

    access_token = create_access_token(identity=username)

    # Store the authentication status in the session
    session['authenticated'] = True

    # Return the access token to the client
    return jsonify(access_token=access_token), 200


@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # Check if the user is authenticated
    authenticated = session.get('authenticated', False)

    if authenticated:
        # Access the current user's identity
        current_user = get_jwt_identity()

        # Return a response for the authenticated user
        return jsonify(message=f'Protected endpoint accessed by {current_user}.'), 200
    else:
        return jsonify(message='Not authenticated.'), 401

#Index -------------------------------------------------------------
@app.route("/")
def index(methods=['GET']):

    vendors = Vendor.query.all()
    products = Product.query.all()
    result = []

    for vendor in vendors:
        vendor_products = db.session.query(Product).filter_by(vendor_id = vendor.id).all()

        vendor = { 'id' : vendor.id,
                   'name' : vendor.name,
                   'products' : [{'id': product.id,
                                'name' :product.name,
                                'img_url' :product.img_url,
                                'description' :product.description,
                                'price': product.price } for product in vendor_products]
        }
    
        result.append(vendor)


    return render_template("index.html", result= result )



#Product ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#SELECT ALL PRODUCTS
@app.route("/product")
def list_products(methods=['GET']):

    products = Product.query.all()
    vendors = Vendor.query.all()

    return render_template("product.html", result = {'products': products,
                                                     'vendors' : vendors} )
    
#SELECT PRODUCT BY ID 
#---------------------------------------------------
@app.route("/product/<int:productID>")
def get_product(productID, methods=['GET']):

    product = Product.query.get(productID)

    if product:
        return jsonify({'id': product.id, 'name': product.name, 'vendor': product.vendor.name,'price': product.price, 'description': product.description})
    else:
        return jsonify({'error': 'Product not found.'}), 404


#CREATE NEW PRODUCT - Input using html form
#---------------------------------------------------
@app.route('/product/new', methods=['GET','POST'])
def create_product():
   
    name = request.form['name']
    price = request.form['price']
    img_url = request.form['img_url']
    description = request.form['description']
    vendor_id = request.form['vendor_id']

    vendor = Vendor.query.get(vendor_id)
    product = Product(name=name, img_url=img_url, price=price, vendor_id=vendor_id, vendor=vendor, description=description)
    product.vendor = vendor

    db.session.add(product)
    db.session.commit()
    message = "New Product Created"

    #return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description})
    return redirect(url_for('list_products'))

#EDIT PRODUCT BY ID THROUGH WEB PAGE
#---------------------------------------------------
@app.route('/product/<int:productID>/edit', methods=['GET','POST'])
def edit_product(productID):
    product = Product.query.get(productID)

    if product:
        return render_template('edit_product.html', product=product)
    else:
        return jsonify({'error': 'Product not found.'}), 404



#UPDATE PRODUCT BY ID THROUGH HTML FORM
#---------------------------------------------------
@app.route('/product/<int:productID>/update', methods=['GET','POST'])
def update_product(productID):

    product = Product.query.get(productID)
    product.name = request.form['name']
    product.img_url = request.form['img_url']
    product.price = float(request.form['price'])
    product.description = request.form['description']

    db.session.commit()
    message = "Edited Product"

    #return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description})
    return redirect(url_for('list_products'))

#DELETE PRODUCT BY ID 
#---------------------------------------------------
@app.route('/product/<int:productID>/delete', methods=['GET','DELETE'])
def delete_product(productID):

    product = Product.query.get(productID)
    
    if product:
        db.session.delete(product)
        db.session.commit()

        message = f"Product: {product} was deleted"

        return redirect(url_for('list_products'))
    else:
        return jsonify({'error': 'Product not found.'}), 404


#Customer ------------------------------------------------------------
#SELECT ALL CUSTOMERS  
#---------------------------------------------------
@app.route("/customer")
def list_customers():
    customers = Customer.query.all()
    return render_template("customer.html", customers=customers)


#CREATE NEW CUSTOMER
#---------------------------------------------------
@app.route('/customer/new', methods=['GET','POST'])
def create_customer():
   
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    customer = Customer(name=name,email=email,phone=phone,address=address)
    
    db.session.add(customer)
    db.session.commit()
    message = "New Customer Created"
    
    return redirect(url_for('list_customers'))


#Vendor--------------------------------------------------------------------

#SELECT ALL VENDORS
#---------------------------------------------------
@app.route("/vendor")
def list_vendors():
    vendors = Vendor.query.all()
    return render_template("vendor.html", vendors=vendors)


#SELECT VENDOR ORDERS BY VENDOR ID 
#---------------------------------------------------
@app.route("/vendor/<int:vendorID>/orders")
def list_vendor_orders(vendorID):

    vendor = Vendor.query.get(vendorID)
    orders = db.session.query(Order).filter_by(vendor_id = vendorID).all()
    customers = Customer.query.all()
    
    return render_template("vendor_orders.html", orders = {'vendor': vendor,
                                                           'orders': orders,
                                                           'customers': customers} )

#SELECT PRODUCTS SOLD BY VENDORS USING VENDOR ID 
#---------------------------------------------------
@app.route("/vendor/<int:vendorID>/products")
def list_vendor_products(vendorID, methods=['GET']):

    vendor = Vendor.query.get(vendorID)
    products = db.session.query(Product).filter_by(vendor_id = vendorID).all()

    if vendor and products:
        product_list = []
        for product in products:
            product_data = {
                    'id' : product.id,
                    'price' : product.price,
                    'vendor' : product.vendor.name,
                    'description' : product.description
            }
            product_list.append(product_data)

        return jsonify({'products':product_list})
        
    else:
        return jsonify({'error': 'Vendor/Product does not exist'}), 404


#CREATE NEW VENDOR 
#---------------------------------------------------
@app.route("/vendor/new" , methods=['GET','POST'])
def create_vendor():

    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    
    vendor = Vendor(name=name, email=email,phone=phone, address=address )

    db.session.add(vendor)
    db.session.commit()
    message = "New Vendor Created"

    #return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description})
    return redirect(url_for('list_vendors'))

    
#Order ---------------------------------------------------------------

#SELECT ALL ORDERS - CATEGORIZED BY VENDOR 
#---------------------------------------------------
@app.route("/orders")
def list_orders():

    vendors = Vendor.query.all()
    customers = Customer.query.all()

    orders = []
    
    for vendor in vendors:

        vendor_orders = db.session.query(Order).filter_by(vendor_id = vendor.id).all()

        vendor = { 'id' : vendor.id,
                   'name' : vendor.name,
                   'orders' : [{'id': order.id,
                                'customer' :order.customer.name,
                                'total_price': order.total_price } for order in vendor_orders]
        }
    
        orders.append(vendor)


    return render_template("order.html", orders= {'orders': orders,'customers': customers} )
    
#SELECT ORDER BY ORDER ID 
#---------------------------------------------------
@app.route("/order/<int:orderID>")
def get_order(orderID):
    order = Order.query.get(orderID)

    if order:
        return jsonify({'id': order.id, 'customerID': order.customer_id,'name': order.customer.name, 'price': order.total_price})
    else:
        return jsonify({'error': 'Order not found.'}), 404
    

#CREATE NEW ORDER USING HTML FORM
#---------------------------------------------------
@app.route('/order/new', methods=['GET','POST'])
def create_order():
   
    customerID = request.form['customer_id']
    vendorID = request.form['vendor_id']

    customer = Customer.query.get(customerID)
    vendor = Vendor.query.get(vendorID)
    total_price = 0

    order = Order(customer_id=customerID, vendor_id = vendorID, vendor=vendor,customer=customer, total_price=total_price)
 
    db.session.add(order)
    db.session.commit()
    message = "New Order Created"
    
    return redirect(url_for('list_orders'))

#DELETE ORDER BY ORDER ID 
#---------------------------------------------------
@app.route('/order/<int:orderID>/delete', methods=['GET','DELETE'])
def delete_order(orderID):

    order = Order.query.get(orderID)
    if order:
        db.session.delete(order)
        db.session.commit()

        message = f"Product: {order} was deleted"

        return redirect(url_for('list_orders'))
    else:
        return jsonify({'error': 'Order not found.'}), 404


#Order Items ----------------------------------------------------------------

#SELECT ORDER ITEM  BY ORDER ID AND ORDERITEM ID 
#---------------------------------------------------
@app.route("/order/<int:orderID>/orderitem/<int:orderitemID>")
def get_orderitem(orderID,orderitemID):
    
    orderitem = OrderItem.query.get(orderitemID)

    if orderitem:
        return jsonify({'id': orderID, 'orderID': orderitem.order_id,'productID': orderitem.product_id, 'quantity': orderitem.quantity})
    else:
        return jsonify({'error': 'Order Item not found.'}), 404


#SELECT ALL ORDERITEMS IN AN ORDER BY ORDER ID 
#---------------------------------------------------
@app.route("/order/<int:orderID>/orderitems")
def get_orderitems(orderID):

    orderItems = db.session.query(OrderItem).filter(OrderItem.order_id==orderID).all()
    order = Order.query.get(orderID)
    
    products = db.session.query(Product).filter_by(vendor_id = order.vendor.id).all()
    return render_template('orderitems.html', orders = {'order' : order,
                                                        'orderItems': orderItems,
                                                        'products': products})
    

#CREATE NEW ORDERITEM BY ORDER ID 
#---------------------------------------------------
@app.route('/order/<int:orderID>/orderitem/new', methods=['GET','POST'])
def create_orderitem(orderID):
   

    order = Order.query.get(orderID)

    productID = request.form['product_id']
    quantity = request.form['quantity']

    
    product = Product.query.get(productID)

    if not product:
        return jsonify({'error': 'Product does not exist.'}), 404

    orderItem = OrderItem(order_id = orderID, order=order, product=product, product_id=productID, quantity=quantity)
    order.total_price += float(quantity) * product.price

    db.session.add(orderItem)
    db.session.commit()
    message = "New Order Item Created"
    
    return redirect(url_for('get_orderitems', orderID = orderID))


#DELETE ORDERITEM BY ORDER ID AND ORDERITEM ID 
#---------------------------------------------------
@app.route('/order/<int:orderID>/orderitem/<int:orderitemID>/delete', methods=['GET','DELETE'])
def delete_orderitem(orderID, orderitemID):

    orderItem = OrderItem.query.get(orderitemID)
    
    if orderItem:
        order = Order.query.get(orderID)
        order.total_price -= float(orderItem.quantity) * orderItem.product.price 

        db.session.delete(orderItem)
        db.session.commit()

        message = f"Product: {orderItem} was deleted"

        return redirect(url_for('get_orderitems', orderID=orderID))
    else:
        return jsonify({'error': 'Product not found.'}), 404


#RUN APP
if __name__ == '__main__':
    app.run(debug=True)
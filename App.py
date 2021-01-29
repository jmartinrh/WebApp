from flask import (
    Flask, session, g, abort, render_template, 
    request, redirect, url_for, flash
    )
import mysql.connector
from passlib.hash import sha256_crypt

#Init
app = Flask(__name__)
#MYSQL Connection
def sql_connection():
    con = mysql.connector.connect(
        host="127.0.0.1", port=3306, user="root", 
        passwd="password", db="flaskcontacts")
    return con

#Settings
app.secret_key = 'veryverysecretsecret'

ACCESS = {'guest':0, 'user':1, 'admin':2}

class User:
    def __init__(self, id, name, email, user, password, access):
        self.id = id
        self.name = name
        self.email = email
        self.user = user
        self.password = password
        self.access = access
    def is_admin(self):
        if self.access == 'admin':
            return self.access == ACCESS['admin']
    def allowed (self, access_level):
        return self.access >= access_level
    def __repr__(self):
        return f'<User: {self.id}>'

def get_user_data():
    con = sql_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    userdata = [] 
    for x in data:
        userdata.append(User(id=x[0], name=x[1], email=x[2], user=x[3], password=x[4], access=x[5]))
    return userdata
############################################
#Log in
############################################

@app.before_request
def before_request():
    userdata = get_user_data()
    g.user = None   
    if 'user_id' in session:
        user = [x for x in userdata if x.id == session['user_id']][0]
        g.user = user

@app.route('/', methods=['GET', 'POST'])
def index():    
    
    userdata = get_user_data()
    if request.method == 'POST':
        session.pop('user_id', None)
        username = request.form['username']
        password = request.form['password']
        for x in userdata:
            if x.user == username:
                user = x
                if sha256_crypt.verify(password, user.password):
          
                    session['user_id'] = user.id                    
                    if user.access == 'admin':                        
                        return redirect(url_for('register_user'))
                    else:
                        return redirect(url_for('modify_quantity'))
                else:
                    flash('Contraseña incorrecta')
                    return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/sign_out')
def sign_out():
    session.pop('user_id')
    return redirect(url_for('index'))

############################################
#For ADMINs
############################################

@app.route('/user_registry') #Decorador
def register_user():
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()    
    return render_template('register-user.html', users = data)

@app.route('/add_usuario', methods=['POST'])
def add_contact():
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user = request.form['user']
        password = request.form['password']
        password = sha256_crypt.hash(password)
        access = request.form['access']

        con = sql_connection()
        cur = con.cursor()
        cur.execute('INSERT INTO users (name, email, user, password, access) VALUES (%s, %s, %s, %s, %s)', 
                    (name, email, user, password, access))
        con.commit()

        flash('Usuario agregado satisfactoriamente')

        return redirect(url_for('register_user')) #redireccionar a página principal

@app.route('/edit/<id>')
def get_usuario(id):
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor() 
    cur.execute('SELECT * FROM users WHERE id = %s', (id,)) 
    #coma después de ID para leer como tupla
    data = cur.fetchall()
    return render_template('edit-usuario.html', user = data[0])

@app.route('/update/<id>', methods = ['POST'])
def update_usuario(id):
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        user = request.form['user']
        password = request.form['password'] 
        password = sha256_crypt.hash(password)
        access = request.form['access']
        
        con = sql_connection()
        cur = con.cursor()
        cur.execute(""" 
            UPDATE users
            SET name = %s,
                email = %s,
                user = %s,
                password = %s,
                access = %s
            WHERE id = %s
        """, (name, email, user, password, access, id))
        con.commit()
        flash('Usuario actualizado satisfactoriamente')
        return redirect(url_for('register_user'))    

@app.route('/delete/<string:id>')
def delete_usuario(id):
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor()
    cur.execute('DELETE FROM users WHERE id = {0}'.format(id))
    con.commit()
    flash('Usuario eliminado satisfactoriamente')
    return redirect(url_for('register_user'))

############################################
#for VENDORs
############################################
@app.route('/modify_quantity')
def modify_quantity():
    if not g.user:
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM products')
    data = cur.fetchall()    
    return render_template('productos-vendor.html', products = data)

@app.route('/edit_quantity/<id>')
def get_quantity(id):
    if not g.user:
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor() 
    cur.execute('SELECT * FROM products WHERE id = %s', (id,)) 
    #coma después de ID para leer como tupla
    data = cur.fetchall()
    return render_template('edit-quantity.html', producto = data[0])

@app.route('/update_quantity/<id>', methods = ['POST'])
def update_quantity(id):
    if not g.user:
        return redirect(url_for('index'))
    if request.method == 'POST': 
        quantity = request.form['quantity']      
        con = sql_connection()
        cur = con.cursor()
        cur.execute(""" 
            UPDATE products
            SET quantity = %s                
            WHERE id = %s
        """, (quantity, id))
        con.commit()
        flash('Producto actualizado satisfactoriamente')
        return redirect(url_for('modify_quantity')) 
############################################
#For products
############################################

@app.route('/productos') 
def lista_productos():
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM products')
    data = cur.fetchall()    
    return render_template('productos.html', products = data)

@app.route('/add_producto', methods=['POST'])
def add_producto():
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        value = request.form['value']
        quantity = request.form['quantity']        

        con = sql_connection()
        cur = con.cursor()
        cur.execute('INSERT INTO products (name, value, quantity) VALUES (%s, %s, %s)', 
                    (name, value, quantity))
        con.commit()

        flash('Producto agregado satisfactoriamente')
        return redirect(url_for('lista_productos')) 

@app.route('/edit_producto/<id>')
def get_producto(id):
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor()
    cur.execute('SELECT * FROM products WHERE id = %s', (id,)) 
    #coma después de ID para leer como tupla
    data = cur.fetchall()
    return render_template('edit-producto.html', producto = data[0])

@app.route('/update_producto/<id>', methods = ['POST'])
def update_productoo(id):
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        value = request.form['value']
        quantity = request.form['quantity']      
        con = sql_connection()
        cur = con.cursor()
        cur.execute(""" 
            UPDATE products
            SET name = %s,
                value = %s,
                quantity = %s
            WHERE id = %s
        """, (name, value, quantity, id))
        con.commit()
        flash('Producto actualizado satisfactoriamente')
        return redirect(url_for('lista_productos')) 

@app.route('/delete_producto/<string:id>')
def delete_producto(id):
    if not g.user.access == 'admin':
        flash("Acceso denegado, ingresar con otras credenciales!")
        return redirect(url_for('index'))
    con = sql_connection()
    cur = con.cursor()
    cur.execute('DELETE FROM products WHERE id = {0}'.format(id))
    con.commit()
    flash('Producto eliminado satisfactoriamente')
    return redirect(url_for('lista_productos'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port= 5000, debug=True)




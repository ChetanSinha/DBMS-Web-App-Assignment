from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import yaml
from datetime import datetime
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Configure DataBase
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def get_date():
    date_time = datetime.now()
    lst = [date_time.strftime("%d"), date_time.strftime("%m"), date_time.strftime("%Y")]
    date = ('-').join(lst)
    return date

# root.
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

# property options for buyer
@app.route('/buyproperty', methods=['GET', 'POST'])
def property():
    select = request.form
    if request.method == 'POST':
        address = select['address']
        type_ = select['type']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM property WHERE address=%s AND type=%s",(address, type_))
        
        if result > 0:
            data = cur.fetchall()
            return render_template('propertylist.html', data=data)
        else:
            return 'No match found'
        
        cur.close()
        
    return render_template('propertylist.html', form=select)

# agent registration
@app.route('/agentregister', methods=['GET', 'POST'])
def register():
    form = request.form
    if request.method == 'POST':
        
        name = form['name']
        password = sha256_crypt.encrypt(str(form['password']))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO agent(name, password) VALUES(%s, %s)", (name, password))
        
        mysql.connection.commit()
        cur.close()
        return redirect('/')

    return render_template('register.html', form=form)

# agent's login
@app.route('/agentlogin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM agent WHERE name=%s", [name])

        if result > 0:
            # get the stored hash
            flag=False
            data = cur.fetchall()
            for row in data:
                password = row['password']
                Id = row['agent_id']
                if sha256_crypt.verify(password_candidate, password):
                    flag = True
                    break
            
            if flag:
                session['logged_in'] = True
                session['username'] = name
                session['Id'] = Id
                return redirect('/agentlogged')
            else:
                return 'Wrong Password'
        else:
            # error = "Invalid login"
            return render_template('login.html')
        
        cur.close()

    return render_template('login.html')


# agent's after login
@app.route('/agentlogged')
def dashboard():
    return render_template('agentdashboard.html')

# sell property or adding to the list of properties
@app.route('/sellProperty/<int:id>', methods=['GET', 'POST'])
def sellproperty(id):
    property_type = request.form
    if request.method == 'POST':
        add = property_type['address']
        type_ = property_type['type']
        sp = property_type['selling_price']
        rp = property_type['renting_price']
        avail = property_type['availability']
        dos = property_type['date_of_selling']
        agent_id = id

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO property(address, type, selling_price, rent_price, availability, date_of_selling, agent_id) VALUES(%s, %s, %s, %s, %s, %s, %s)",[add, type_, sp, rp, avail, dos, agent_id])
        mysql.connection.commit()
        cur.close()
        return redirect('/agentlogged')

    return render_template('addproperty.html', form=property_type)

# agent's notification(not implemented)
@app.route('/notification<int:id>')
def notification():
    pass
    # return render_template('')

# agent logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# contact option for buyer(not fully implemented)
@app.route('/contact/<string:address>')
def contact(address):
    cur = mysql.connection.cursor()
    id = cur.execute("SELECT id FROM property WHERE address=%s",[address])
    cur.close()
    return redirect('/notification/id')

# more information of the property(not implemented)
@app.route('/moreinfo<string:address>')
def moreinfo(address):
    pass

# @app.route('/delete/<string:address>')
# def delete(address):
#     # task_to_delete = Todo.query.get_or_404(id)
#     try:
#         cur = mysql.connection.cursor()
#         cur.execute("DELETE FROM property WHERE address=%s", [address])
#         mysql.connection.commit()
#         cur.close()
#         return redirect('/')
#     except:
#         return "Problem in deletion"


# @app.route('/update/<string:address>', methods=['GET', 'POST'])
# def update(address):
#     # task = Todo.query.get_or_404(id)
#     if request.method == 'POST':
#         task.content = request.form['content']

#         try:
#             db.session.commit()
#             return redirect('/')
#         except:
#             return 'update issue'
#     else:
#         return render_template('update.html', task=task)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
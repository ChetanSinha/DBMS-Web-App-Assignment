from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import yaml
from datetime import datetime
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Configure DataBase
db = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)

app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# get today's date
def get_date():
    date_time = datetime.now()
    lst = [date_time.strftime("%d"), date_time.strftime("%m"), date_time.strftime("%Y")]
    date = ('-').join(lst)
    return date

# root
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

# property options for buyer
@app.route('/buyproperty/<int:id>', methods=['GET', 'POST'])
def property(id):
    select = request.form
    if request.method == 'POST':
        address = select['location']
        # size = select['size']

        cur = mysql.connection.cursor()

        result = cur.execute('SELECT * FROM property WHERE location=%s',[address])
        
        if result > 0:
            data = cur.fetchall()
            return render_template('propertylist.html', data=data, id=id)
        else:
            return 'No match found'
        
        cur.close()
        
    return render_template('propertylist.html', form=select, id=id)

# agent registration
@app.route('/agentregister', methods=['GET', 'POST'])
def aregister():
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

# agent registration
@app.route('/buyerregister', methods=['GET', 'POST'])
def bregister():
    form = request.form
    if request.method == 'POST':
        
        name = form['name']
        password = sha256_crypt.encrypt(str(form['password']))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO buyer(name, password) VALUES(%s, %s)", (name, password))
        
        mysql.connection.commit()
        cur.close()
        return redirect('/')

    return render_template('register.html', form=form)


# agent's login
@app.route('/agentlogin', methods=['GET', 'POST'])
def alogin():
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
def adashboard():
    return render_template('agentdashboard.html')

# buyer login
@app.route('/buyerlogin', methods=['GET', 'POST'])
def blogin():
    if request.method == 'POST':
        name = request.form['name']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM buyer WHERE name=%s", [name])

        if result > 0:
            # get the stored hash
            flag=False
            data = cur.fetchall()
            for row in data:
                password = row['password']
                Id = row['buyer_id']
                if sha256_crypt.verify(password_candidate, password):
                    flag = True
                    break
            if flag:
                session['logged_in'] = True
                session['username'] = name
                session['Id'] = Id
                return redirect('/buyerlogged')
            else:
                return 'Wrong Password'
        else:
            # error = "Invalid login"
            return render_template('login.html')
        
        cur.close()

    return render_template('login.html')

# buyer dashboard
@app.route('/buyerlogged')
def bdashboard():
    return render_template('buyerdashboard.html')

# adding to the list of properties
@app.route('/sellProperty/<int:id>', methods=['GET', 'POST'])
def sellproperty(id):
    property_type = request.form
    if request.method == 'POST':
        add = property_type['address']
        type_ = property_type['type']
        sp = property_type['selling_price']
        rp = property_type['renting_price']
        avail = property_type['availablity']
        dos = property_type['date_of_selling']
        agent_id = id

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO property(address, type, selling_price, rent_price, availablity, date_of_selling, agent_id) VALUES(%s, %s, %s, %s, %s, %s, %s)",[add, type_, sp, rp, avail, dos, agent_id])
        mysql.connection.commit()
        cur.close()
        return redirect('/agentlogged')

    return render_template('addproperty.html', form=property_type)

# agent's notification(not implemented)
@app.route('/notification/<int:agentid>')
def agentnotification(agentid):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM property WHERE (availablity=%s OR availablity=%s) AND agent_id=%s AND date_of_selling = 'NA'",[-1, 1, agentid])
    if result > 0:
        data = cur.fetchall()
        return render_template('agentnotifylist.html', data=data)
    else:
        return 'No Notifications'
    return redirect('/agentlogged')
        

# agent logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# contact agent for buying
@app.route('/contact/<string:buytype>/<int:propid>/<int:buyid>')
def contact(buytype, propid, buyid):
    cur = mysql.connection.cursor()
    if buytype == 'rent':
        cur.execute("UPDATE property SET buyer_id = %s, availablity = %s WHERE property_id = %s", [ buyid, -1, propid])
        
    elif buytype == 'buy':
        cur.execute("UPDATE property SET buyer_id = %s, availablity = %s WHERE property_id = %s", [ buyid, 1, propid])

    mysql.connection.commit()
    cur.close()
    return redirect('/buyerlogged')

# list of properties of agent
@app.route('/agentproperty/<int:agentid>')
def agentproperty(agentid):
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM property WHERE agent_id=%s',[agentid])
    if result > 0:
        data = cur.fetchall()
        return render_template('agentproplist.html', data=data)
    else:
        return 'No Property'
    cur.close()
    return redirect('/agentlogged')

# confirm the request of the buyer.
@app.route('/confirm/<int:propId>')
def confirm(propId):
    cur = mysql.connection.cursor()
    cur.execute("SELECT availablity FROM property WHERE property_id = %s", [propId])
    available_flag = cur.fetchone()

    # SELL 
    if available_flag == 1:
        cur.execute("UPDATE property SET availablity = %s, date_of_selling = %s WHERE property_id = %s AND buyer_id <> -1", [1, get_date(), propId])

    # RENT
    elif available_flag == -1:
        cur.execute("UPDATE property SET availablity = %s, date_of_selling = %s WHERE property_id = %s AND buyer_id <> -1",[-1, get_date(), propId ])
    mysql.connection.commit()
    cur.close()
    return redirect('/agentlogged')


# more information of the property(not implemented)
@app.route('/moreinfo<string:address>')
def moreinfo(address):
    pass


# __________________________________________________________________________________________________________________________________
# REAL ESATATE AGENT OFFICE

# check the selling and renting of the agent 
@app.route('/reoffice')
def reoffice():
    cur = mysql.connection.cursor()
    sell_result = cur.execute("SELECT agent.agent_id, name, SUM(selling_price) as sum FROM agent, property WHERE availablity=1 AND agent.agent_id=property.agent_id AND buyer_id <> -1 GROUP BY property.agent_id")
    
    sell_data = cur.fetchall()
    rent_result = cur.execute("SELECT agent.agent_id, name, SUM(renting_price) as sum FROM agent, property WHERE availablity=-1 AND agent.agent_id=property.agent_id AND buyer_id <> -1 GROUP BY property.agent_id")
    
    rent_data = cur.fetchall()

    if sell_result + rent_result > 0:
        return render_template('agentreport.html', sell_data=sell_data, rent_data=rent_data)
    
    else:
        return 'No Selling'
    
    cur.close()
    return redirect('/')

# check the details of a particular agent
@app.route('/sellingdetails/<string:buytype>/<int:agentid>')
def sellingdetails(buytype, agentid):
    cur = mysql.connection.cursor()
    if buytype == 'rented':
        result = cur.execute("SELECT location, type, size, date_of_entry, date_of_selling, renting_price, buyer_id FROM property WHERE agent_id=%s AND availablity=-1", [agentid])
        if result > 0:
            data = cur.fetchall()
            return render_template('rentingreport.html', data=data)
    
    elif buytype == 'sold':
        result = cur.execute("SELECT location, type, size, date_of_entry, date_of_selling, selling_price, buyer_id FROM property WHERE agent_id=%s AND availablity=1", [agentid])
        if result > 0:
            data = cur.fetchall()
            return render_template('sellingreport.html', data=data)
    
    cur.close()
    return redirect('/')

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SelectField
from wtforms import IntegerField
from flask_pymongo import PyMongo
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired,Email,Regexp,Length
from datetime import date
from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm 
from wtforms_sqlalchemy.fields import QuerySelectField

from flask_mail import Mail,Message

app = Flask(__name__)


app.config.update(
  DEBUG=True,
  #EMAIL SETTINGS
  MAIL_SERVER='smtp.gmail.com',
  MAIL_PORT=465,
  MAIL_USE_SSL=True,
  MAIL_USERNAME = 'sinchanagaonkar99@gmail.com',
  MAIL_PASSWORD = 'EXooO123*'
  )
mail = Mail(app)

#config Mongodb
app.config["MONGO_URI"] = "mongodb://localhost:27017/myApp"
mongo = PyMongo(app)


# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Welcome123*'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)


# Index
@app.route('/')
def index():
    return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')
  
class RegistrationForm(Form):
    room_no = IntegerField('Room_number', [validators.Length(min=1, max=50)])
    block_no = IntegerField('Block_number', [validators.Length(min=4, max=25)])
    warden = SelectField('Preferred Warden',choices=[('Ram12','Ram Nayak'),('Shyam12','Shyam Shetty'),('Suma12','Suma Rai')])
    leave_date=DateField('Room Leaving Date', format='%Y-%m-%d')
  
@app.route('/register_room',methods=['GET','POST'])
def register_room():
    form = RegistrationForm(request.form) 
    cur = mysql.connection.cursor()

   
    result = cur.execute("SELECT room_no,block_no FROM rooms WHERE alloc_status='unallocated'")

    room = cur.fetchall()
    if request.method == 'POST':
      
        room_no=form.room_no.data
        block_no=form.block_no.data
        warden=form.warden.data
        leave_date = form.leave_date.data
        leave_date_str = leave_date.strftime('%y-%m-%d')
        cur = mysql.connection.cursor()
        result=cur.execute("SELECT * FROM room_alloc WHERE username=%s",[session['username']])
        cnt=cur.fetchone()
        res=cur.execute("SELECT room_no from rooms where username=%s",[session['username']])
        cur.close()
        if result>0 :
            msg='Room is already requested'
            return  render_template('dashboard.html', msg=msg)
        elif res>0:
            msg='Room is already allotted' 
            return  render_template('dashboard.html', msg=msg)  
         
        else:
         flag=False
         for r in room:
           if r['room_no']==room_no and r['block_no']==block_no:
               flag=True



        if flag==True:
           cur = mysql.connection.cursor()
           cur.execute("INSERT INTO room_alloc(username,room_no,block_no,stat,warden,last_date) VALUES(%s, %s, %s,'unallocated',%s,%s)", ([session['username']], room_no, block_no,warden,leave_date_str))
           mysql.connection.commit()
           cur.execute("UPDATE users set warden=%s where username=%s", (warden,[session['username']]))
           mysql.connection.commit()
           cur.close()
           return redirect(url_for('dashboard'))
        else:
            msg='Requested room is already allotted to some other student or the room does not exist'
            return  render_template('dashboard.html', msg=msg)
       
    
    else:
        if result > 0:
          return render_template('register_room.html', room=room,form=form)
        else:
          msg = 'No Room Is Empty'
          return render_template('register_room.html', msg=msg)
          # Close connection
          cur.close()
        

@app.route('/allot_room')
def allot_room():
    
    
       cur = mysql.connection.cursor()
       result = cur.execute("SELECT room_alloc.username,room_alloc.room_no,room_alloc.block_no,users.GPA,room_fee.amount FROM users,room_alloc,room_fee WHERE room_alloc.username =users.username and room_alloc.username=room_fee.username and room_alloc.warden=%s ORDER BY GPA DESC",[session['username']])
       students = cur.fetchall()
       if result > 0:
          return render_template('allot_room.html', students=students)
       else:
          msg = 'No request for rooms'
          return render_template('allot_room.html', msg=msg)
    # Close connection
       cur.close()
    
@app.route('/sample')
def sample():
   return {item:'abc99',code:'123'}


class RegisterForm(Form):
    first_name = StringField('First Name', validators=[InputRequired()])
    second_name = StringField('Second Name', [InputRequired()])
    last_name = StringField('Last Name', [InputRequired()])
    email = StringField('Email', [InputRequired(),Email()])
    parent_email = StringField('Parent Email', [InputRequired(),Email()])
    username=StringField('Username', [validators.Length(min=4, max=25)])
    gender=SelectField('Gender',choices=[('Male','Male'),('Female','Female')])
    GPA=IntegerField('GPA')
    contactno=StringField('Contact No.',[validators.Length(min=7, max=10)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password',)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        second_name = form.second_name.data
        last_name = form.last_name.data
        email = form.email.data
        parent_email = form.parent_email.data
        username = form.username.data
        gender = form.gender.data
        GPA=form.GPA.data
        contactno = form.contactno.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(first_name, second_name, last_name, email,parent_email,username,gender,GPA,contactno,password) VALUES(%s, %s, %s,%s, %s ,%s ,%s,%s,%s,%s)", (first_name, second_name, last_name, email,parent_email,username,gender,GPA,contactno,password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                 result=cur.execute("SELECT last_date from rooms where username=%s",[username])
                 if result==0:
                  session['logged_in'] = True
                  session['username'] = username
                  flash('You are now logged in', 'success')
                  return redirect(url_for('dashboard'))
                 else:
                  data1=cur.fetchone()
                  last_date=data1['last_date']
                  cur_date= date.today()
                  cur_date=cur_date.strftime('%y-%m-%d')
                  
                  if cur_date==last_date:
                   
                   
                   result=cur.execute("UPDATE rooms set last_date=NULL where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("UPDATE rooms set alloc_status='unallocated' where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("UPDATE rooms set username=NULL where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("DELETE from room_alloc where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("DELETE from mess_allot where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("DELETE from room_fee where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("DELETE from mess_fee where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("DELETE from feedback where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("DELETE from attendance where username=%s",[username])
                   mysql.connection.commit()
                   result=cur.execute("DELETE from users where username=%s",[username])
                   mysql.connection.commit()
                   flash('Period of stay is exceeded! Room has been unallocated')
                   return redirect(url_for('login'))
                  else:
                   session['logged_in'] = True
                   session['username'] = username 
                   flash('You are now logged in', 'success')
                   return redirect(url_for('dashboard'))  
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')



@app.route('/Warden_login', methods=['GET', 'POST'])
def warden_login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM warden WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if password_candidate==password:
                # Passed
                session['logged_in'] = True
                session['username'] = username
                


                flash('You are now logged in', 'success')
                return redirect(url_for('warden_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('Warden_login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('Warden_login.html', error=error)

    return render_template('Warden_login.html') 

@app.route('/allot/<string:id>', methods=['POST'])
def allot(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("UPDATE rooms SET alloc_status='allocated' WHERE room_no=%s",[id])
    cur.execute("UPDATE rooms SET alloc_status='allocated' WHERE room_no=%s",[id])
     
    cur.execute("UPDATE room_alloc set stat='allocated' where room_no=%s",[id])
    result=cur.execute("SELECT last_date from room_alloc where room_no=%s",[id])
    data=cur.fetchone()
    last=data['last_date']
    cur.execute("UPDATE rooms set last_date=%s where room_no=%s",(last,id))
    mysql.connection.commit()


    # Commit to DB

    cur.execute("UPDATE room_alloc set stat='allocated' where room_no=%s",[id])


    cur.execute("UPDATE rooms join room_alloc on rooms.room_no=room_alloc.room_no set rooms.username=room_alloc.username where room_alloc.stat='allocated'")   
    mysql.connection.commit()

    cur.execute("DELETE from room_alloc where room_no=%s",[id])
    mysql.connection.commit()
    
    #Close connection
    cur.close()

    flash('Room Alloted', 'success')

    return redirect(url_for('warden_dashboard'))




# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

   
    result = cur.execute("SELECT * FROM users WHERE username = %s", [session['username']])

    users = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', users=users)
    else:
        msg = 'No User Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()


@app.route('/warden_dashboard')
@is_logged_in
def warden_dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

     
    result = cur.execute("SELECT * FROM warden WHERE username = %s", [session['username']])

    wardens = cur.fetchall()

    result=cur.execute("SELECT * from users where warden=%s",[session['username']])
    cnt=cur.fetchall()

    if result > 0:
        return render_template('warden_dashboard.html', wardens=wardens,result=result)
    else:
        msg = 'No User Found'
        return render_template('warden_dashboard.html', msg=msg)
    # Close connection
    cur.close()    



@app.route('/room_info')
def room_info():
     
       cur=mysql.connection.cursor() 

       result=cur.execute("SELECT * from rooms where username=%s",[session['username']])

       if result > 0:
            # Get stored hash
            data = cur.fetchall()
            return render_template('room_info.html',data=data)
            
        
       else:
            error = 'Room has not been allocated yet'
            return render_template('room_info.html', error=error)

       cur.close()

  


class mess__form(Form):
   type1=SelectField('Type',choices=[('Veg','Veg'),('Non_Veg','Non_Veg')])

@app.route("/mess",methods=['GET','POST'])
def mess():
    form=mess__form(request.form)
    if request.method=='GET':
      vmenu = mongo.db.menu_veg.find({})
      nmenu = mongo.db.menu_nonveg.find({})
      return render_template("mess.html",form=form,vmenu=vmenu,nmenu=nmenu)
    else:
         t=form.type1.data
         
         cur = mysql.connection.cursor()
        
         cur.execute("INSERT INTO mess_allot(username,type) VALUES(%s, %s)", ([session['username']],t))
         mysql.connection.commit()
         
         #cur.execute("UPDATE users set mess_type=%s where username=%s",(type,[session['username']]))
         #mysql.connection.commit()
         cur.close()

         return redirect(url_for('dashboard'))



class attendanceform(Form):
   studname=StringField('Student Name', [validators.Length(min=2, max=50)])
   date=DateField('Attend Date', format='%Y-%m-%d')
   present=SelectField('Is Present',choices=[('present','Yes'),('absent','No')])
   remark=StringField('Remark', [validators.Length(min=0, max=50)])



@app.route("/attendance",methods=['GET','POST'])
def attendance():
    form=attendanceform(request.form)
    

    if request.method == 'POST' and form.validate():  
        

         
        studname = form.studname.data
        date = form.date.data
        present = form.present.data
        remark = form.remark.data
        start_date_str = date.strftime('%y-%m-%d')

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO attendance(username, _date, status,remark) VALUES(%s, %s, %s, %s )", (studname, start_date_str, present, remark))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        
        return redirect(url_for('warden_dashboard'))
   
    return render_template('attendance.html', form=form)
       

   



@app.route("/attendance_info")
def attendance_info():
   
      cur = mysql.connection.cursor()

   
      result = cur.execute("SELECT * FROM attendance where username=%s ",[session['username']])

      att_details = cur.fetchall()
      if result>0:  
        res=cur.execute("SELECT * from attendance where username=%s and status='present'",[session['username']])
        
        perc=(res/result)*100

        if(perc>85):
           msg1='Good attendance!'
        elif(perc>75):
           msg1='Satisfactory attendance'
        else:
           msg1='Attendance shortage! Please meet your warden'
           return render_template('attendance_info.html', details=att_details,perc=perc,msg1=msg1)
      else:
            msg = 'Attendance not marked yet'
            return render_template('attendance_info.html', msg=msg)
    # Close connection
      cur.close()

@app.route("/attend_date")
def attend_date():
   
        cur = mysql.connection.cursor()

   
        result = cur.execute("SELECT users.username,attendance._date,attendance.status,attendance.remark FROM attendance,users where users.username=attendance.username and users.warden=%s",[session['username']])

        att_details = cur.fetchall()

        
       
        return render_template('attend_date.html', details=att_details)
       
    # Close connection
        cur.close()



@app.route("/attendance_view")
def attendance_view():
   
        cur = mysql.connection.cursor()

   
        result = cur.execute("SELECT * FROM attendance")

        att_details = cur.fetchall()

        if result > 0:
            return render_template('attendance_view.html', details=att_details)
        else:
            msg = 'Attendance not marked yet'
            return render_template('attendance_view.html', msg=msg)
    # Close connection
        cur.close()   


class paymentform(Form):
   date=DateField('Payment Date',format='%Y-%m-%d')
   paid_by=SelectField('Paid By', choices=[('Bank','Bank'),('DBBL','DBBL'),('Bkash','Bkash')])
   mobile_no=StringField('Transaction no. or mobile no.',validators=[InputRequired(),Length(min=6, max=10)])
   mess=StringField('Veg/Non-Veg/None')
   amount=StringField('Amount')


@app.route("/payment_mess",methods=['GET','POST'])
def payment_mess():
    
    cur = mysql.connection.cursor()
    result=cur.execute("SELECT type from mess_allot where username=%s", [session['username']])
    data_mess = cur.fetchone()
    
    
    t='None'
    if result==0:
      amt='0000'
     
    else:
      t= data_mess['type']
      if t=='Veg'  :
        amt='25000'
      elif t=='Non_Veg':
       amt='50000'
      else:
       amt='00000'
    cur.close()
    
    form=paymentform(request.form)
    form.amount.data=amt
    form.mess.data=t
      
    if request.method=='POST' and form.validate():
         
        _date = form.date.data
        
       
        paid_by = form.paid_by.data
        mobile_no = form.mobile_no.data
        start_date_str = _date.strftime('%y-%m-%d')
        

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO mess_fee( _date,paid_by,transaction_no,amount,username) VALUES(%s, %s, %s, %s,%s)", (start_date_str, paid_by, mobile_no, amt,session['username']))

        # Commit to DB
        mysql.connection.commit()

       
        cur.execute("UPDATE users set mess_type=%s where username=%s",(t,[session['username']]))
        mysql.connection.commit()



        
        # Close connection
        cur.close()

        
        return redirect(url_for('dashboard'))
    return render_template('payment_mess.html', form=form)
           


class paymentformRoom(Form):
   date=DateField('Payment Date',format='%Y-%m-%d')
   paid_by=SelectField('Paid By', choices=[('Bank','Bank'),('DBBL','DBBL'),('Bkash','Bkash')])
   mobile_no=StringField('Transaction no. or mobile no.',validators=[InputRequired(),Length(min=6, max=10)])
   room=StringField('Requested/Not-requested')
   amount=StringField('Amount')        
             


@app.route("/payment_room",methods=['GET','POST'])
def payment_room():
    
    cur = mysql.connection.cursor()
    result=cur.execute("SELECT * FROM room_alloc WHERE username=%s",[session['username']])
    

    cnt=cur.fetchall()
    
    
    if result==0  :
       amt='00000'
       req='Not requested'
    else:
       amt='25000'
       req='Requested'
    cur.close()
    form=paymentformRoom(request.form)
    form.amount.data=amt
    form.room.data=req
                     

   
    if request.method=='POST' and form.validate():
      
        date = form.date.data
        paid_by = form.paid_by.data
        mobile_no = form.mobile_no.data
        start_date_str = date.strftime('%y-%m-%d')

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO room_fee( _date,paid_by,transaction_no,amount,username) VALUES(%s, %s, %s, %s,%s )", (start_date_str , paid_by, mobile_no, amt,[session['username']]))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()
  
        return redirect(url_for('dashboard'))  
     
    else:
       cur = mysql.connection.cursor()   
       res=cur.execute("SELECT * from room_fee where username=%s",[session['username']])
       cur.close()

       if res==0:
          return render_template('payment_room.html', form=form)
       else:
          msg='Payment done'
          return render_template('payment_room.html',form=form, msg=msg) 


@app.route('/mess_info')
def mess_info():
     
       cur=mysql.connection.cursor() 

       result=cur.execute("SELECT users.mess_type,mess.supervisor from mess,users where username=%s and users.mess_type=mess.mess_type",[session['username']])

       if result > 0:
            # Get stored hash
            data = cur.fetchall()

           

            return render_template('mess_info.html',data=data)
            
        
       else:
            error = 'Payment has not been done yet'
            return render_template('mess_info.html', error=error)

       cur.close()



@app.route('/payment_info')
def payment_info():
    
    
       cur = mysql.connection.cursor()
       result = cur.execute("SELECT room_fee.username,amount,transaction_no,_date,paid_by FROM room_fee,users WHERE room_fee.username=users.username and warden=%s",[session['username']] )
       students = cur.fetchall()
       if result > 0:
          return render_template('payment_info.html', students=students)
       else:
          msg = 'No payment has been done yet'
          return render_template('payment_info.html', msg=msg)
    # Close connection
       cur.close() 



@app.route('/ward_info')
def ward_info():
    
    
       cur = mysql.connection.cursor()
       result = cur.execute("SELECT first_name,last_name,email,parent_email,gender,GPA,contactno,mess_type FROM users WHERE  warden=%s",[session['username']] )
       students = cur.fetchall()
       if result > 0:
          return render_template('ward_info.html', students=students)
       else:
          msg = 'No ward has been allocated room yet'
          return render_template('ward_info', msg=msg)
    # Close connection
       cur.close()   



class create_roomForm(Form):
    room_no = SelectField('Room_number', choices=[(401,401),(402,402),(403,403),(404,404),(501,501),(502,502),(503,503)])
    block_no = SelectField('Block_number', choices=[(4,4),(5,5)])
    
  
@app.route('/create_room',methods=['GET','POST'])
def create_room():
    form = create_roomForm(request.form) 
    if request.method=='GET':
      
         return render_template('create_room.html',form=form)
      
    
    else:
        
         room_no=form.room_no.data
         block_no=form.block_no.data
         
         
         cur = mysql.connection.cursor()
         cur.execute("INSERT INTO rooms(room_no,block_no,alloc_status) VALUES(%s, %s,%s)", (room_no,block_no,'unallocated'))
         mysql.connection.commit()
         
         cur.close()
         return redirect(url_for('warden_dashboard'))       


class FeedbackForm(Form):
    
    body = TextAreaField('Body', [validators.Length(min=5)])


@app.route('/feedback', methods=['GET', 'POST'])

def feedback():
    form = FeedbackForm(request.form)
    if request.method == 'POST' and form.validate():
        
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO feedback(username,txt) VALUES(%s, %s)",( session['username'], body))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Feedback Submitted', 'success')

        return redirect(url_for('dashboard'))

    return render_template('feedback.html', form=form)


@app.route('/feedback_info')
def feedback_info():
    
    
       cur = mysql.connection.cursor()
       result = cur.execute("SELECT txt,users.username FROM feedback,users WHERE feedback.username=users.username and warden=%s",[session['username']] )
       students = cur.fetchall()
       if result > 0:
          return render_template('feedback_info.html', students=students)
       else:
          msg = 'No feedback has been given yet'
          return render_template('feedback_info.html', msg=msg)
    # Close connection
       cur.close() 

class UpdateForm(Form):
    first_name = StringField('First Name', validators=[InputRequired()])
    second_name = StringField('Second Name', [InputRequired()])
    last_name = StringField('Last Name', [InputRequired()])
    email = StringField('Email', [InputRequired(),Email()])
    
    gender=SelectField('Gender',choices=[('Male','Male'),('Female','Female')])
    GPA=IntegerField('GPA')
    contactno=StringField('Contact No.',[validators.Length(min=7, max=10)])



@app.route('/update',methods=['GET','POST'])
def update():         
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM users WHERE username = %s", [session['username']])

    details = cur.fetchone()
    cur.close()
    # Get form
    form = UpdateForm(request.form)

    # Populate article form fields
    form.first_name.data = details['first_name']
    form.second_name.data = details['second_name']
    form.last_name.data = details['last_name']
    form.email.data = details['email']
    form.gender.data = details['gender']
    form.GPA.data = details['GPA']

    form.contactno.data = details['contactno']

    if request.method == 'POST' and form.validate():

        form.first_name.data = request.form['first_name']
        form.second_name.data =request.form['second_name']
        form.last_name.data = request.form['last_name']
        form.email.data = request.form['email']
        form.gender.data =request.form['gender']
        form.GPA.data = request.form['GPA']
       

        # Create Cursor
        cur = mysql.connection.cursor()
       
        # Execute
        cur.execute ("UPDATE users SET first_name=%s, second_name=%s, last_name=%s , email=%s, gender=%s, GPA=%s where username=%s" ,(form.first_name.data,form.second_name.data,form.last_name.data,form.email.data,form.gender.data,form.GPA.data,session['username']))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Profile Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('update.html', form=form)

class mailform(Form):
   recipient=SelectField('Paid By', choices=[('Parent','Parent'),('Student','Student')])
   receiver_mail= StringField('Recipient Email_ID', [InputRequired(),Email()])
   subject=StringField('Subject',[InputRequired(),Length(min=3, max=20)])
   body=TextAreaField('Message')
   


@app.route('/send_mail',methods=['GET','POST'])
def send_mail():
  form = mailform(request.form)
  if request.method == 'POST' and form.validate():
  
    receiver_mail = form.receiver_mail.data
    subject= form.subject.data
    body=form.body.data
    try:
      msg = Message(subject, sender="abc99@gmail.com",recipients=[receiver_mail])
      msg.body = body           
      mail.send(msg)
      return redirect(url_for('warden_dashboard'))

    except Exception as e:
      return(str(e))  
  
  return render_template('send_mail.html',form=form)          


if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)




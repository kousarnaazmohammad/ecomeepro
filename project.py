from flask import Flask,request,render_template,redirect,url_for,flash,session #flash is a method
from otp import genotp    #fun name,var name,class name---->we call them as identifiers
from cmail import sendmail
from token_1 import encode,decode
import os
import razorpay
import re
import mysql.connector 
from mysql.connector import (connection) 
mydb=mysql.connector.connect(host="localhost",user="root",password="admin",db="ecomee")
app=Flask(__name__)
app.secret_key="kousar@1" #to create flash msgs we create secret_key
app.config['SESSION_TYPE']='filesystem'
client = razorpay.Client(auth=("rzp_test_hO4xe5Tf68Z20c", "dHl9OlOpcvK75y0kLerSIMwI"))
@app.route("/")
def home():
    return render_template('welcome.html')
@app.route("/adminregistration",methods=["GET","POST"])
def adminregistration():
    if request.method=="POST":
        aname=request.form['username']
        aemail=request.form['email']
        apwd=request.form['password']
        address=request.form['address']
        accept=request.form['agree']
        print(request.form)#accessing data from frontend as immutabledictionary format by name attribute
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(email) from admincreate where email=%s',[aemail])
            email_count=cursor.fetchone() #(0,) or (1,)
        except Exception as e:
            print(e)
            flash('connection error')
            return redirect(url_for('adminregistration'))
        else:
            if email_count[0]==0:
                otp=genotp()
                admindata={'aname':aname,'aemail':aemail,'apwd':apwd,"address":address,"accept":accept,"adminotp":otp}
                subject='Ecommerce verification code'
                body=f'Ecommerce otp for admin registration {otp}' #here f str is used to see the dynmically generated otp
                sendmail(to=aemail,subject=subject,body=body)
                flash('otp has send to given mail')
                return redirect(url_for('adminotp',padminotp=encode(data=admindata))) #passinf encripted otp #to send one funcs variable to another function we pass keyword arguments
            elif email_count[0]==1:
                flash('email already exist')
                return redirect(url_for('adminlogin'))
            else:
                flash('wrong email')
                return redirect(url_for('adminregistration')) #...............................
    return render_template('admincreate.html')
@app.route('/index')
def index():
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,price,quantity,category,image_name from items')
        items_data=cursor.fetchall()
    except Exception as e:
        print(e)
        flash("couldn't fetch items")
        return redirect(url_for('home'))
    return render_template('index.html',items_data=items_data)
@app.route('/adminotp/<padminotp>',methods=["GET","POST"])
def adminotp(padminotp):
    if request.method=="POST":
        fotp=request.form['otp']#user given otp
        try:
            decodeotp=decode(data=padminotp)  #decoding the admindata  {'aname':aname,'aemail':aemail,'apwd':apwd,"address":address,"accept":accept,"adminotp":otp}
        except Exception as e:
            flash('something went wrong')
            return redirect(url_for('adminregistration'))
        else:
            if decodeotp['adminotp']==fotp: 
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into admincreate(email,username,password,address,accept) values(%s,%s,%s,%s,%s)',
                [decodeotp['aemail'],decodeotp['aname'],decodeotp['apwd'],decodeotp['address'],decodeotp['accept']])
                mydb.commit()
                cursor.close()
                flash('Admin registration successfull')
                return  redirect(url_for('adminlogin'))
            else:
                flash('otp was wrong')
                return redirect(url_for('adminotp',padminotp=padminotp))
    return render_template('adminotp.html')
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if not session.get('admin'):
        if request.method=="POST":
            aemail=request.form['email']
            alpwd=request.form['password']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select count(email) from admincreate where email=%s',[aemail])
                email_count=cursor.fetchone()
            except Exception as e:
                print(e)
                flash('connection error')
                return redirect(url_for('adminlogin'))
            else:
                if email_count[0]==1:
                    cursor.execute('select password from admincreate where email=%s',[aemail])
                    stored_password=cursor.fetchone()
                    if stored_password[0].decode('utf-8')==alpwd:
                        session['admin']=aemail
                        if not session.get(aemail):
                            session[aemail]={}
                        return redirect(url_for('admindashboard'))  
                    else:
                        flash('email not registered')
                        return redirect(url_for('adminlogin'))#
                elif email_count[0]==0:
                    flash('email was wrong')
                    return redirect(url_for('adminlogin'))
                else:
                    flash('email not registered')
                    return redirect(url_for('adminregistration'))
        return render_template('adminlogin.html')
    else:
        return redirect(url_for('admindashboard'))
@app.route('/admindashboard')
def admindashboard():
    if session.get('admin'):
        return render_template('adminpanel.html')
    else:
        return render_template('adminpanel.html') ########
@app.route('/aforgotpwd',methods=["GET","POST"])
def aforgotpwd():
    if request.method=="POST":
        forgot_email=request.form['email']
        cursor=mydb.cursor('buffered=True')
        cursor.execute('select count(email) from admincreate where email=%s',[forgot_email])
        stored_email=cursor.fetchone()
        if stored_email[0]==1:
            subject='Admin password reset link for ecomee application'
            body=f"click on the link for password update:{url_for('ad_pwdupdate',token=encode(data=forgot_email),_external=True)}" #_external=True this makes the text into link format
            sendmail(to=forgot_email,subject=subject,body=body)
            flash('reset link has send to given email')
            return redirect(url_for('aforgotpwd'))
        elif stored_email[0]==0:
            flash('no email registered please check')
            return redirect(url_for('aforgotpwd'))
    return render_template('forgot.html')
@app.route('/ad_pwdupdate/<token>',methods=["GET","POST"])
def ad_pwdupdate(token):
    if request.method=="POST":
        newpwd=request.form['npassword']
        cpwd=request.form['cpassword']
        try:
            dtoken=decode(data=token)
        except Exception as e:
            print(e)
            flash('email not found')
            return redirect(url_for('adminlogin'))
        else:
            if newpwd==cpwd:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update admincreate set password=%s where email=%s',[newpwd,dtoken])
                mydb.commit()
                flash('password update successfully')
                return redirect(url_for('adminlogin'))
            else:
                flash('password mismatch')
                return redirect(url_for('ad_pwdupdate',token=token))
    return render_template('newpassword.html')
@app.route('/alogout')
def alogout():
    session.pop('admin')
    return redirect(url_for('adminlogin'))
@app.route('/additems',methods=['GET',"POST"])
def additems():
    if session.get('admin'):
        if request.method=="POST":
            title=request.form['title']
            desc=request.form['Discription']
            price=request.form['price']
            category=request.form['category']
            quantity=request.form['quantity']
            item_img=request.files['file']
            filename=genotp()+'.'+item_img.filename.split('.')[-1]
            drname=os.path.dirname(os.path.abspath(__file__))
            print(drname)
            static_path=os.path.join(drname,'static')
            print(static_path)
            item_img.save(os.path.join(static_path,filename))
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into items(item_id,item_name,price,quantity,category,image_name,added_by,description) values(uuid_to_bin(uuid()),%s,%s,%s,%s,%s,%s,%s)',[title,price,quantity,category,filename,session.get('admin'),desc])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('connection error')
                return redirect(url_for('additems'))
            else:
                flash(f'item {title} added successfully')
                return redirect(url_for('additems'))
        return render_template('additem.html')
    else:
        return redirect(url_for('adminlogin'))
@app.route('/viewallitems')
def viewallitems():
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select bin_to_uuid(item_id),item_name,image_name from items where added_by=%s',[session.get('admin')])
            stored_itemdata=cursor.fetchall()
        except Exception as e:
            print(e)
            flash('connection error')
            return redirect(url_for('adminpanel'))
        else:
            return render_template('viewall_items.html',stored_itemdata=stored_itemdata)
    else:
        return render_template('adminlogin')
@app.route('/delete_item/<item_id>')
def delete_item(item_id):
    if session.get('admin'):
        try:
            drname=os.path.dirname(os.path.abspath(__file__))
            static_path=os.path.join(drname,'static')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select image_name from items where item_id=uuid_to_bin(%s)',[item_id])
            stored_imgname=cursor.fetchone()
            print(stored_imgname)
            if stored_imgname in os.listdir(static_path):
                os.remove(os.path.join(static_path,stored_imgname[0]))
            cursor.execute('delete from items where item_id=uuid_to_bin(%s)',[item_id])
            mydb.commit()
        except Exception as e:
            print(e)
            flash("couldn't delete item")
            return redirect(url_for('viewallitems'))
        else:
            flash('item deleted successfully')
            return redirect(url_for('viewallitems'))
    else:
        return redirect(url_for('adminlogin'))
@app.route("/viewsingleitem/<item_id>")
def viewsingleitem(item_id):
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select bin_to_uuid(item_id),item_name,price,quantity,category,image_name,added_by,description from items where item_id=uuid_to_bin(%s)',[item_id])
            stored_itemdata=cursor.fetchone()
        except Exception as e:
            print(e)
            flash('connection problem')
            return redirect(url_for('viewallitems'))
        else:
            return render_template('view_item.html',data=stored_itemdata)
    else:
        return redirect(url_for('adminlogin'))
@app.route('/updateitem/<item_id>',methods=["GET","POST"])
def updateitem(item_id):
    if session.get('admin'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select bin_to_uuid(item_id),item_name,price,quantity,category,image_name,added_by,description from items where item_id=uuid_to_bin(%s)',[item_id])
            stored_itemdata=cursor.fetchone()
        except Exception as e:
            print(e)
            flash('connection problem')
            return redirect(url_for('viewallitems'))
        else:
            if request.method=="POST":
                title=request.form['title']
                desc=request.form['Discription']
                price=request.form['price']
                category=request.form['category']
                quantity=request.form['quantity']
                item_img=request.files['file']
                filename=item_img.filename
                print(item_img)
                if filename=='': #not uploading img
                    img_name=stored_itemdata[5]
                else:
                    img_name=genotp()+'.'+filename.split('.')[-1]
                    drname=os.path.dirname(os.path.abspath(__file__))#C:\pfs6\eccomercepro
                    static_path=os.path.join(drname,'static')
                    if stored_itemdata[5] in os.listdir(static_path):
                        os.remove(os.path.join(static_path,stored_itemdata[5]))
                    item_img.save(os.path.join(static_path,img_name))
                cursor.execute('update items set item_name=%s,price=%s,quantity=%s,category=%s,image_name=%s,description=%s where item_id=uuid_to_bin(%s)',[title,price,quantity,category,img_name,desc,item_id])
                mydb.commit()
                cursor.close()
                flash('item updated successfully')
                return redirect(url_for('viewsingleitem',item_id=item_id))
        return render_template('update_item.html',stored_itemdata=stored_itemdata)
    else:
        return redirect(url_for('admin'))
@app.route('/adminupdateprofile/', methods=["GET", "POST"])
def adminupdateprofile():
  if session.get('admin'):
    try:
      cursor = mydb.cursor(buffered=True)
      cursor.execute('select username,address,dp_image from admincreate where email=%s', [session.get('admin')])
      admin_data = cursor.fetchone()
    except Exception as e:
      print(e)
      flash('connection problem')
      return redirect(url_for('adminpanel'))
    else:
      if request.method == "POST":
        adminname = request.form['adminname']
        address = request.form['address']
        dp_img = request.files['file']  
        print(adminname,address,dp_img)
        if dp_img.filename=='':
          img_name = admin_data[2] 
        else:
          img_name=genotp()+'.'+dp_img.filename.split('.')[-1]#new filename
          drname = os.path.dirname(os.path.abspath(__file__))
          static_path = os.path.join(drname, 'static')
          if admin_data[2] in os.listdir(static_path):
              os.remove(os.path.join(static_path,admin_data[2]))              
          dp_img.save(os.path.join(static_path,img_name))
        cursor.execute('update admincreate set username=%s,address=%s,dp_image=%s where email=%s', [adminname, address, img_name, session.get('admin')])
        cursor.close()
        mydb.commit()
        flash('Profile updated successfully')
        return redirect(url_for('adminupdateprofile'))
    return render_template('adminupdate.html', admin_data=admin_data)
  return redirect(url_for('adminlogin'))
@app.route('/userregistration', methods=['GET', 'POST'])
def userregistration():
    if request.method=="POST":
        uname=request.form['name']
        uemail=request.form['email']
        address=request.form['address']
        upwd=request.form['password']
        gender = request.form['usergender'] 
        print(request.form)
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(user_email) from usercreate where user_email=%s',[uemail])
            uemail_count=cursor.fetchone() 
        except Exception as e:
            print(e)
            flash('connection error')
            return redirect(url_for('userregistration'))
        if uemail_count[0] == 0:
            otp = genotp()
            userdata = {'uname': uname,'uemail': uemail,"address": address,'upwd': upwd,"gender":gender,"userotp": otp}
            subject = 'Ecommerce verification code'
            body = f'Ecommerce otp for user registration {otp}'
            flash('otp has send to given mail')
            sendmail(to=uemail, subject=subject, body=body)
            return redirect(url_for('userotp', puserotp=encode(data=userdata)))
        elif uemail_count[0] == 1:
            flash('Email already exists')
            return redirect(url_for('userlogin'))
        else:
            flash('Wrong email')
            return redirect(url_for('userregistration'))
    return render_template('usersignup.html')
@app.route('/userotp/<puserotp>',methods=["GET","POST"])
def userotp(puserotp):
    if request.method=="POST":
        fotp=request.form['otp']#user given otp
        try:
            decodeotp=decode(data=puserotp)  #decoding the userdata  {'uname':uname,'uemail':uemail,'upwd':upwd,"address":address,"userotp":otp}
        except Exception as e:
            return redirect(url_for('userregistration'))
        else:
            if decodeotp['userotp']==fotp: 
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into usercreate(username,user_email,address,password,gender) values(%s,%s,%s,%s,%s)',
                [decodeotp['uname'],decodeotp['uemail'],decodeotp['address'],decodeotp['upwd'],decodeotp["gender"]])
                mydb.commit()
                cursor.close()
                flash('user registration successfull')
                return  redirect(url_for('userlogin'))
            else:
                flash('otp was wrong')
                return redirect(url_for('userotp',puserotp=puserotp))
    return render_template('userotp.html')
@app.route('/userlogin',methods=['GET','POST'])
def userlogin():
    if not session.get('user'):
        if request.method=="POST":
            uemail=request.form['email']
            upwd=request.form['password']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select count(user_email) from usercreate where user_email=%s',[uemail])
                uemail_count=cursor.fetchone()
                print(uemail_count)
            except Exception as e:
                print(e)
                flash('connection error')
                return redirect(url_for('userlogin'))
            else:
                if uemail_count[0]==1:
                    cursor.execute('select password from usercreate where user_email=%s',[uemail])
                    ustored_password=cursor.fetchone()
                    if ustored_password[0].decode('utf-8')==upwd:
                        session['user']=uemail   #{'user': 'kousarnaazm@gmail.com'}
                        if not session.get(uemail):
                            session[uemail]={}  # {'kousarnaazm@gmail.com': {}, 'user': 'kousarnaazm@gmail.com'}
                        return redirect(url_for('index'))  #
                    else:
                        flash('Incorrect password')
                        return redirect(url_for('userlogin'))
                elif uemail_count[0]==0:
                    flash('email was wrong')
                    return redirect(url_for('userlogin'))
                else:
                    flash('email not registered')
                    return redirect(url_for('userregistration'))
        return render_template('userlogin.html')
    else:
        return redirect(url_for('index')) #
@app.route('/userforgotpwd',methods=["GET","POST"])
def uforgotpwd():
    if request.method=="POST":
        forgot_email=request.form['email']
        cursor=mydb.cursor('buffered=True')
        cursor.execute('select count(user_email) from usercreate where user_email=%s',[forgot_email])
        stored_email=cursor.fetchone()
        if stored_email[0]==1:
            subject='user password reset link for ecomee application'
            body=f"click on the link for password update:{url_for('user_pwdupdate',token=encode(data=forgot_email),_external=True)}" #_external=True this makes the text into link format
            sendmail(to=forgot_email,subject=subject,body=body)
            flash('reset link has send to given email')
            return redirect(url_for('uforgotpwd'))
        elif stored_email[0]==0:
            flash('no email registered please check')
            return redirect(url_for('uforgotpwd'))
    return render_template('forgot.html')
@app.route('/user_pwdupdate/<token>',methods=["GET","POST"])
def user_pwdupdate(token):
    if request.method=="POST":
        newpwd=request.form['npassword']
        cpwd=request.form['cpassword']
        try:
            dtoken=decode(data=token)
        except Exception as e:
            print(e)
            flash('email not found')
            return redirect(url_for('userlogin'))
        else:
            if newpwd==cpwd:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update usercreate set password=%s where user_email=%s',[newpwd,dtoken])
                mydb.commit()
                flash('password update successfully')
                return redirect(url_for('userlogin'))
            else:
                flash('password mismatch')
                return redirect(url_for('user_pwdupdate',token=token))
    return render_template('newpassword.html')
@app.route('/ulogout')
def ulogout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('userlogin'))
    return redirect(url_for('userlogin'))
@app.route('/category/<ctype>',methods=["GET","POST"])
def category(ctype):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,price,quantity,category,image_name from items where category=%s',[ctype])
        items_data=cursor.fetchall()
    except Exception as e:
        print(e)
        flash("couldn't fetch items")
        return redirect(url_for('index'))
    return render_template('dashboard.html',items_data=items_data)
@app.route('/addcard/<itemid>/<name>/<float:price>/<qyt>/<category>/<image>')
def addcart(itemid,name,price,category,image,qyt):
    if not session.get('user'):
        return redirect(url_for('userlogin'))
    else:
        print(session)
        if itemid not in session.get(session.get('user')):
            session.get(session.get('user'))[itemid]=[name,price,1,image,category,qyt] #session.get{'kousarnaazm@gmail.com}[itemid]=[]
            session.modified=True #to reflect
            print(session)
            flash(f'item {name} added to cart')
            return redirect(url_for('index'))
        else:
            session[session.get('user')][itemid][2]+=1
            flash('item already in card')
            return redirect(url_for('index'))
@app.route('/viewcart')
def viewcart():
    if session.get('user'):
        if session.get(session.get('user')):
            items=session.get(session.get('user')) #shows session data of login email
        else:
            items='empty'
        if items=='empty':
            flash('no items added in cart')
        return render_template('cart.html',items=items)
    else:
        return redirect(url_for('userlogin'))
@app.route('/removecartitem/<itemid>')
def removecartitem(itemid):
    if session.get('user'):
        session.get(session.get('user')).pop(itemid)
        session.modified=True
        flash('item removed from cart')
        return redirect(url_for('viewcart'))
    else:
        return redirect(url_for('userlogin'))
@app.route('/description/<itemid>')
def description(itemid):
    try:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select bin_to_uuid(item_id),item_name,description,price,quantity,category,image_name from items where item_id=uuid_to_bin(%s)',[itemid])
        item_data=cursor.fetchone()
    except Exception as e:
        print(e)
        flash("couldn't fetch items")
        return redirect(url_for('index'))
    return render_template('description.html',item_data=item_data)
@app.route('/payment/<itemid>/<name>/<float:price>',methods=["GET","POST"])
def payment(itemid,name,price):
    try:
        qyt=int(request.form.get('qyt'))
        amount=price*100 #convert price into paise
        total_price=qyt*amount
        print(amount,qyt,total_price)
        print(f'creating payment for item:{itemid},name:{name},price:{price}')
        #creating razorpay ord
        order=client.order.create({
            'amount':total_price,
            'currency':'INR',
            'payment_capture':'1'
        })
        print(f"order create:{order}")
        return render_template('pay.html',order=order,itemid=itemid,name=name,price=total_price,qyt=qyt)
    except Exception as e:
        #log the error and return a 400 response
        print(f'error creating order:{str(e)}')
        flash('error in creating order')
        return redirect(url_for('index'))
@app.route('/success',methods=["GET","POST"])
def success():
    #extract payment details for the form
    payment_id=request.form.get('razorpay_payment_id')
    order_id=request.form.get('razorpay_order_id')
    signature=request.form.get('razorpay_signature')
    name=request.form.get('name')
    itemid=request.form.get('itemid')
    total_price=request.form.get('total_price')
    qyt=request.form.get('qyt')
    #verification process
    params_dict={
        'razorpay_order_id':order_id,
        'razorpay_payment_id':payment_id,
        'razorpay_signature':signature
    }
    try:
        client.utility.verify_payment_signature(params_dict)
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into orders(itemid,item_name,total_price,user,qty) values(uuid_to_bin(%s),%s,%s,%s,%s)',[itemid,name,total_price,session.get('user'),qyt])
        mydb.commit()
        cursor.close()
    except razorpay.errors.SignatureVerifivationError:
        return 'payment verification failed',400
    else:
        flash('order placed successfully')
        return 'youre order is placed'
@app.route('/orders')
def orders():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select orderid,bin_to_uuid(itemid),item_name,total_price,qty,user from orders where user=%s',[session.get('user')])
            ordlist=cursor.fetchall()
        except Exception as e:
            print(f'error in fetching orders:{e}')
            flash("couldn't fetch orders")
            return redirect(url_for('index'))
        else:
            return render_template('orders.html',ordlist=ordlist)
    else:
        return redirect(url_for('userlogin'))
@app.route('/search',methods=["GET","POST"])
def search():
        if request.method=="POST":
            search=request.form["search"]
            strg=["A-Za-z0-9"]
            pattern=re.compile(f'^{strg}',re.IGNORECASE)
            if (pattern.match(search)):
                try:
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select bin_to_uuid(item_id),item_name,price,quantity,category,image_name,description from items where item_name like %s or price like %s or category like %s or description like %s',['%'+search+'%','%'+search+'%','%'+search+'%','%'+search+'%'])
                    searched_data=cursor.fetchall()
                except Exception as e:
                    print(f'error in search{e}')
                    flash('could not fetch data')
                    return redirect(url_for('index'))
                else:
                    return render_template('dashboard.html',items_data=searched_data)
            else:
                flash('no item found')
                return redirect(url_for('index'))
        return render_template('index.html')
@app.route('/addrevview/<itemid>',methods=["GET","POSt"])
def addreview(itemid):
    if session.get('user'):
        if request.method=="POST":
            title=request.form['title']
            reviewtext=request.form['review']
            rating=request.form['rate']
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into reviews(title,review,rating,itemid,username) values(%s,%s,%s,uuid_to_bin(%s),%s)',[title,reviewtext,rating,itemid,session.get('user')])
                mydb.commit()
            except Exception as e:
                print(f'error in inserting review:{e}')
                flash("can't add review")
                return redirect(url_for('description',itemid=itemid))
            else:
                cursor.close()
                flash('review has been added')
                return redirect(url_for('description',itemid=itemid))
        return render_template('review.html')
    else:
        return redirect(url_for('userlogin'))






app.run(use_reloader=True,debug=True) 


#ye local system(i mean ismey ch changes karsaktey habi app.py kaam karta nai) may hota aws may deployment kartey hai kako



#cursor.execute("create table if not exists contactus (name varchar(100) DEFAULT NULL,email varchar(100) DEFAULT NULL,message text) ")





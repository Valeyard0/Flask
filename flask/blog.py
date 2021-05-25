from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
import email_validator
from functools import wraps



#Kullanici Giris Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if("logged_in" in session):
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayi goruntulemek icin lutfen giris yapin","danger")
            return redirect(url_for("login"))
    
    return decorated_function

# Kullanici Kayit Form
class RegisterForm(Form):
    name = StringField("Isim Soyisim :",validators=[validators.Length(min = 4 , max = 25)])
    username = StringField("Kullanici Adi :",validators=[validators.Length(min = 5 , max = 35)])
    email = StringField("Email :",validators=[validators.Email(message= "Lutfen Gecerli Bir Email Giriniz")])
    password = PasswordField("Parola :",validators=[
        validators.DataRequired(message= "Lutfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolaniz Uyusmuyor")

    ])
    confirm = PasswordField("Parola Dogrula ")



app = Flask(__name__)
@app.route("/")
def index():
    return render_template("index.html")

app.secret_key = "val"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)


@app.route("/about")
def about():
    return render_template("includes/about.html")

#Kayit Olma
@app.route("/register",methods = ["GET" ,"POST"])
def register():
    form = RegisterForm(request.form)
    if(request.method == "POST" and form.validate()):
        name = form.name.data
        
        username = form.username.data
        
        email = form.email.data
        
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        
        mysql.connection.commit()
        
        cursor.close()
        flash("Kayit islemi basariyla tamamlandi","success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)


class LoginForm(Form):
    username = StringField("Kullanici Adi ")
    password = PasswordField("Parola ")




@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if(request.method == "POST"):
        username = form.username.data
        
        password_entered = form.password.data
        
        cursor = mysql.connection.cursor() # işlem yapmaya olanak tanır
        
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if(result > 0):
            data = cursor.fetchone()
            real_password = data["password"]
            if(sha256_crypt.verify(password_entered,real_password)):
                flash("Basariyla Giris Yaptiniz","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanizi Yanlis Girdiniz","danger")
                return redirect(url_for("login"))    
        else:
            flash("Boyle bir kullanici bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("/login.html",form = form)


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if(result > 0):
        articles = cursor.fetchall()
        return render_template("includes/dashboard.html",articles = articles)

    else:
        return render_template("includes/dashboard.html")
        





@app.route("/addarticle", methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if(request.method == "POST" and form.validate()):
        title = form.title.data
        
        content = form.content.data
        
        cursor = mysql.connection.cursor()
        
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        
        cursor.execute(sorgu,(title,session["username"],content))
        
        mysql.connection.commit()
        
        flash("Makale Basariyla Eklendi","success")
        cursor.close()

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)


class ArticleForm(Form):
    title = StringField("Makale Basligi :",validators=[validators.Length(min = 5 , max = 100)])
    content = TextAreaField("Makale Icerigi :",validators=[validators.Length(min = 10)])

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if(result > 0):
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")



if __name__ == "__main__":
    app.run(debug=True)
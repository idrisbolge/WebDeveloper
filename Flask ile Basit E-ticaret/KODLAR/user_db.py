# This file contains an example Flask-User application.
# To keep the example simple, we are applying some unusual techniques:
# - Placing everything in one file
# - Using class-based configuration (instead of file-based configuration)
# - Using string-based templates (instead of file-based templates)

import datetime
from flask import Flask, request, render_template_string, render_template
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin
from sqlalchemy.sql import table, column, select 
from sqlalchemy import MetaData
import sqlite3
import os

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'
    
    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///basic_app.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids SQLAlchemy warning

    # Flask-Mail SMTP server settings 
    # #USER_ENABLE_EMAIL=True ise bu ayarları yapın. Google güvenlik ayarları bu işlemi yapmanıza izin vermeyebilir.
    #Detaylı bilgiyi https://support.google.com/accounts/answer/6010255?p=lsa_blocked&hl=en-GB&visit_id=636759033269131098-410976990&rd=1 dan edinebilirsiniz. 
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = int(os.getenv('MAIL_PORT','465'))
    MAIL_USE_SSL = int(os.getenv('MAIL_USE_SSL',False))
    MAIL_USE_TLS = int(os.getenv('MAIL_USE_TLS',True))
    MAIL_USERNAME = 'xyz@gmail.com' # gmail adresinizi girin
    MAIL_PASSWORD = 'sifre' # gmail şifrenizi girin
    MAIL_DEFAULT_SENDER = '"MyApp" <xyz@gmail.com>'

    # Flask-User settings
    USER_APP_NAME = "E- Ticaret Sitesi"      # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = True        # Enable email authentication
    USER_ENABLE_USERNAME = False    # Disable username authentication
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"
   # Daha detaylı bilgi https://flask-user.readthedocs.io/en/latest/configuring_settings.html de bulunabilir.
def create_app():
    """ Flask application factory """
    
    # Create Flask app load app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask-BabelEx
    babel = Babel(app)
    # Initialize Flask-SQLAlchemy
    @babel.localeselector
    def get_locale():
       translations = [str(translation) for translation in babel.list_translations()]
    #   return request.accept_languages.best_match(translations)
    # @babel.localeselector
    #def get_locale():
    #   if request.args.get('lang'):
    #       session['lang'] = request.args.get('lang')
    #       return session.get('lang', 'tr')

    db = SQLAlchemy(app)
 

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!


    # Database'deki tablolarda işlem yapmak için class yapılarıyla belirledik.
    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')

        # User information
        first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

        # Define the relationship to Role via UserRoles
        roles = db.relationship('Role', secondary='user_roles')

    # Define the Role data-model

    class Gonderi(db.Model):
        __tablename__ = 'gonderiler'
        id = db.Column(db.Integer, autoincrement=True, primary_key=True)
        baslik=db.Column(db.String(40))
        govde = db.Column(db.String(140))
        timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow())
        user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    class Sepet(db.Model):
        __tablename__ = 'sepetler'
        id = db.Column(db.Integer, autoincrement=True, primary_key=True)
        urunadi = db.Column(db.String(140))
        urunAdet = db.Column(db.String(20))
        timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow())
        user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    class GecmisSepet(db.Model):
        __tablename__ = 'GecmisSepetler'
        id = db.Column(db.Integer, autoincrement=True, primary_key=True)
        urunadi = db.Column(db.String(140))
        urunAdet = db.Column(db.String(20))
        timestamp = db.Column(db.DateTime, index=True, default=datetime.datetime.utcnow())
        user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))  
     
    class Isim(db.Model):
         __tablename__ = 'isimler'
         id = db.Column(db.Integer, autoincrement=True, primary_key=True)
         isim=db.Column(db.String(40))
        

    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    # Define the UserRoles association table
    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(app, db, User)

    # Create all database tables
    db.create_all()
    engine = create_engine('sqlite:///basic_app.sqlite')
    meta = MetaData(engine,reflect=True)
    table = meta.tables['gonderiler']
    table_isim = meta.tables['isimler']
    table_sepet = meta.tables['sepetler']
    table_gecmissepet = meta.tables['GecmisSepetler']

    # Create 'member@example.com' user with no roles

    #Kullanıcıları belirledik. 2 Üye 1 Admin Tanımladık.
    if not User.query.filter(User.email == 'member@example.com').first():
        user = User(
            email='member@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user.roles.append(Role(name='Member'))
        db.session.add(user)
        db.session.commit()
    
    if not User.query.filter(User.email == 'member1@example.com').first():
        user = User(
            email='member1@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user.roles.append(Role(name='Member'))
        db.session.add(user)
        db.session.commit()
    
    # Create 'admin@example.com' user with 'Admin' and 'Agent' roles
    if not User.query.filter(User.email == 'admin@example.com').first():
        user = User(
            email='admin@example.com',
            email_confirmed_at=datetime.datetime.utcnow(),
            password=user_manager.hash_password('Password1'),
        )
        user.roles.append(Role(name='Admin'))
        user.roles.append(Role(name='Agent'))
        db.session.add(user)
        db.session.commit()

   

    # Sayfanın Giriş sayfası
    @app.route('/')
    def home_page():
        return render_template_string("""
                {% extends "flask_user_layout.html" %}
                {% block content %}
                    <h2>{%trans%}Ana sayfa{%endtrans%}</h2>
                    <h1>{%trans%}Bu web sitesinin anasayfasıdır{%endtrans%}</h1>
                    <p><a href={{ url_for('user.register') }}>{%trans%}Kayıt ol{%endtrans%}</a></p>
                    <p><a href={{ url_for('user.login') }}>{%trans%}Giriş Yap{%endtrans%}</a></p>
                    <p><a href={{ url_for('home_page') }}>{%trans%}Ana sayfa{%endtrans%}</a> (Herkes erişebilir)</p>
                    <p><a href={{ url_for('member_page') }}>{%trans%}Üye sayfası{%endtrans%}</a> (Giriş gerekli: member@example.com / Password1)</p>
                    <p><a href={{ url_for('admin_page') }}>{%trans%}Admin sayfası{%endtrans%}</a> (Rol gerekli: admin@example.com / Password1)</p>
                    <p><a href={{ url_for('guncellemeler') }}>{%trans%}Güncellenen ürünler{%endtrans%}</a></p>
                    <p><a href={{ url_for('urunsatisbilgisi') }}>{%trans%}Urun Satış Bilgisi{%endtrans%}</a></p>
                    <p><a href={{ url_for('urunsatisbilgisitarih') }}>{%trans%}Urun Satış Bilgisi(Tarihli){%endtrans%}</a></p>

                    <p><a href={{ url_for('user.logout') }}>{%trans%}Çıkış{%endtrans%}</a></p>
                {% endblock %}
                """)

    #tarihe göre satılan ürün sayısı
    @app.route('/urunsatisbilgisitarih')
    def urunsatisbilgisitarih():
        return render_template('tarihbul.html')

    #tarihe göre sıralamak için tarihi çekmemiz lazım. Gerekenler :
    @app.route('/bultrh', methods = ['POST','GET']) 
    def bultrh():
        con = sqlite3.connect("basic_app.sqlite")
        con.row_factory = sqlite3.Row
        if request.method == 'POST':
            tarih = request.form['trh']
            try:
                with con:
                    cur = con.cursor()
                    cur.execute("select * from GecmisSepetler where timestamp > '"+tarih+"'")
                    rows = cur.fetchall()
                    msg = "Kayıtlar Bulundu"
            except:
                con.rollback()      
                msg = "Kayıtlar bulunurken hata"

            finally:
                con.close()
                return render_template("tarihsonuc.html", msg = msg, rows=rows)  
        
    #Tüm zamanlara göre satılan ürün sayısı
    @app.route('/urunsatisbilgisi')
    def urunsatisbilgisi():
        con = sqlite3.connect("basic_app.sqlite")
        con.row_factory = sqlite3.Row
   
        cur = con.cursor()
        cur.execute("select urunadi, Count(*) AS sayi FROM GecmisSepetler group by urunadi order by Count(*) DESC")
   
        rows = cur.fetchall()
        return render_template('urunsatisbilgisi.html',rows = rows)  

    #Tüm ürünlerin güncel hallerini listeleme
    @app.route('/guncellemeler')
    def guncellemeler():
        con = sqlite3.connect("Data.db")
        con.row_factory = sqlite3.Row
   
        cur = con.cursor()
        cur.execute("select * from Urunler")
   
        rows = cur.fetchall()
        return render_template('guncellenenler.html',rows = rows)        


    # Sadece üyelerin girebildiği Sayfa
    @app.route('/members')
    @roles_required('Member')
   # @login_required  # Use of @login_required decorator
    def member_page():
        return render_template_string("""
            {% extends "flask_user_layout.html" %}
            {% block content %}
            <h2>{%trans%}Üyeler sayfası {%endtrans%}</h2>
            <h1>{%trans%} Sisteme giriş yapanlar bu sayfayı görüntüleyebilir{%endtrans%}</h1>
            <p><a href={{ url_for('gonderi_islemleri') }}>{%trans%}Gönderi İşlemleri{%endtrans%}</a></p>
            <p><a href={{ url_for('Sepet_islemleri') }}>{%trans%}Sepet İşlemleri{%endtrans%}</a></p>
            <p><a href={{ url_for('user.register') }}>{%trans%}Kayıt ol{%endtrans%}</a></p>
            <p><a href={{ url_for('user.login') }}>{%trans%}Giriş Yap{%endtrans%}</a></p>
            <p><a href={{ url_for('home_page') }}>{%trans%}Ana sayfa{%endtrans%}</a> (Herkes erişebilir)</p>
            <p><a href={{ url_for('member_page') }}>{%trans%}Üye sayfası{%endtrans%}</a> (Giriş gerekli: member@example.com / Password1)</p>
            <p><a href={{ url_for('admin_page') }}>{%trans%}Admin sayfası{%endtrans%}</a> (Rol gerekli: admin@example.com / Password1)</p>
             <p><a href={{ url_for('user.logout') }}>{%trans%}Çıkış{%endtrans%}</a></p>
             {% endblock %}
              """)
    #üyelerin yapacağı işlemleri seçeceği sayfaya yönlendirir.
    @app.route('/Sepet_islemleri')
    @login_required
    def Sepet_islemleri():
        return render_template('MusteriHome.html')


    #Ürünleri listeleme bölümü 
    @app.route('/urunsatinal')
    @login_required
    def urunsatinal():
        con = sqlite3.connect("Data.db")
        con.row_factory = sqlite3.Row
   
        cur = con.cursor()
        cur.execute("select * from Urunler")
   
        rows = cur.fetchall()
        return render_template('UrunSatin.html',rows = rows)

    #seçilen ürünü sepete ekleme işlemi
    @app.route('/SepeteEkle', methods = ['POST', 'GET'])
    @login_required
    def SepeteEkle():
        if request.method == 'POST':
            try:
                urunadi = request.form['urunadi']
                urunAdet = request.form['urunAdet']
                sepet = Sepet(urunadi = urunadi, urunAdet = urunAdet, user_id = current_user.id)  
                db.session.add(sepet)
                db.session.commit()
                msg = "Sepete başarı ile eklendi"
            except:
                msg = "Sepete kayıt işlemi sırasında hata oluştu"
                    
            finally:
                return render_template("sonuc.html", msg = msg)

    #Sepetteki ürünleri listeleme
    @app.route('/sepetlistele')
    @login_required    # bunu kapatmamalıyız dikkat kapatırsak insanın anlamayacağı hata alırız, id boş geldiği için builtins.AttributeError hatası alırız
    def sepetlistele():
        db_uri =  'sqlite:///basic_app.sqlite'
        engine = create_engine(db_uri)
        conn = engine.connect()
        select_st=select([table_sepet.c.id, table_sepet.c.urunadi, table_sepet.c.urunAdet]).where(table_sepet.c.user_id==current_user.id)
        rows = conn.execute(select_st)
        return render_template("sepetlistele.html", rows = rows)

    #Sepetteki ürünün adetini id numarasına göre değiştirme
    @app.route('/UrunAdetDegistir', methods = ['POST','GET'])
    @login_required
    def UrunAdetDegistir():
        if request.method == 'POST':
            con = sqlite3.connect("basic_app.sqlite")
            try:
                urunid = request.form['urunid']
                urunAdet = request.form['urunAdet']

                with  con:
                    sorgu = '''update sepetler set urunAdet = ?  where id = ?  '''
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute(sorgu,(str(urunAdet),urunid))
                    msg = "Güncelleme başarılı"
      
            except:
                con.rollback()
                msg = "Güncelleme başarısız"
      
            finally:
                con.close()
                return render_template("sonuc.html", msg = msg)
    #Sepetteki herhangi bir ürünü id numarasına göre silme
    @app.route('/UrunSil', methods = ['POST','GET'])
    @login_required
    def UrunSil():
        if request.method == 'POST':
            con = sqlite3.connect("basic_app.sqlite")
            try:
                silinenid = request.form['silinenid']

                with  con:
                    sorgu = 'delete from sepetler  where id = ? '
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute(sorgu,(silinenid))
                    msg = "Silme başarılı"
      
            except:
                con.rollback()
                msg = "Silme başarısız"
      
            finally:
                con.close()
                return render_template("sonuc.html", msg = msg)
    #Sepet Boşaltma
    @app.route('/UrunleriSil', methods = ['POST','GET'])
    @login_required
    def UrunleriSil():
        if request.method == 'POST':
            con = sqlite3.connect("basic_app.sqlite")
            try:
                with  con:
                    sorgu = 'delete from sepetler'
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute(sorgu)
                    msg = "Sepet  başarılı ile boşaltıldı"
      
            except:
                con.rollback()
                msg = "Sepet boşaltma başarısız"
      
            finally:
                con.close()
                return render_template("sonuc.html", msg = msg)
    #Ürünü/ürünleri satın alma
    @app.route('/Satis',methods = ['POST','GET'])
    @login_required
    def Satis():
        if request.method == 'POST':
            con = sqlite3.connect("basic_app.sqlite")
            idnu = current_user.id
            
            try:
                with con:
                    sorgu = "insert into GecmisSepetler (urunadi,urunAdet,timestamp,user_id) select sepetler.urunadi, sepetler.urunAdet, sepetler.timestamp, sepetler.user_id from sepetler where sepetler.user_id = ?"
                    sorgu2 = 'delete from sepetler where user_id = ?'
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute(sorgu,(idnu))
                    con.commit()
                    cur.execute(sorgu2,(idnu))
                    con.commit()
                    msg = "Satın alma başarılı"
            except:
                msg = "Satın almada hata oluştu"
            
            finally:
                con.close()
                return render_template("sonuc.html",msg = msg)
    #Şu ana kadar satılan ürünler
    @app.route('/gecmissepet')
    @login_required
    def gecmissepet():
        db_uri =  'sqlite:///basic_app.sqlite'
        engine = create_engine(db_uri)
        conn = engine.connect()
        select_st=select([table_gecmissepet.c.id, table_gecmissepet.c.urunadi, table_gecmissepet.c.urunAdet, table_gecmissepet.c.timestamp]).where(table_gecmissepet.c.user_id==current_user.id)
        rows = conn.execute(select_st)
        return render_template("gecmissepetliste.html", rows =rows)


    @app.route('/gonderi_islemleri')
    @login_required    # Use of @login_required decorator
    def gonderi_islemleri():
         return render_template('/home.html')
    @app.route('/yeni_gonderi')
    @login_required    # Use of @login_required decorator
    def yeni_gonderi():
        return render_template('gonderi.html')

    
    @app .route('/gonderi_ekle', methods = ['POST', 'GET'])
    @login_required    # Use of @login_required decorator
    def gonderi_ekle():
        if request.method == 'POST':
            try:
                baslik = request.form['baslik']
                govde = request.form['govde']
                gonderi = Gonderi(
                    baslik=baslik,
                    govde=govde,
                     user_id=current_user.id
                    )  
                db.session.add(gonderi)   
                db.session.commit()
                msg = "Kayıt başarı ile eklendi"
            except:
                msg = "Kayıt işlemi sırasında hata oluştu"
                    
            finally:
                return render_template("sonuc.html", msg = msg)
    
    @app.route('/listele')
    @login_required    # bunu kapatmamalıyız dikkat kapatırsak insanın anlamayacağı hata alırız, id boş geldiği için builtins.AttributeError hatası alırız
    def listele():
        db_uri =  'sqlite:///basic_app.sqlite'
        engine = create_engine(db_uri)
        conn = engine.connect()
        select_st=select([table.c.baslik, table.c.govde]).where(table.c.user_id==current_user.id)
        rows = conn.execute(select_st)
        return render_template("listele.html", rows =rows)



    #Sadece Adminlerin göreceği sayfayı tanımlama
    @app.route('/admin_page')
    @roles_required('Admin') #Use of @roles_required decorator
    def admin_page():
        return render_template_string("""
             {% extends "flask_user_layout.html" %}
              
            {% block content %}
                <h2>{%trans%}Admin Sayfası{%endtrans%}</h2>
                <h1>{%trans%}Bu yalnızca adminlerin giriş yapabildiği bir sayfadır{%endtrans%}</h1>
                <p><a href={{ url_for('admin') }}>{%trans%}Admin İşlemleri{%endtrans%}</a></p>
                <p><a href={{ url_for('isim_sayfasi') }}>{%trans%}İsim Girişi{%endtrans%}</a></p>
                <p><a href={{ url_for('user.register') }}>{%trans%}Kayıt ol{%endtrans%}</a></p>
                <p><a href={{ url_for('user.login') }}>{%trans%}Giriş Yap{%endtrans%}</a></p>
                <p><a href={{ url_for('home_page') }}>{%trans%}Ana sayfa{%endtrans%}</a> (Herkes erişebilir)</p>
                <p><a href={{ url_for('member_page') }}>{%trans%}Üye sayfası{%endtrans%}</a> (Giriş gerekli: member@example.com / Password1)</p>
                <p><a href={{ url_for('admin_page') }}>{%trans%}Admin sayfası{%endtrans%}</a> (Rol gerekli: admin@example.com / Password1)</p>
                <p><a href={{ url_for('user.logout') }}>{%trans%}Çıkış{%endtrans%}</a></p>
            {% endblock %}
             """)
    
    #Sadece Adminlerin göreceği sayfa
    @app.route('/admin')
    @roles_required('Admin')
    def admin():
        return render_template('admin.html')

    @app.route('/isim_sayfasi')
    @roles_required('Admin')
    def isim_sayfasi():
        return render_template('isim.html')

    @app.route('/isim_ekle', methods = ['POST', 'GET'])
    @roles_required('Admin')
    def isim_ekle():
        if request.method == 'POST':
            try:
                isim = request.form['isim']
                isim = Isim(isim=isim)
                db.session.add(isim)
                db.session.commit()
                msg = "İsim başarı ile eklendi"
            except:
                msg = "İsim ekleme işlemi sırasında hata oluştu"
            finally:
                return render_template("home_isim.html", msg = msg)
    @app.route('/isim_listele')
    def isim_listele():
        db_uri =  'sqlite:///basic_app.sqlite'
        engine = create_engine(db_uri)
        conn = engine.connect()
        select_st=select([table_isim.c.isim])
        rows = conn.execute(select_st)
        return render_template("isim_listele.html", rows =rows)



    #Ürün ekleme sayfasına yönlendirme
    @app.route('/urunekle')
    def urunekle():
        return render_template('urunekle.html')
    #Ürün ekleme
    @app.route('/kayit_ekle', methods = ['POST', 'GET'])
    def kayit_ekle():
        if request.method == 'POST':
            try:
                adi = request.form['urunadi']
                fiyati = request.form['urunfiyat']

                with sqlite3.connect("Data.db") as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO Urunler (urunadi,urunfiyat) VALUES (?,?)",(adi,fiyati) )
                    con.commit()
                    msg = "Kayit basari ile eklendi"
            except:
                    con.rollback()
                    msg = "Kayit islemi sirasinda hata olustu"
      
            finally:
                    con.close()
                    return render_template("sonuc.html",msg = msg)
   #ürün arama sayfasına yönlendirme
    @app.route('/urunarama')
    def urunarama():
        return render_template('urunarama.html')

    #Ürün adına göre arama yapma
    @app.route('/bul', methods = ['POST','GET'])
    def bul():
        if request.method == 'POST':
            try:
                isim = request.form['urunadi']
                with sqlite3.connect("Data.db") as con:
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute("select * from Urunler where urunadi = '%s' " %isim)
                    rows = cur.fetchall()
                    msg = "Kayit bulundu"
            
            except:
                con.rollback()
                msg = "Kayit bulunamadı"
      
            finally:
                con.close()
                return render_template("urunguncelle.html",msg = msg,rows=rows)  
    #Ürünü güncelleme
    @app.route('/guncelle', methods = ['POST', 'GET'])
    def guncelle():
        if request.method == 'POST':
            try:
                u_adi = request.form['ad']
                u_fiy = request.form['fiyat']
                secil = request.form["secilen"]

                with sqlite3.connect("Data.db") as con:
                    sorgu = '''update Urunler set urunadi = ? , urunfiyat = ? where id = ?  '''
                    con.row_factory = sqlite3.Row
                    cur = con.cursor()
                    cur.execute(sorgu,(u_adi,u_fiy,secil[0]))
                    msg = "Güncelleme başarılı"
      
            except:
                con.rollback()
                msg = "Güncelleme başarısız"
      
            finally:
                con.close()
                return render_template("sonuc.html", msg = msg)
    #Ürün silme sayfasına yönlendirme
    @app.route('/urunsilme')
    def urunsilme():
        con = sqlite3.connect("Data.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("select * from Urunler")
        rows = cur.fetchall()
        return render_template("urunsilme.html", rows = rows)


    #Ürün silme 
    @app.route('/sil', methods = ['POST', 'GET'])
    def sil():
        con = sqlite3.connect('Data.db')
        con.row_factory = sqlite3.Row

        if request.method == 'POST':
            secil = request.form['secilen']

            try:
                with con:
                    sorgu = 'DELETE FROM Urunler WHERE id = ? '
                    cur = con.cursor()
                    cur.execute(sorgu,str(secil))
                    con.commit()
                    msg = "Silme başarılı"
                    return render_template("sonuc.html", msg = msg)
            except:
                con.rollback()
                msg = "Silme başarısız"
      
            finally:
                con.close()
    #Üyelerin üye işlemlerini yapacağı sayfaya yönlendirme
    @app.route('/uye')
    def Anasayfa():
        return render_template("MusteriHome.html")
    #ürünleri listeleme işlemi
    @app.route('/urunlistesi')
    def urunlistesi():
        con = sqlite3.connect("Data.db")
        con.row_factory = sqlite3.Row
   
        cur = con.cursor()
        cur.execute("select * from Urunler")
   
        rows = cur.fetchall()
        return render_template("Urunler.html", rows = rows)

        #Ürün satın alma sayfasına yönlendirme
        @app.route('/urunsatinal')
        def urunsatinal():
            con = sqlite3.connect("Data.db")
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("select * from Urunler")
            rows = cur.fetchall()
            return render_template("UrunSatin.html", rows = rows)

    return app


# Start development web  server
if __name__ == '__main__':
    app = create_app()
   # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='127.0.0.1', port=5000, debug=True)

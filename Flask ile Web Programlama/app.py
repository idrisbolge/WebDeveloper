from flask import Flask,render_template,request
import sqlite3 as sql
app=Flask(__name__)


conn=sql.connect('veritabani.db')
conn.execute('CREATE TABLE IF NOT EXISTS ogrenciler(ad TEXT, adres TEXT, sehir TEXT)')
conn.close()

@app.route('/')
def home():

    return render_template('/home.html')


@app.route('/yeni_ogrenci')
def yeni_ogrenci():
    return render_template('ogrenci.html')

@app.route('/kayit_ekle',methods =['POST','GET'])
def kayit_ekle():
    if request.method=='POST':
        try:
            isim=request.form['ad']
            addr=request.form['adres']
            shr=request.form['sehir']

            with sql.connect('veritabani.db') as con:
                cur=con.cursor()
                cur.execute("INSERT INTO ogrenciler (ad,adres,sehir) VALUES (?,?,?)",(isim,addr,shr))
                con.commit()
                msg="kayıt başarı ile eklendi"
                
        except:
            con.rollback()
            msg="Kayıt işlemi sırasında hata oluştu.."

        finally:
            con.close()
            return render_template("sonuc.html", msg=msg)

@app.route('/listele')
def listele():
    con=sql.connect('veritabani.db')
    con.row_factory=sql.Row

    cur=con.cursor()
    cur.execute("select * from ogrenciler")

    rows=cur.fetchall()
    return render_template("listele.html",rows=rows)

if __name__=="__main__":
    app.run(debug=True)

from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(300), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Article %r>' % self.id


class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    eq = db.Column(db.String(100), nullable=False)
    col = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('article.id'))

    def __repr__(self):
        return '<Equipment %r>' % self.id


@app.route('/')
@app.route('/home')
@app.route('/inventory')
def inventory():
    q = request.args.get('q')
    if q:
        articles = Article.query.filter(Article.title.contains(q)).all()
    else:
        articles = Article.query.order_by(Article.date.desc()).all()
    return render_template("inventory.html", articles=articles)


# тут шляпа надо переделывать
@app.route('/inventory/<int:id>')
def equip(id):
    article = Article.query.get(id)
    equipment = Equipment.query.all()
    return render_template("eq.html", article=int(article.id), equipment=equipment, name=article)


'''@app.route('/inventory/<int:id>/update')
def inventory_detail(id):
    article = Article.query.get(id)
    equipment = Equipment.query.get(id)
    return render_template("inventory_detail.html", article=article, equipment=equipment)
'''


@app.route('/inventory/<int:id>/<int:eq_id>/add', methods=['POST', 'GET'])
def addeq(id, eq_id):
    article = Article.query.get(id)
    equipment = Equipment.query.get(eq_id)

    if request.method == 'POST':
        equipment.eq = request.form['eq']
        equipment.col = request.form['col']
        try:
            db.session.add(equipment)
            db.session.commit()
            return redirect('/inventory')
        except:
            db.session.rollback()
            return 'Error'
    else:
        return render_template("addeq.html", equipment=equipment)


@app.route('/inventory/<int:id>/delete')
def inventory_delete(id):
    article = Article.query.get_or_404(id)
    equipment = Equipment.query.all()
    for el in equipment:
        if el.user_id == article.id:
            try:
                db.session.delete(el)
                db.session.commit()
            except:
                return 'Error'
    try:
        db.session.delete(article)
        db.session.commit()
        return redirect('/inventory')
    except:
        return 'Error'


@app.route('/inventory/<int:id>/<int:eq_id>/deleteeq')
def eq_delete(id, eq_id):
    article = Article.query.get(id)
    equipment = Equipment.query.all()
    for el in equipment:
        if article.id == el.user_id:
            if el.id == eq_id:
                try:
                    db.session.delete(el)
                    db.session.commit()
                    return redirect('/inventory/' + str(id))
                except:
                    return 'Error'
    return redirect('/inventory/' + str(id))


@app.route('/inventory/<int:id>/<int:eq_id>/updateeq', methods=['POST', 'GET'])
def eq_update(id, eq_id):
    article = Article.query.get(id)
    equipment = Equipment.query.all()
    for el in equipment:
        if article.id == el.user_id:
            if el.id == eq_id:
                try:
                    el = Equipment(id=eq_id, eq=el.eq, col=el.col, user_id=article.id)
                    if request.method == 'POST':
                        db.session.add(el)
                        db.session.commit()
                        return redirect('/inventory/' + str(id))
                except:
                    return 'Error'
    return redirect('/inventory/' + str(id))


@app.route('/inventory/<int:id>/<int:eq_id>/show', methods=['POST', 'GET'])
def eq_show(id, eq_id):
    article = Article.query.get(id)
    equipment = Equipment.query.get(eq_id)
    #print(article,equipment)
    if request.method == 'POST':
        eq=request.form[f'eq.{eq_id}']
        col=request.form[f'col.{eq_id}']

        equipment = Equipment(eq=eq, col=col, user_id=id)
        try:
            db.session.add(equipment)
            db.session.commit()
            eq_delete(id,eq_id)
            #return redirect('/inventory/<int:id>/<int:eq_id>/deleteeq')
        except:
            return 'Error'

    return redirect('/inventory/' + str(id))


@app.route('/inventory/<int:id>/update', methods=['POST', 'GET'])
def updateInventory(id):
    article = Article.query.get(id)
    equipment = Equipment.query.get(id)
    print(equipment.user_id)
    if request.method == 'POST':
        article.title = request.form['Title']
        article.intro = request.form['Intro']
        article.text = request.form['Text']
        equipment.eq = request.form['eq']
        equipment.col = request.form['col']
        try:
            db.session.commit()
            return redirect('/inventory')
        except:
            db.session.rollback()
            return 'Error'
    else:

        return render_template("updateInventory.html", article=article, equipment=equipment)


@app.route('/inventory/<int:id>/<int:eq_id>/new/<int:commit_eq>', methods=['POST', 'GET'])
def add_eq(id, eq_id, commit_eq):
    article = Article.query.get(id)
    equipment = Equipment.query.get(eq_id)

    if request.method == 'POST':
        new_eq = Equipment.query.get(commit_eq)
        print(new_eq)
        eq = request.form['eq_id']
        print(new_eq.eq)
        col = request.form['col_id']
        new_eq = Equipment(eq=eq, col=col, user_id=id)
        try:
            db.session.add(new_eq)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'
    else:
        # article = Article.query.get(id)
        equipment = Equipment.query.get(commit_eq)
        eq = request.form['eq']
        try:
            db.session.add(equipment)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'

        return redirect('/inventory/' + str(id))


'''
@app.route('/create-article', methods=['POST', 'GET'])
def createArticle():
    if request.method == 'POST':
        title = request.form['Title']
        intro = request.form['Intro']
        eq = request.form['eq']
        col = request.form['col']
        article = Article(title=title, intro=intro)

        try:
            db.session.add(article)
            db.session.flush()
            equipment = Equipment(eq=eq, col=col, user_id=article.id)
            db.session.add(equipment)
            db.session.commit()
            return redirect('/inventory')
        except:
            return 'Error'
    else:
        return render_template("create-article.html")
'''


@app.route('/create-article', methods=['POST', 'GET'])
def createArticle():
    article = Article.query.all()
    print(article)
    if article != []:
        id = article[-1].id + 1
    else:
        id = 1
    title = ''
    intro = ''
    article = Article(id=id, title=title, intro=intro)
    equipment = Equipment.query.all()
    if equipment != []:
        eq_id = equipment[-1].id + 1
    else:
        eq_id = 1
    equipment = Equipment(id=eq_id)
    if request.method == 'POST':
        try:
            db.session.add(article)
            db.session.commit()
            print(equipment)
            return render_template("create-article.html", article=article, equipment=equipment)
            # return redirect(f'/inventory/{article.id}')
        except:
            return 'Error'
    else:
        return render_template("create-article.html")


@app.route('/inventory/<int:id>/<int:eq_id>/newuser/<int:commit_eq>', methods=['POST', 'GET'])
def add_user_eq(id, eq_id, commit_eq):
    article = Article.query.get(id)
    equipment = Equipment.query.get(eq_id)
    title = request.form['Title']
    #print(title)
    intro = request.form['Intro']

    if request.method == 'POST':
        new_eq = Equipment.query.get(commit_eq)
        eq = request.form['eq_id']
        col = request.form['col_id']

        delarticle =Article.query.get(id)
        print(delarticle)
        #print(newarticle.title, newarticle.id)
        try:
            db.session.delete(delarticle)
            db.session.flush()
            newarticle = Article(title=title, intro=intro)
            db.session.add(newarticle)

            #db.session.flush()
            new_eq = Equipment(eq=eq, col=col, user_id=id)
            db.session.add(new_eq)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'
    else:
        # article = Article.query.get(id)
        equipment = Equipment.query.get(commit_eq)
        eq = request.form['eq']
        try:
            db.session.add(equipment)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'

        return redirect('/inventory/' + str(id))

if __name__ == "__main__":
    app.run(debug=True)

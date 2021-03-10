from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_required, login_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,  BooleanField, PasswordField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
app.secret_key = "#safefsegwe"
login_manager.login_view = "login"


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


class Users(db.Model,UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100),nullable=False)
    def __repr__(self):
        return '<Users %r>' % self.id

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField()


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))



@app.route('/login/', methods=['post', 'get'])
def login():
    password = request.form.get('password')
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(Users).filter(Users.login == form.username.data).first()
        if user and user.password == password:
            login_user(user, remember=form.remember.data)
            return redirect('/')
        else:
            return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/')
@app.route('/home')
@app.route('/inventory')
@login_required
def inventory():

    q = request.args.get('q')
    if q:
        articles = Article.query.filter(Article.title.contains(q)).all()
        print(articles)
    else:
        articles = Article.query.order_by(Article.date.desc()).all()
    return render_template("inventory.html", articles=articles)


@app.route('/inventory/<int:id>')
@login_required
def equip(id):
    article = Article.query.get(id)
    equipment = Equipment.query.all()
    return render_template("eq.html", article=int(article.id), equipment=equipment, name=article)


@app.route('/inventory/<int:id>/delete')
@login_required
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
@login_required
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
@login_required
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
@login_required
def eq_show(id, eq_id):
    if request.method == 'POST':
        eq=request.form[f'eq.{eq_id}']
        col=request.form[f'col.{eq_id}']
        equipment = Equipment(eq=eq, col=col, user_id=id)
        try:
            db.session.add(equipment)
            db.session.commit()
            eq_delete(id,eq_id)
        except:
            return 'Error'
    return redirect('/inventory/' + str(id))


@app.route('/inventory/<int:id>/update', methods=['POST', 'GET'])
@login_required
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
@login_required
def add_eq(id, eq_id, commit_eq):
    if request.method == 'POST':
        new_eq = Equipment.query.get(commit_eq)

        eq = request.form['eq_id']
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
        equipment = Equipment.query.get(commit_eq)
        try:
            db.session.add(equipment)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'


@app.route('/create-article', methods=['POST', 'GET'])
@login_required
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
            return render_template("create-article.html", article=article, equipment=equipment)
        except:
            return 'Error'
    else:
        return render_template("create-article.html")


@app.route('/inventory/<int:id>/<int:eq_id>/newuser/<int:commit_eq>', methods=['POST', 'GET'])
@login_required
def add_user_eq(id, eq_id, commit_eq):
    title = request.form['Title']
    intro = request.form['Intro']
    if request.method == 'POST':
        eq = request.form['eq_id']
        col = request.form['col_id']
        try:
            newarticle = Article(title=title, intro=intro)
            db.session.add(newarticle)
            new_eq = Equipment(eq=eq, col=col, user_id=id)
            db.session.add(new_eq)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'
    else:
        equipment = Equipment.query.get(commit_eq)
        try:
            db.session.add(equipment)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'


if __name__ == "__main__":
    app.run(debug=True)

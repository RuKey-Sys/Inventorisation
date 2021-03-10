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

#Описываем таблицу где будут ФИО,Должность и время создания
class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    intro = db.Column(db.String(300), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Article %r>' % self.id

#Описываем таблицу где будет записано оборудование
class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)    #id
    eq = db.Column(db.String(100), nullable=False)  #Наименование
    col = db.Column(db.Integer, nullable=False)     #Количество
    user_id = db.Column(db.Integer, db.ForeignKey('article.id'))    #Внешний ключ на таблицу с пользователями

    def __repr__(self):
        return '<Equipment %r>' % self.id

#Описываем таблицу, в которой будут пользователи, которым разрешено посещение сайта
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



@app.route('/login/', methods=['post', 'get'])      #Обработчик ссылки /login
def login():
    password = request.form.get('password')         #в password записываем написанное в поле password на странице
    form = LoginForm()
    if form.validate_on_submit():                   #Если нажали submit
        user = db.session.query(Users).filter(Users.login == form.username.data).first()    #Из таблицы Users берем первого пользователя и проверяем с написанным
        if user and user.password == password:          #Проверяем написанный на сайте пароль, и пароль из таблицы
            login_user(user, remember=form.remember.data) #пропускаем если все сошлось
            return redirect('/')
        else:
            return redirect(url_for('login'))
    return render_template('login.html', form=form)     #При Переходе на /login генерируем страницу login.html


@app.route('/')
@app.route('/home')
@app.route('/inventory')        #Обработчик ссылок /, /home, /inventory
@login_required
def inventory():

    q = request.args.get('q')       #Аргументы из поля поиска записываем переменную q
    if q:
        articles = Article.query.filter(Article.title.contains(q)).all()    # В переменную article записываем записи, где в поле title содержится q
    else:
        articles = Article.query.order_by(Article.title).all()      #Иначе показываем всех
    return render_template("inventory.html", articles=articles)     #При Переходе на ссылки /,/home/inventory генерируем страницу inventory.html


@app.route('/inventory/<int:id>')       #Обработчик ссылки /inventory/{id пользователя} "ака Детальная страница пользователя"
@login_required
def equip(id):
    article = Article.query.get(id)     #В article записываем id title и intro пользователя
    equipment = Equipment.query.all()   #В equipment записываем всю таблицу с оборудованием
    return render_template("eq.html", article=int(article.id), equipment=equipment, name=article)   #Генерируем страницу eq.html, куда передаем необходимые переменные


@app.route('/inventory/<int:id>/delete')    #Удаление пользователя. id-номер пользователя
@login_required
def inventory_delete(id):
    article = Article.query.get_or_404(id)  #Берем пользователя
    equipment = Equipment.query.all()
    for el in equipment:
        if el.user_id == article.id:        #Если оборудование принадлежит пользователю, то удаляем оборудование из таблицы Equipment
            try:
                db.session.delete(el)
                db.session.commit()
            except:
                return 'Error'
    try:
        db.session.delete(article)          #Удаляем пользователя из таблицы Article
        db.session.commit()
        return redirect('/inventory')       #Переходим на страницу со всеми пользователями
    except:
        return 'Error'


@app.route('/inventory/<int:id>/<int:eq_id>/deleteeq')      #Удаление отдельного оборудования у пользователя. id-номер пользователя, eq_id- номер оборудования
@login_required
def eq_delete(id, eq_id):
    article = Article.query.get(id)                         #Берем пользователя
    equipment = Equipment.query.all()                       #Берем все оборудование
    for el in equipment:
        if article.id == el.user_id:                        #Если оборудование принадлежит пользователю, то удаляем оборудование из таблицы Equipment
            if el.id == eq_id:
                try:
                    db.session.delete(el)
                    db.session.commit()
                    return redirect('/inventory/' + str(id))#Перенапрявляем на детальную страницу пользователя
                except:
                    return 'Error'
    return redirect('/inventory/' + str(id))

#неиспользуемая функция, можно удалить
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

#Редактировать оборудование
@app.route('/inventory/<int:id>/<int:eq_id>/show', methods=['POST', 'GET'])
@login_required
def eq_show(id, eq_id):
    if request.method == 'POST':
        eq=request.form[f'eq.{eq_id}']          #Считываем наименование
        col=request.form[f'col.{eq_id}']        #Считываем количество
        equipment = Equipment(eq=eq, col=col, user_id=id)       #Записываем что equipment=записи в таблице Equipment с названием eq и количеством col; номер = id
        try:
            db.session.add(equipment)       #Добавляем строку в таблицу Equipment
            db.session.commit()
            eq_delete(id,eq_id)             #Функция удаления(Удаляем предыдущее значение)
        except:
            return 'Error'
    return redirect('/inventory/' + str(id))

#Неиспользуемая функция
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

#Добавление нового оборудования commit_eq-номер последнего оборудования
@app.route('/inventory/<int:id>/<int:eq_id>/new/<int:commit_eq>', methods=['POST', 'GET'])
@login_required
def add_eq(id, eq_id, commit_eq):
    if request.method == 'POST':
        new_eq = Equipment.query.get(commit_eq)     #Берем последнюю запись

        eq = request.form['eq_id']                  #Наименование
        col = request.form['col_id']                #Количество
        new_eq = Equipment(eq=eq, col=col, user_id=id)  #Представляем как строка в таблице с необходимыми записями
        try:
            db.session.add(new_eq)                  #Добавляем строку
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()                   #В случае ошибки откатываем изменения
            return 'Error'
    else:                                           #До сюда не доходит
        equipment = Equipment.query.get(commit_eq)
        try:
            db.session.add(equipment)
            db.session.commit()
            return redirect(f'/inventory/{id}')
        except:
            db.session.rollback()
            return 'Error'

#Создание пользователя
@app.route('/create-article', methods=['POST', 'GET'])
@login_required
def createArticle():
    article = Article.query.all()       #Берем всех пользователей
    if article != []:                   #Если список не пустой
        id = article[-1].id + 1         #id - номер последнего +1
    else:                               #Иначе id - 1
        id = 1
    title = ''
    intro = ''
    article = Article(id=id, title=title, intro=intro)  #Представляем что article пустая строка в таблице Article
    equipment = Equipment.query.all()   #Берем всё оборудование
    if equipment != []:                 #Если список не пустой
        eq_id = equipment[-1].id + 1    #eq_id - номер последнего оборудования +1
    else:                               #Иначе eq_id - 1
        eq_id = 1
    equipment = Equipment(id=eq_id)     #Представляем что equipment пустая строка в таблице Equipment, eq_id - номер последнего оборудования
    if request.method == 'POST':
        return render_template("create-article.html", article=article, equipment=equipment)
    '''
        Генерируем страницу create-article.html, передаем пустую строку с id последнего+1 и eq_id - номер последнего оборудования +1'''

#Добавление оборудования у нового пользователя
@app.route('/inventory/<int:id>/<int:eq_id>/newuser/<int:commit_eq>', methods=['POST', 'GET'])
@login_required
def add_user_eq(id, eq_id, commit_eq):
    title = request.form['Title']       #ФИО пользователя
    intro = request.form['Intro']       #Должность
    if request.method == 'POST':
        eq = request.form['eq_id']      #наименование оборудования
        col = request.form['col_id']    #Количество
        try:
            newarticle = Article(title=title, intro=intro)  #Записываем нового пользователя в таблицу Article
            db.session.add(newarticle)
            new_eq = Equipment(eq=eq, col=col, user_id=id)  #Записываем оборудование для данного пользователя
            db.session.add(new_eq)
            db.session.commit()
            return redirect(f'/inventory/{id}')             #переходим на страницу данного пользователя
        except:
            db.session.rollback()
            return 'Error'
    else:                              #до сюда не доходит
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

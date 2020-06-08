from flask import Flask, render_template, flash, session, request, redirect
from flask_bootstrap import Bootstrap
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_ckeditor import CKEditor
from flask_wtf import FlaskForm
import yaml
import os


app = Flask(__name__)
Bootstrap(app)
ckeditor = CKEditor(app)

# configure DB
db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

app.config['SECRET_KEY'] = os.urandom(24)

@app.errorhandler(404)
def page_not_found(e):
    return 'This is not the page you are looking for. Please retry search.'

@app.errorhandler(KeyError)
def key_error(e):
    flash('Please login and try again.', 'warning')
    return redirect ('/login')

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    resultValue = cur.execute(" SELECT * FROM blog")
    if resultValue > 0:
        blogs = cur.fetchall()
        cur.close()
        return render_template('index.html', blogs=blogs)
    cur.close()
    return render_template('index.html', blogs=None)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blogs/<int:id>/')
def blogs(id):
    cur = mysql.connection.cursor()
    resultValue = cur.execute("SELECT * FROM blog WHERE blog_id ={}".format(id))
    if resultValue > 0:
        blog = cur.fetchone()
        return render_template('blogs.html', blog=blog)
    return ' Blog not found'


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userDetails = request.form
        if userDetails['password'] != userDetails['confirm_password']:
            flash('Passwords do not match! Try again.', 'danger')
            return render_template('register.html')
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user(first_name, last_name, username, email, password)"\
        "VALUES(%s,%s,%s,%s,%s)", (userDetails['first_name'], userDetails['last_name'], \
        userDetails['username'], userDetails['email'], generate_password_hash(userDetails['password'])))
        mysql.connection.commit()
        cur.close()
        flash('Registration Sucessful! Please Login.', 'success')
        return redirect('/login')
    return render_template('register.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userDetails = request.form
        username = userDetails['username']
        cur = mysql.connection.cursor()
        resultValue = cur.execute("SELECT * FROM user WHERE username = %s", ([username]))
        if resultValue > 0:
            user = cur.fetchone()
            if check_password_hash(user['password'], userDetails['password']):
                session['login'] = True
                session['firstName'] = user['first_name']
                session['lastName'] = user['last_name']
                flash('Welcome ' + session['firstName'] +'! You have been logged in', 'success')
            else:
                cur.close()
                flash('Password does not match', 'danger')
                return render_template('login.html')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/')
    return render_template('login.html')

@app.route('/write-blog', methods=['GET', 'POST'])
def write_blog():
    if request.method == 'POST':
        blogpost = request.form
        title = blogpost['title']
        body = blogpost['body']
        author = session['firstName'] + ' ' +session['lastName']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO blog(title, body, author) VALUES(%s, %s, %s)", (title, body, author))
        mysql.connection.commit()
        cur.close()
        flash("Sucessfully posted new blog", 'alert-success')
        return redirect('/')
    return render_template('write-blog.html')

@app.route('/my-blogs')
def my_blogs():
    author = session['firstName'] + ' ' + session['lastName']
    cur = mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blog WHERE author = %s", [author])
    if result_value > 0:
        my_blogs = cur.fetchall()
        return render_template('my-blogs.html', my_blogs=my_blogs)
    else:
        return render_template('my-blogs.html', my_blogs=None)


@app.route('/edit-blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        title = request.form['title']
        body = request.form['body']
        cur.execute("UPDATE blog SET title = %s, body = %s where blog_id = %s", (title,body, id))
        mysql.connection.commit()
        cur.close()
        flash('Blog updated successfully', 'success')
        return redirect('/blogs/{}'.format(id))
    cur=mysql.connection.cursor()
    result_value = cur.execute("SELECT * FROM blog WHERE blog_id = {}".format(id))
    if result_value > 0:
        blog = cur.fetchone()
        blog_form = {}
        blog_form['title'] = blog['title']
        blog_form['body'] = blog['body']
        return render_template('edit-blog.html', blog_form=blog_form)

@app.route('/delete-blog/<int:id>/')
def delete_blog(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM blog WHERE blog_id = {}".format(id))
    mysql.connection.commit()
    flash(" Your blog has been deleted", 'success')
    return redirect('/my-blogs')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", 'info')
    return redirect('/')



if __name__ == '__main__':
        app.run(debug=True)

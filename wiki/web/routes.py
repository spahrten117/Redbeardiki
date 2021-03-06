"""
    Routes
    ~~~~~~
"""
from flask import Blueprint
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user

from wiki.core import Processor, clean_url
from wiki.web.forms import EditorForm, CombineForm, UploadForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web.forms import ExportForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect
import os


bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/export/<path:url>/', methods=['GET', 'POST'])
@protect
def export(url):
    page = current_wiki.get_or_404(url)
    form = ExportForm()
    if form.is_submitted():
        file = open('wiki/web/templates/test.html', 'w')
        file.truncate(0)
        file.close()
        file = open('wiki/web/templates/test.html', 'a')
        file.write(page.html)
        file.close()
        os.system("pandoc -s -o " + form.fileName.data + ".pdf" + " C:\\Users\\tope0_000\\Desktop\\Redbeardiki\\wiki\\web\\templates\\test.html")
        return display('home')
    else:
        return render_template('Export.html', form = form, page = page)


@bp.route('/combine/', methods=['GET', 'POST'])
@protect
def combine():
    pages = current_wiki.index()
    os.system("pandoc -s -o testdoc.pdf \"C:\\Users\\tope0_000\\Desktop\\CSC 440\\Homework 1\\CSC440-540-HW1-ver3.md\"")
    form = CombineForm()
    url = form.url._value()
    if form.is_submitted():
        if form.title.validate(form) and form.url.validate(form):
            newUrl = form.clean_url(form.url.data)
            array = request.form.getlist('url')
            file = open('wiki/web/templates/test.html', 'w')
            file.truncate(0)
            file.close()
            for item in array:
                if item != url:
                    page = current_wiki.get(item)
                    file = open('wiki/web/templates/test.html', 'a')
                    file.write(page.html)
            file.close()
            page = current_wiki.get(newUrl)
            form = CombineForm(obj=page)
            if not page:
                page = current_wiki.get_bare(newUrl)
            form.populate_obj(page)
            file = open('wiki/web/templates/test.html', 'r')
            page.body = file.read()
            file.close()
            page.save()
            flash('"%s" was saved.' % page.title, 'success')
            return redirect(url_for('wiki.display', url=newUrl))
        else:
            return render_template('combine.html', form=form, pages=pages)
    else:
        return render_template('combine.html', form=form, pages=pages)


@bp.route('/upload/', methods=['GET', 'POST'])
@protect
def upload():
    pages = current_wiki.index()
    form = UploadForm()
    if form.is_submitted():
        if form.title.validate(form) and form.url.validate(form):
            url = form.clean_url(form.url.data)
            page = current_wiki.get(url)
            form = UploadForm(obj=page)
            if not page:
                page = current_wiki.get_bare(url)
            form.populate_obj(page)
            page.body = form.fileInput.data
            page.save()
            flash('"%s" was saved.' % page.title, 'success')
            return redirect(url_for('wiki.display', url=url))
        else:
            return render_template('upload.html', form=form, pages=pages)
    else:
        return render_template('upload.html', form=form, pages=pages)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


@bp.route('/user/')
def user_index():
    pass


@bp.route('/user/create/')
def user_create():
    pass


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/delete/<int:user_id>/')
def user_delete(user_id):
    pass


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


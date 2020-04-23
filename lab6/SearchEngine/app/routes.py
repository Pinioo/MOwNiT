from app import app
from src import s_engine 
from flask import request, render_template, redirect
from app.forms.forms import QueryForm

engine = s_engine.SearchEngine()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def search():
    form = QueryForm()
    if form.validate_on_submit():
        return render_template(
            'result_form.html', 
            title='Search', 
            form = form, 
            results_svd=engine.find_n_articles(form.query.data.split(" "), form.results.data, s_engine.SVD),
            results_normed=engine.find_n_articles(form.query.data.split(" "), form.results.data, s_engine.NORMED),
            results_noidf=engine.find_n_articles(form.query.data.split(" "), form.results.data, s_engine.NOIDF)
        )
    else:
        return render_template(
            'search_form.html', 
            title='Search', 
            form = form
        )

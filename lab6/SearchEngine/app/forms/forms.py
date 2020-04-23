from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired

class QueryForm(FlaskForm):
    query = StringField('Query', validators=[DataRequired()])
    results = IntegerField('Results', validators=[DataRequired()], default=5)
    submit = SubmitField('Search')
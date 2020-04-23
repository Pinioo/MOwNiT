from flask import Flask
from src import s_engine
from datetime import timedelta
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
start_time = time.time()
s_engine.SearchEngine(True)
end_time = time.time()
print(f"Search engine preprocessing done in {timedelta(seconds=(end_time - start_time))}")

from app import routes

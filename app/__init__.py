"""
A Flask layer to haystack interface.
"""
import os

from flask import Flask, send_from_directory

from app.blueprint_haystack import haystack as haystack_blueprint

app = Flask(__name__)
app.register_blueprint(haystack_blueprint)


@app.route('/')
def index():
    return "Flask is up and running"

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

def main():
    debug = ("1" == os.environ.get("FLASK_DEBUG", "0"))
    app.run(host='0.0.0.0' if not debug else 'localhost',
            port=5000,
            debug=debug)

if __name__ == '__main__':
    main()
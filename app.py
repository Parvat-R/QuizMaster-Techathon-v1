from flask import Flask, render_template
from flask_cors import CORS
import routes

app = Flask(__name__)
app.secret_key = "secret key"

@app.route("/")
def index():
    return render_template('index.html')

app.register_blueprint(routes.teacher.bp)
app.register_blueprint(routes.student.bp)

if __name__ == "__main__":
    app.run(debug=True)
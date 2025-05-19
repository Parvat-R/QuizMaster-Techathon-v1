from flask import Flask, render_template, session, redirect, url_for
from flask_cors import CORS
import routes

app = Flask(__name__)
app.secret_key = "secret key"

@app.route("/")
def index():
    if 'user_type' in session:
        return redirect(url_for(f"{session['user_type']}.index"))
    return render_template('index.html')

app.register_blueprint(routes.teacher.bp)
app.register_blueprint(routes.student.bp)

if __name__ == "__main__":
    app.run(debug=True)
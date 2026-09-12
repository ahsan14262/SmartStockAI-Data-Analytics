from flask import Flask, render_template
from routes.data_routes import data_bp
from routes.sales_routes import sales_bp

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024
app.register_blueprint(data_bp)
app.register_blueprint(sales_bp)

@app.get('/')
def home(): return render_template('data.html')
@app.get('/data')
def data_page(): return render_template('data.html')
@app.get('/sales')
def sales_page(): return render_template('sales.html')

if __name__ == '__main__': app.run(debug=True)

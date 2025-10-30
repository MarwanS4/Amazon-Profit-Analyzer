from flask import Flask, render_template, jsonify
import csv
import os

app = Flask(__name__)

UPLOADS_FOLDER = 'uploads'
CSV_FILE = 'eurolots_test.csv'

def load_products():
    path = os.path.join(UPLOADS_FOLDER, CSV_FILE)
    products = []

    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            products.append(row)
    return products

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_products')
def get_products():
    products = load_products()
    return jsonify(products)

if __name__ == '__main__':
    app.run(debug=True)

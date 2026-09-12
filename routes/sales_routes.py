import os
from flask import Blueprint, jsonify
from backend import sales_service

sales_bp = Blueprint('sales', __name__)
DATA = 'data/processed/sales_cleaned.csv'

def ready(): return os.path.exists(DATA)

@sales_bp.get('/api/sales/summary')
def summary(): return jsonify(sales_service.summary(DATA)) if ready() else (jsonify({'error':'Process a dataset first.'}),404)

@sales_bp.get('/api/sales/daily')
def daily(): return jsonify(sales_service.daily(DATA)) if ready() else (jsonify({'error':'Process a dataset first.'}),404)

@sales_bp.get('/api/sales/products')
def products(): return jsonify(sales_service.products(DATA)) if ready() else (jsonify({'error':'Process a dataset first.'}),404)

@sales_bp.get('/api/sales/categories')
def categories(): return jsonify(sales_service.categories(DATA)) if ready() else (jsonify({'error':'Process a dataset first.'}),404)

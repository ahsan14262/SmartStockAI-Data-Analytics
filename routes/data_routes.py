import os
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from backend.data_processor import load_and_validate, dataset_summary, clean_dataset, save_processed

data_bp = Blueprint('data', __name__)
RAW = 'data/raw'
PROCESSED = 'data/processed/sales_cleaned.csv'

@data_bp.post('/api/data/upload')
def upload():
    f = request.files.get('file')
    if not f or not f.filename.lower().endswith('.csv'):
        return jsonify({'error':'Please upload a CSV file.'}), 400
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, secure_filename(f.filename))
    f.save(path)
    try:
        df = load_and_validate(path)
        return jsonify({'message':'File uploaded and validated.', 'filename':os.path.basename(path), 'summary':dataset_summary(df)})
    except Exception as e:
        return jsonify({'error':str(e)}), 400

@data_bp.get('/api/data/summary')
def summary():
    if not os.path.exists(PROCESSED): return jsonify({'error':'No processed dataset found.'}), 404
    df = load_and_validate(PROCESSED)
    return jsonify(dataset_summary(df))

@data_bp.get('/api/data/preview')
def preview():
    if not os.path.exists(PROCESSED): return jsonify({'error':'No processed dataset found.'}), 404
    df = load_and_validate(PROCESSED).head(20).fillna('')
    return jsonify(df.to_dict('records'))

@data_bp.post('/api/data/clean')
def clean():
    filename = (request.get_json(silent=True) or {}).get('filename')
    if not filename: return jsonify({'error':'filename is required.'}), 400
    path = os.path.join(RAW, secure_filename(filename))
    if not os.path.exists(path): return jsonify({'error':'Uploaded file not found.'}), 404
    try:
        df = clean_dataset(load_and_validate(path))
        save_processed(df, PROCESSED)
        return jsonify({'message':'Dataset cleaned successfully.', 'summary':dataset_summary(df)})
    except Exception as e:
        return jsonify({'error':str(e)}), 400

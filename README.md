# SmartStock AI — Member 2 Module

**Owner:** Ahsan — Data Engineering + Data Management + Sales Analytics

## Features
- CSV upload and schema validation
- Missing/duplicate/invalid-data cleaning
- Standard processed dataset for the Chronos-2 forecasting module
- Dataset summary and preview
- Historical sales KPIs
- Daily revenue, top-products and category charts
- Flask JSON APIs for team integration

## Required CSV columns
`date, product, quantity, price`

Optional: `product_id, category, promotion, holiday`.

## Run
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000/data`.

Try `data/sample_sales.csv` first.

## API contract
- `POST /api/data/upload` — multipart field `file`
- `POST /api/data/clean` — JSON `{ "filename": "..." }`
- `GET /api/data/summary`
- `GET /api/data/preview`
- `GET /api/sales/summary`
- `GET /api/sales/daily`
- `GET /api/sales/products`
- `GET /api/sales/categories`

The canonical cleaned output is `data/processed/sales_cleaned.csv`. Member 3 can consume this as the input to Chronos-2.

## Streamlit test UI

For a quick Member 2 demo/test without the Flask frontend:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open the local URL shown by Streamlit. Use **Data Management** to upload and clean a CSV, then open **Sales Analytics** from the sidebar.

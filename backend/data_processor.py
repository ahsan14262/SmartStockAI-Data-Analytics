import os
import pandas as pd

REQUIRED = ['date','product','quantity','price']
OPTIONAL_DEFAULTS = {'product_id':'','category':'Uncategorized','promotion':0,'holiday':0}


def load_and_validate(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(missing))
    for c, default in OPTIONAL_DEFAULTS.items():
        if c not in df.columns:
            df[c] = default
    return df


def dataset_summary(df):
    dates = pd.to_datetime(df['date'], errors='coerce')
    return {
        'rows': int(len(df)),
        'products': int(df['product'].nunique()),
        'categories': int(df['category'].nunique()),
        'date_from': dates.min().strftime('%Y-%m-%d') if dates.notna().any() else None,
        'date_to': dates.max().strftime('%Y-%m-%d') if dates.notna().any() else None,
        'missing_values': int(df.isna().sum().sum()),
        'duplicates': int(df.duplicated().sum())
    }


def clean_dataset(df):
    df = df.copy().drop_duplicates()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['promotion'] = pd.to_numeric(df['promotion'], errors='coerce').fillna(0)
    df['holiday'] = pd.to_numeric(df['holiday'], errors='coerce').fillna(0)
    df['product'] = df['product'].astype(str).str.strip()
    df['category'] = df['category'].fillna('Uncategorized').astype(str).str.strip()
    df = df.dropna(subset=['date','quantity','price'])
    df = df[(df['quantity'] >= 0) & (df['price'] >= 0) & (df['product'] != '')]
    df['revenue'] = df['quantity'] * df['price']
    df = df.sort_values(['date','product']).reset_index(drop=True)
    return df


def save_processed(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = df.copy()
    out['date'] = out['date'].dt.strftime('%Y-%m-%d')
    out.to_csv(path, index=False)

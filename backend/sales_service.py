import pandas as pd


def _load(path):
    df = pd.read_csv(path, parse_dates=['date'])
    if 'revenue' not in df.columns:
        df['revenue'] = df['quantity'] * df['price']
    return df


def summary(path):
    df = _load(path)
    by_product = df.groupby('product')['quantity'].sum().sort_values(ascending=False)
    return {
        'total_revenue': round(float(df['revenue'].sum()), 2),
        'units_sold': round(float(df['quantity'].sum()), 2),
        'products': int(df['product'].nunique()),
        'categories': int(df['category'].nunique()) if 'category' in df else 0,
        'average_daily_revenue': round(float(df.groupby(df['date'].dt.date)['revenue'].sum().mean()), 2),
        'best_selling_product': by_product.index[0] if len(by_product) else None,
        'worst_selling_product': by_product.index[-1] if len(by_product) else None
    }


def daily(path):
    df = _load(path)
    x = df.groupby(df['date'].dt.date).agg(revenue=('revenue','sum'), quantity=('quantity','sum')).reset_index()
    return [{'date': str(r['date']), 'revenue': round(float(r['revenue']),2), 'quantity': float(r['quantity'])} for _,r in x.iterrows()]


def products(path, limit=10):
    df = _load(path)
    x = df.groupby('product').agg(quantity=('quantity','sum'), revenue=('revenue','sum')).sort_values('quantity',ascending=False).head(limit).reset_index()
    return x.round(2).to_dict('records')


def categories(path):
    df = _load(path)
    x = df.groupby('category').agg(quantity=('quantity','sum'), revenue=('revenue','sum')).sort_values('revenue',ascending=False).reset_index()
    return x.round(2).to_dict('records')

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from backend.data_processor import load_and_validate, dataset_summary, clean_dataset
from backend.market_analyzer import analyze_product

st.set_page_config(page_title="SmartStock AI - Member 2", page_icon="🛒", layout="wide")

st.title("🛒 SmartStock AI")
st.caption("Member 2 — Data Engineering, Data Management & Sales Analytics")

if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "clean_df" not in st.session_state:
    st.session_state.clean_df = None

page = st.sidebar.radio("Navigation", ["📁 Data Management", "📊 Sales Analytics", "🌐 Market Analyzer"])


def money(value):
    return f"Rs. {value:,.2f}"


def show_summary(df, title="Dataset Summary"):
    s = dataset_summary(df)
    st.subheader(title)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{s['rows']:,}")
    c2.metric("Products", f"{s['products']:,}")
    c3.metric("Categories", f"{s['categories']:,}")
    c4.metric("Missing Values", f"{s['missing_values']:,}")
    c5, c6, c7 = st.columns(3)
    c5.metric("Duplicates", f"{s['duplicates']:,}")
    c6.metric("From", s['date_from'] or "N/A")
    c7.metric("To", s['date_to'] or "N/A")


if page == "📁 Data Management":
    st.header("📁 Data Management")
    st.write("Upload historical grocery sales, validate the schema, clean the data, and prepare a forecast-ready dataset for Chronos-2.")

    uploaded = st.file_uploader("Upload sales CSV", type=["csv"])
    if uploaded is not None:
        try:
            # load_and_validate expects a path, so save the uploaded bytes temporarily.
            tmp = Path("data/raw/streamlit_upload.csv")
            tmp.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(uploaded.getvalue())
            st.session_state.raw_df = load_and_validate(str(tmp))
            st.success("CSV uploaded and required columns validated.")
        except Exception as exc:
            st.session_state.raw_df = None
            st.error(str(exc))

    df = st.session_state.raw_df
    if df is not None:
        show_summary(df)

        st.subheader("Data Quality")
        required = ["date", "product", "quantity", "price"]
        for col in required:
            st.write(f"✅ `{col}` column found" if col in df.columns else f"❌ `{col}` column missing")
        duplicates = int(df.duplicated().sum())
        missing = int(df.isna().sum().sum())
        st.write(f"{'⚠️' if missing else '✅'} Missing values: **{missing:,}**")
        st.write(f"{'⚠️' if duplicates else '✅'} Duplicate rows: **{duplicates:,}**")

        st.subheader("Raw Data Preview")
        st.dataframe(df.head(100), use_container_width=True)

        if st.button("🧹 Clean Dataset", type="primary"):
            cleaned = clean_dataset(df)
            st.session_state.clean_df = cleaned
            Path("data/processed").mkdir(parents=True, exist_ok=True)
            save_df = cleaned.copy()
            save_df["date"] = save_df["date"].dt.strftime("%Y-%m-%d")
            save_df.to_csv("data/processed/sales_cleaned.csv", index=False)
            removed = len(df) - len(cleaned)
            st.success(f"Dataset cleaned successfully. {removed:,} invalid/duplicate row(s) removed.")

    clean_df = st.session_state.clean_df
    if clean_df is not None:
        show_summary(clean_df, "Cleaned Dataset Summary")
        st.subheader("Cleaned Data Preview")
        st.dataframe(clean_df.head(100), use_container_width=True)
        csv_bytes = clean_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Cleaned CSV",
            data=csv_bytes,
            file_name="sales_cleaned.csv",
            mime="text/csv",
        )
        st.info("This cleaned dataset is the handoff to the Chronos-2 forecasting module.")

elif page == "📊 Sales Analytics":
    st.header("📊 Sales Analytics")
    df = st.session_state.clean_df

    if df is None:
        processed = Path("data/processed/sales_cleaned.csv")
        if processed.exists():
            df = pd.read_csv(processed, parse_dates=["date"])

    if df is None or df.empty:
        st.warning("No cleaned dataset is available. Go to Data Management, upload a CSV, and click Clean Dataset first.")
    else:
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["date"]):
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if "revenue" not in df.columns:
            df["revenue"] = df["quantity"] * df["price"]

        product_sales = df.groupby("product", as_index=False).agg(
            quantity=("quantity", "sum"), revenue=("revenue", "sum")
        ).sort_values("quantity", ascending=False)
        daily = df.groupby("date", as_index=False).agg(
            revenue=("revenue", "sum"), quantity=("quantity", "sum")
        ).sort_values("date")
        category = df.groupby("category", as_index=False).agg(
            revenue=("revenue", "sum"), quantity=("quantity", "sum")
        ).sort_values("revenue", ascending=False)

        total_revenue = float(df["revenue"].sum())
        units = float(df["quantity"].sum())
        products = int(df["product"].nunique())
        avg_daily = float(daily["revenue"].mean()) if len(daily) else 0
        best = product_sales.iloc[0]["product"] if len(product_sales) else "N/A"

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Revenue", money(total_revenue))
        c2.metric("Units Sold", f"{units:,.0f}")
        c3.metric("Products", products)
        c4.metric("Avg Daily Revenue", money(avg_daily))
        c5.metric("Best Seller", best)

        st.subheader("Daily Revenue Trend")
        st.line_chart(daily.set_index("date")["revenue"], use_container_width=True)

        left, right = st.columns(2)
        with left:
            st.subheader("Top 10 Products by Units Sold")
            top10 = product_sales.head(10).set_index("product")["quantity"]
            st.bar_chart(top10, use_container_width=True)
        with right:
            st.subheader("Category Revenue")
            st.bar_chart(category.set_index("category")["revenue"], use_container_width=True)

        st.subheader("Product Performance")
        display = product_sales.copy()
        display["revenue"] = display["revenue"].round(2)
        display["quantity"] = display["quantity"].round(2)
        st.dataframe(display, use_container_width=True)

        st.caption("These are historical analytics. Predicted best sellers belong to the Product Intelligence module and should use Chronos-2 forecast output.")


else:
    st.header("🌐 Market Analyzer")
    st.write(
        "Research current web trend signals with DuckDuckGo, compare a product with "
        "the SmartStock catalog, and surface stocking opportunities."
    )
    st.info(
        "Trend Score measures web evidence/popularity signals. It is not verified sales volume. "
        "Historical quantity is sales quantity, not current inventory."
    )

    left, right = st.columns([2, 1])
    with left:
        market_product = st.text_input(
            "Product to analyze",
            placeholder="e.g. Greek Yogurt, Protein Bars, Almond Milk",
        )
    with right:
        market_type = st.selectbox("Market", ["grocery", "food retail", "supermarket"])

    if st.button("🔎 Analyze Market", type="primary", disabled=not market_product.strip()):
        with st.spinner("Searching current market signals..."):
            try:
                report = analyze_product(market_product.strip(), market_type)
                st.session_state.market_report = report
            except Exception as exc:
                st.session_state.market_report = None
                st.error(f"Market search failed: {exc}")

    report = st.session_state.get("market_report")
    if report:
        catalog = report["catalog"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Web Trend Score", f'{report["trend_score"]}/100')
        c2.metric("In Catalog", "Yes" if catalog["exists"] else "No")
        c3.metric("Historical Units Sold", f'{catalog["units_sold"]:,.0f}' if catalog["exists"] else "N/A")

        action = report["action"]
        if action == "NEW STOCK OPPORTUNITY":
            st.success(f"🟢 {action}")
        elif action in {"REVIEW DEMAND / RESTOCK", "RESEARCH FURTHER"}:
            st.warning(f"🟡 {action}")
        else:
            st.info(f"🔵 {action}")
        st.write(report["reason"])

        if catalog["exists"]:
            st.caption(
                f'Matched catalog product: {catalog["matched_product"]} · '
                f'Historical revenue: {money(catalog["revenue"])}'
            )

        st.subheader("Web Evidence")
        if not report["results"]:
            st.warning("No web results were returned for this search.")
        for i, item in enumerate(report["results"], 1):
            title = item["title"] or f"Source {i}"
            if item["url"]:
                st.markdown(f'**{i}. [{title}]({item["url"]})**')
            else:
                st.markdown(f"**{i}. {title}**")
            if item["snippet"]:
                st.write(item["snippet"])

        st.caption(f'Search query: {report["query"]}')

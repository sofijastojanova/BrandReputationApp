import streamlit as st
import pandas as pd
from transformers import pipeline

@st.cache_data
def load_data():
    products = pd.read_csv("data/products.csv")
    testimonials = pd.read_csv("data/testimonials.csv")
    reviews = pd.read_csv("data/reviews.csv")
    if not reviews.empty and 'date' in reviews.columns:
        reviews['date'] = pd.to_datetime(reviews['date'], errors='coerce')
    return products, testimonials, reviews

products_df, testimonials_df, reviews_df = load_data()

@st.cache_resource
def load_sentiment_model():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

sentiment_model = load_sentiment_model()

st.set_page_config(page_title="Brand Reputation Monitor", layout="wide")
st.title("Brand Reputation Monitor – 2023")

st.sidebar.title("Navigation")
section = st.sidebar.radio("Go to", ["Products", "Testimonials", "Reviews"])

if section == "Products":
    st.header("Products")
    st.dataframe(products_df)

elif section == "Testimonials":
    st.header("Testimonials")
    st.dataframe(testimonials_df)

else:
    st.header("Reviews – Sentiment Analysis")
    
    if reviews_df.empty:
        st.error("No reviews.csv - run: python scrape_data.py")
        st.stop()
    
    # CLEAN DATA
    reviews_clean = reviews_df.dropna(subset=['date']).copy()
    reviews_2023 = reviews_clean[reviews_clean['date'].dt.year == 2023].copy()
    
    st.info(f"📊 Loaded {len(reviews_2023)} reviews from 2023")
    
    if len(reviews_2023) == 0:
        st.warning("No 2023 reviews found.")
        st.stop()
    
    # STRING MONTHS - NO RANGEERROR
    reviews_2023['month_str'] = reviews_2023['date'].dt.strftime('%Y-%m')
    months = sorted(reviews_2023['month_str'].unique())
    
    # DEBUG - shows on page
    st.caption(f"Available months: {months}")
    
    # SAFE SLIDER - only if months exist
    if len(months) > 0:
        selected_month = st.select_slider(
            "Select 2023 month:", 
            options=months,
            value=months[0]  # Default first month
        )
        
        month_reviews = reviews_2023[reviews_2023['month_str'] == selected_month].copy()
        
        st.subheader(f"Reviews: {selected_month}")
        st.success(f"Found {len(month_reviews)} reviews ✓")
        
        # SENTIMENT ANALYSIS
        texts = month_reviews['text'].fillna('').tolist()
        if len(texts) > 0:
            results = sentiment_model(texts)
            month_reviews['sentiment'] = [r['label'] for r in results]
            month_reviews['confidence'] = [r['score'] for r in results]
            
            # TABLE
            st.dataframe(month_reviews[['date', 'text', 'sentiment', 'confidence']].head(10))
            
            # CHARTS
            counts = month_reviews['sentiment'].value_counts()
            avg_conf = month_reviews.groupby('sentiment')['confidence'].mean()
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Sentiment Distribution")
                st.bar_chart(counts)
            
            with col2:
                st.subheader("🎯 Confidence Scores")
                st.dataframe(avg_conf.round(3), use_container_width=True)
        else:
            st.info("No reviews for this month.")
    else:
        st.error("No valid months detected.")

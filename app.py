import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

@st.cache_data
def load_data():
    products = pd.read_csv("data/products.csv")
    testimonials = pd.read_csv("data/testimonials.csv")
    reviews = pd.read_csv("data/reviews.csv", encoding='latin1')
    return products, testimonials, reviews

products_df, testimonials_df, reviews_df = load_data()

def get_sentiment(text):
    if pd.isna(text) or str(text).strip() == "":
        return 'NEUTRAL'
    score = analyzer.polarity_scores(str(text))
    compound = score['compound']
    if compound >= 0.05:
        return 'POSITIVE'
    elif compound <= -0.05:
        return 'NEGATIVE'
    return 'NEUTRAL'

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
    st.header("Reviews – VADER Sentiment Analysis")
    
    # USE LIVE VADER - NO FILE DEPENDENCY
    reviews_2023 = reviews_df[pd.to_datetime(reviews_df['date'], errors='coerce').dt.year == 2023].copy()
    reviews_2023['sentiment'] = reviews_2023['text'].apply(get_sentiment)
    
    st.success(f"✅ Loaded {len(reviews_2023)} reviews with VADER sentiment!")
    st.info(f"📊 2023 reviews: {len(reviews_2023)}")
    
    if len(reviews_2023) == 0:
        st.warning("No 2023 reviews found.")
        st.stop()
    
    # MONTH PROCESSING
    reviews_2023['date'] = pd.to_datetime(reviews_2023['date'], errors='coerce')
    reviews_2023['month_str'] = reviews_2023['date'].dt.strftime('%Y-%m').fillna('Unknown')
    months = sorted(reviews_2023['month_str'].unique())
    
    st.caption(f"Available months: {months}")
    
    # MONTH SELECTOR
    selected_month = st.select_slider("Select month:", options=months, value=months[0])
    month_reviews = reviews_2023[reviews_2023['month_str'] == selected_month]
    
    st.subheader(f"Reviews: {selected_month} ({len(month_reviews)})")
    
    # TABLE
    st.dataframe(month_reviews[['date', 'text', 'sentiment']].head(10))
    
    # CHARTS - SAFE
    if len(month_reviews) > 0:
        counts = month_reviews['sentiment'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Sentiment Distribution")
            st.bar_chart(counts)
        
        with col2:
            st.subheader("Review Samples")
            st.write(month_reviews[['text', 'sentiment']].head(3))
    else:
        st.info("No reviews for this month.")

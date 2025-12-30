import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

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
def get_sentiment(text):
    if pd.isna(text):
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
    st.header("Reviews – Pre-computed Sentiment Analysis (Professor Method)")
    
    # Load professor-approved file (you'll create this next)
    try:
        reviews_sentiment = pd.read_csv("data/reviews_with_sentiment.csv")
        st.success(f"✅ Professor-approved: Loaded {len(reviews_sentiment)} reviews with sentiment!")
        
        # Filter 2023
        reviews_2023 = reviews_sentiment[pd.to_datetime(reviews_sentiment['date']).dt.year == 2023]
        st.info(f"📊 2023 reviews: {len(reviews_2023)}")
        
        if len(reviews_2023) > 0:
            # Month selector
            reviews_2023['month_str'] = pd.to_datetime(reviews_2023['date']).dt.strftime('%Y-%m')
            months = sorted(reviews_2023['month_str'].unique())
            selected_month = st.select_slider("Select month:", options=months, value=months[0])
            
            month_reviews = reviews_2023[reviews_2023['month_str'] == selected_month]
            
            st.subheader(f"Reviews: {selected_month} ({len(month_reviews)})")
            
            # Show table
            st.dataframe(month_reviews[['date', 'text', 'sentiment', 'confidence']].head(10))
            
            # Charts
            counts = month_reviews['sentiment'].value_counts()
            st.subheader("📈 Sentiment Distribution")
            st.bar_chart(counts)
            
        else:
            st.warning("No 2023 reviews in pre-computed file.")
            
    except FileNotFoundError:
        st.error("❌ Missing 'data/reviews_with_sentiment.csv' - run sentiment analysis first!")
        st.info("👉 Command Prompt: python → paste sentiment code → exit()")

    
    st.info(f"📊 Loaded {len(reviews_2023)} reviews from 2023")
    
    if len(reviews_2023) == 0:
        st.warning("No 2023 reviews found.")
        st.stop()
        
    reviews_2023['date'] = pd.to_datetime(reviews_2023['date'], errors='coerce')

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

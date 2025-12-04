"""
Streamlit dashboard for Enhanced OCR/Thread Analyzer.

Provides visualizations for:
- Per-thread sentiment over time
- Top topics via clustering
- Semantic search across messages

Run with: streamlit run webapp/dashboard/streamlit_app.py
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from prototype.enhanced.embeddings import MessageEmbeddings, compute_message_sentiment

# Page configuration
st.set_page_config(
    page_title="Thread Analyzer Dashboard",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Enhanced OCR/Thread Analyzer Dashboard")
st.markdown("Visualize sentiment, topics, and search messages semantically")

# Sidebar for file selection
st.sidebar.header("📁 Data Selection")

# Look for data files
data_dir = Path("output")
if not data_dir.exists():
    data_dir = Path(".")

# Find available message files
message_files = list(data_dir.glob("**/processed_messages.json"))
message_files.extend(list(data_dir.glob("**/ocr_results.json")))

if not message_files:
    st.error("No message data found. Please run the processing pipeline first.")
    st.info("Run: `python prototype/enhanced/process_folder.py <input> <output>`")
    st.stop()

selected_file = st.sidebar.selectbox(
    "Select Data File",
    options=message_files,
    format_func=lambda x: str(x.relative_to("."))
)

# Load data
@st.cache_data
def load_messages(file_path):
    """Load messages from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict):
        messages = data.get('messages', [])
    else:
        messages = data
    
    return messages

messages = load_messages(selected_file)

if not messages:
    st.warning("No messages found in selected file")
    st.stop()

st.sidebar.success(f"✓ Loaded {len(messages)} messages")

# Compute sentiment if not present
for msg in messages:
    if 'sentiment' not in msg:
        msg['sentiment'] = compute_message_sentiment(msg.get('text', ''))

# Convert to DataFrame
df = pd.DataFrame(messages)

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "😊 Sentiment", "🏷️ Topics", "🔍 Search"])

with tab1:
    st.header("Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Messages", len(messages))
    
    with col2:
        avg_confidence = df['confidence'].mean() if 'confidence' in df.columns else 0
        st.metric("Avg OCR Confidence", f"{avg_confidence:.1%}")
    
    with col3:
        avg_length = df['text'].str.len().mean()
        st.metric("Avg Message Length", f"{avg_length:.0f} chars")
    
    st.subheader("Sample Messages")
    st.dataframe(
        df[['text', 'confidence']].head(10),
        use_container_width=True,
        hide_index=True
    )

with tab2:
    st.header("Sentiment Analysis")
    
    # Extract sentiment scores
    sentiment_data = []
    for msg in messages:
        sentiment = msg.get('sentiment', {})
        sentiment_data.append({
            'message_id': msg.get('id', ''),
            'text': msg.get('text', '')[:50] + '...',
            'positive': sentiment.get('positive', 0),
            'negative': sentiment.get('negative', 0),
            'neutral': sentiment.get('neutral', 0)
        })
    
    sentiment_df = pd.DataFrame(sentiment_data)
    
    # Overall sentiment distribution
    st.subheader("Overall Sentiment Distribution")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_positive = sentiment_df['positive'].mean()
        st.metric("Avg Positive", f"{avg_positive:.2%}")
    
    with col2:
        avg_negative = sentiment_df['negative'].mean()
        st.metric("Avg Negative", f"{avg_negative:.2%}")
    
    with col3:
        avg_neutral = sentiment_df['neutral'].mean()
        st.metric("Avg Neutral", f"{avg_neutral:.2%}")
    
    # Sentiment over time (if we have indices as proxy for time)
    st.subheader("Sentiment Trend")
    st.line_chart(sentiment_df[['positive', 'negative', 'neutral']])
    
    # Most positive/negative messages
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Most Positive Messages")
        top_positive = sentiment_df.nlargest(5, 'positive')
        for _, row in top_positive.iterrows():
            st.success(f"**Score: {row['positive']:.2%}** - {row['text']}")
    
    with col2:
        st.subheader("Most Negative Messages")
        top_negative = sentiment_df.nlargest(5, 'negative')
        for _, row in top_negative.iterrows():
            st.error(f"**Score: {row['negative']:.2%}** - {row['text']}")

with tab3:
    st.header("Topic Clustering")
    
    # Load or create embeddings
    embeddings_file = selected_file.parent / "embeddings.pkl"
    
    if embeddings_file.exists():
        try:
            embedder = MessageEmbeddings.load(str(embeddings_file))
            st.success(f"✓ Loaded embeddings from {embeddings_file.name}")
        except Exception as e:
            st.warning(f"Could not load embeddings: {e}")
            st.info("Creating embeddings (this may take a moment)...")
            embedder = MessageEmbeddings()
            embedder.add_messages(messages)
    else:
        st.info("Creating embeddings (this may take a moment)...")
        try:
            embedder = MessageEmbeddings()
            embedder.add_messages(messages)
        except ImportError as e:
            st.error(f"Required libraries not installed: {e}")
            st.stop()
    
    # Cluster messages
    n_clusters = st.slider("Number of Clusters", min_value=2, max_value=10, value=5)
    
    if st.button("Generate Topics"):
        with st.spinner("Clustering messages..."):
            clusters = embedder.cluster(n_clusters=n_clusters)
            topics = embedder.get_cluster_topics(n_clusters=n_clusters, top_words=5)
        
        st.subheader(f"Found {len(clusters)} Topic Clusters")
        
        for cluster_id in sorted(clusters.keys()):
            cluster_messages = clusters[cluster_id]
            cluster_topics = topics.get(cluster_id, [])
            
            with st.expander(f"📌 Cluster {cluster_id + 1}: {', '.join(cluster_topics[:3])} ({len(cluster_messages)} messages)"):
                st.markdown(f"**Keywords:** {', '.join(cluster_topics)}")
                st.markdown("**Sample Messages:**")
                for msg in cluster_messages[:5]:
                    st.write(f"- {msg.text[:100]}...")

with tab4:
    st.header("Semantic Search")
    
    # Load embeddings if not already loaded
    embeddings_file = selected_file.parent / "embeddings.pkl"
    
    if embeddings_file.exists():
        try:
            embedder = MessageEmbeddings.load(str(embeddings_file))
        except:
            embedder = MessageEmbeddings()
            embedder.add_messages(messages)
    else:
        try:
            embedder = MessageEmbeddings()
            embedder.add_messages(messages)
        except ImportError as e:
            st.error(f"Required libraries not installed: {e}")
            st.stop()
    
    st.markdown("Search for messages by meaning, not just keywords")
    
    query = st.text_input("Enter search query:", placeholder="e.g., 'meeting tomorrow' or 'dinner plans'")
    
    k = st.slider("Number of results", min_value=1, max_value=20, value=5)
    
    if query:
        with st.spinner("Searching..."):
            results = embedder.search(query, k=k)
        
        st.subheader(f"Top {len(results)} Results")
        
        for i, (msg, distance) in enumerate(results, 1):
            similarity = 1 / (1 + distance)  # Convert distance to similarity
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{i}. {msg.text}**")
                    if msg.metadata:
                        st.caption(f"Source: {msg.metadata.get('source_image', 'unknown')}")
                
                with col2:
                    st.metric("Similarity", f"{similarity:.2%}")
                
                st.divider()

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Dashboard Info")
st.sidebar.info("""
This dashboard provides:
- Sentiment analysis over time
- Topic clustering
- Semantic message search

Data is loaded from the processing pipeline output.
""")

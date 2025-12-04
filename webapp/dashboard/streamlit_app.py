"""
Streamlit dashboard for OCR thread analysis and visualization.

Features:
- Sentiment analysis over time
- Topic clustering visualization
- Semantic search across messages
- Statistics and insights

Usage:
    streamlit run streamlit_app.py
"""

import streamlit as st
import sys
from pathlib import Path
import json
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Add prototype/enhanced to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'prototype' / 'enhanced'))

from embeddings import MessageEmbedder, compute_sentiment_scores

# Page config
st.set_page_config(
    page_title="OCR Thread Analyzer Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'embedder' not in st.session_state:
    st.session_state.embedder = None

# Title
st.title("📊 OCR Thread Analyzer Dashboard")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Load embeddings index
    index_path = st.text_input("Embeddings Index Path", value="webapp/results/embeddings")
    
    if st.button("Load Index"):
        try:
            embedder = MessageEmbedder(index_path=index_path)
            st.session_state.embedder = embedder
            st.success(f"Loaded {embedder.index.ntotal} messages")
        except Exception as e:
            st.error(f"Error loading index: {e}")
    
    st.divider()
    
    st.header("📚 About")
    st.markdown("""
    This dashboard provides insights into extracted message threads:
    - 📈 Sentiment analysis
    - 🔍 Semantic search
    - 🎯 Topic clustering
    - 📊 Statistics
    """)

# Main content
if st.session_state.embedder is None:
    st.info("👈 Load an embeddings index from the sidebar to get started")
    st.stop()

embedder = st.session_state.embedder

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🔍 Search", "🎯 Topics", "📊 Statistics"])

with tab1:
    st.header("Overview")
    
    # Get all messages
    messages = embedder.messages
    
    if not messages:
        st.warning("No messages in index")
        st.stop()
    
    # Compute sentiment scores
    with st.spinner("Computing sentiment scores..."):
        sentiments = compute_sentiment_scores(messages)
    
    # Create dataframe
    df = pd.DataFrame({
        'index': range(len(messages)),
        'message': messages,
        'sentiment': sentiments,
        'timestamp': range(len(messages))  # Placeholder timestamps
    })
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Messages", len(messages))
    
    with col2:
        avg_sentiment = df['sentiment'].mean()
        st.metric("Avg Sentiment", f"{avg_sentiment:.2f}", 
                 delta=None, delta_color="normal")
    
    with col3:
        positive_pct = (df['sentiment'] > 0).sum() / len(df) * 100
        st.metric("Positive %", f"{positive_pct:.1f}%")
    
    with col4:
        avg_length = df['message'].str.len().mean()
        st.metric("Avg Length", f"{avg_length:.0f} chars")
    
    # Sentiment over time chart
    st.subheader("Sentiment Over Time")
    
    fig = go.Figure()
    
    # Add scatter plot
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['sentiment'],
        mode='markers+lines',
        name='Sentiment',
        marker=dict(
            size=8,
            color=df['sentiment'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Sentiment")
        ),
        line=dict(width=1, color='lightgray')
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        xaxis_title="Message Index",
        yaxis_title="Sentiment Score",
        hovermode='closest',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sentiment distribution
    st.subheader("Sentiment Distribution")
    
    fig = px.histogram(df, x='sentiment', nbins=30, 
                      color_discrete_sequence=['#4CAF50'])
    fig.update_layout(
        xaxis_title="Sentiment Score",
        yaxis_title="Count",
        showlegend=False,
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent messages
    st.subheader("Recent Messages")
    
    recent_df = df.tail(10)[['message', 'sentiment']].copy()
    recent_df['sentiment'] = recent_df['sentiment'].apply(lambda x: f"{x:.2f}")
    
    st.dataframe(recent_df, use_container_width=True, hide_index=True)

with tab2:
    st.header("🔍 Semantic Search")
    
    st.markdown("""
    Search for messages semantically - find messages similar in meaning,
    not just keyword matches.
    """)
    
    # Search input
    query = st.text_input("Search query", placeholder="e.g., greeting, meeting, happy")
    
    k = st.slider("Number of results", min_value=1, max_value=20, value=5)
    
    if st.button("Search", type="primary") and query:
        with st.spinner("Searching..."):
            results = embedder.search(query, k=k)
        
        if results:
            st.success(f"Found {len(results)} results")
            
            for idx, msg, dist, meta in results:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"**Message #{idx}:** {msg}")
                        if meta:
                            st.caption(f"Metadata: {meta}")
                    
                    with col2:
                        similarity = max(0, 1 - dist / 10)  # Normalize distance to similarity
                        st.metric("Similarity", f"{similarity:.1%}")
                    
                    st.divider()
        else:
            st.warning("No results found")

with tab3:
    st.header("🎯 Topic Clustering")
    
    st.markdown("""
    Discover main topics in your messages using unsupervised clustering.
    """)
    
    n_clusters = st.slider("Number of topics", min_value=2, max_value=20, value=5)
    
    if st.button("Cluster Messages", type="primary"):
        with st.spinner("Clustering messages..."):
            clusters = embedder.cluster_messages(n_clusters=n_clusters)
            representatives = embedder.get_cluster_representatives(clusters, n_per_cluster=3)
        
        st.success(f"Found {len(clusters)} topics")
        
        # Show cluster sizes
        cluster_sizes = {k: len(v) for k, v in clusters.items()}
        
        fig = px.bar(
            x=list(cluster_sizes.keys()),
            y=list(cluster_sizes.values()),
            labels={'x': 'Topic', 'y': 'Number of Messages'},
            title='Messages per Topic',
            color=list(cluster_sizes.values()),
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show representatives
        st.subheader("Topic Representatives")
        
        for cluster_id, reps in representatives.items():
            with st.expander(f"📌 Topic {cluster_id} ({cluster_sizes[cluster_id]} messages)"):
                for idx, msg in reps:
                    st.markdown(f"- {msg}")

with tab4:
    st.header("📊 Statistics")
    
    stats = embedder.compute_statistics()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("General Statistics")
        st.json({
            "Total Messages": stats['num_messages'],
            "Total Characters": stats['total_chars'],
            "Total Words": stats['total_words'],
            "Avg Message Length": f"{stats['avg_length']:.1f} chars",
            "Avg Words per Message": f"{stats['avg_words']:.1f}",
            "Min Length": stats['min_length'],
            "Max Length": stats['max_length']
        })
    
    with col2:
        st.subheader("Model Information")
        st.json({
            "Model": stats['model'],
            "Embedding Dimension": stats['embedding_dimension']
        })
    
    # Message length distribution
    st.subheader("Message Length Distribution")
    
    lengths = [len(msg) for msg in embedder.messages]
    
    fig = px.histogram(
        x=lengths,
        nbins=50,
        labels={'x': 'Message Length (characters)', 'y': 'Count'},
        color_discrete_sequence=['#2196F3']
    )
    fig.update_layout(showlegend=False, height=300)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Word count distribution
    st.subheader("Word Count Distribution")
    
    word_counts = [len(msg.split()) for msg in embedder.messages]
    
    fig = px.histogram(
        x=word_counts,
        nbins=30,
        labels={'x': 'Word Count', 'y': 'Count'},
        color_discrete_sequence=['#FF9800']
    )
    fig.update_layout(showlegend=False, height=300)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Export options
    st.subheader("Export Data")
    
    if st.button("Export to JSON"):
        output_path = Path("webapp/results/export.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        embedder.export_to_json(str(output_path))
        st.success(f"Exported to {output_path}")
        
        with open(output_path, 'r') as f:
            data = f.read()
        
        st.download_button(
            label="Download JSON",
            data=data,
            file_name="messages_export.json",
            mime="application/json"
        )

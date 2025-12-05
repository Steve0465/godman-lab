#!/usr/bin/env python3
"""
Document Organizer - Visual Dashboard

Interactive web dashboard for viewing and managing documents.
Run with: streamlit run docs_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import json

st.set_page_config(
    page_title="Document Manager",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; margin-bottom: 2rem;}
    .metric-card {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;}
    .urgent {background-color: #ff4b4b; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem;}
    .action {background-color: #ffa500; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem;}
    .review {background-color: #4CAF50; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data(csv_path: str):
    """Load document analysis data"""
    try:
        df = pd.read_csv(csv_path)
        if 'due_date' in df.columns:
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def main():
    # Header
    st.markdown('<div class="main-header">📄 Document Manager Dashboard</div>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Settings")
        
        csv_path = st.text_input(
            "CSV Path",
            value="organized_documents/document_analysis.csv"
        )
        
        st.divider()
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Load data
    if not Path(csv_path).exists():
        st.warning(f"⚠️ No data file found at: {csv_path}")
        st.info("Run `organize_documents.py` first to analyze your documents.")
        return
    
    df = load_data(csv_path)
    
    if df.empty:
        st.warning("No documents found")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", len(df))
    
    with col2:
        urgent_count = len(df[df['action'] == 'URGENT'])
        st.metric("Urgent Items", urgent_count, 
                 delta=f"{urgent_count} need attention" if urgent_count > 0 else None,
                 delta_color="inverse")
    
    with col3:
        if 'amount' in df.columns:
            total_amount = df['amount'].sum()
            st.metric("Total Amount", f"${total_amount:,.2f}")
        else:
            st.metric("Categories", df['category'].nunique())
    
    with col4:
        action_count = len(df[df['action'] == 'ACTION'])
        st.metric("Needs Action", action_count)
    
    st.divider()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Overview", 
        "⚠️ Urgent Items", 
        "📊 Analytics",
        "🔍 Search",
        "📅 Timeline"
    ])
    
    # Tab 1: Overview
    with tab1:
        st.subheader("Document Overview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Category breakdown
            category_counts = df['category'].value_counts()
            fig_cat = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Documents by Category",
                hole=0.4
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            # Action priority breakdown
            action_counts = df['action'].value_counts()
            colors = {'URGENT': '#ff4b4b', 'ACTION': '#ffa500', 
                     'REVIEW': '#4CAF50', 'ARCHIVE': '#808080'}
            fig_action = px.bar(
                x=action_counts.index,
                y=action_counts.values,
                title="Documents by Action Priority",
                color=action_counts.index,
                color_discrete_map=colors
            )
            st.plotly_chart(fig_action, use_container_width=True)
        
        # Recent documents table
        st.subheader("Recent Documents")
        display_df = df[['filename', 'category', 'action', 'summary', 'due_date', 'amount']].copy()
        st.dataframe(display_df, use_container_width=True, height=400)
    
    # Tab 2: Urgent Items
    with tab2:
        st.subheader("⚠️ Urgent Items Requiring Attention")
        
        urgent_df = df[df['action'].isin(['URGENT', 'ACTION'])].copy()
        
        if len(urgent_df) == 0:
            st.success("✅ No urgent items! Everything is up to date.")
        else:
            # Sort by due date
            if 'due_date' in urgent_df.columns:
                urgent_df = urgent_df.sort_values('due_date')
            
            for idx, row in urgent_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        priority = "🔴 URGENT" if row['action'] == 'URGENT' else "🟠 ACTION"
                        st.markdown(f"### {priority} - {row['filename']}")
                        st.write(row['summary'])
                        if row.get('action_required'):
                            st.info(f"**Action:** {row['action_required']}")
                    
                    with col2:
                        if pd.notna(row.get('due_date')):
                            due = row['due_date']
                            days_until = (due - datetime.now()).days
                            if days_until < 0:
                                st.error(f"**OVERDUE**\n{abs(days_until)} days ago")
                            elif days_until == 0:
                                st.warning("**DUE TODAY**")
                            else:
                                st.info(f"**Due in {days_until} days**\n{due.strftime('%Y-%m-%d')}")
                    
                    with col3:
                        if pd.notna(row.get('amount')):
                            st.metric("Amount", f"${row['amount']:,.2f}")
                    
                    st.divider()
    
    # Tab 3: Analytics
    with tab3:
        st.subheader("📊 Document Analytics")
        
        if 'amount' in df.columns and df['amount'].notna().any():
            col1, col2 = st.columns(2)
            
            with col1:
                # Spending by category
                category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
                fig_spending = px.bar(
                    x=category_spending.values,
                    y=category_spending.index,
                    orientation='h',
                    title="Total Amount by Category",
                    labels={'x': 'Amount ($)', 'y': 'Category'}
                )
                st.plotly_chart(fig_spending, use_container_width=True)
            
            with col2:
                # Amount distribution
                fig_dist = px.histogram(
                    df[df['amount'] > 0],
                    x='amount',
                    title="Amount Distribution",
                    nbins=20
                )
                st.plotly_chart(fig_dist, use_container_width=True)
            
            # Timeline of amounts
            if 'due_date' in df.columns:
                timeline_df = df[df['due_date'].notna()].copy()
                if len(timeline_df) > 0:
                    fig_timeline = px.scatter(
                        timeline_df,
                        x='due_date',
                        y='amount',
                        color='category',
                        size='amount',
                        hover_data=['filename', 'summary'],
                        title="Document Timeline"
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Tab 4: Search
    with tab4:
        st.subheader("🔍 Search Documents")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_term = st.text_input("Search by filename, summary, or category")
        
        with col2:
            category_filter = st.selectbox(
                "Filter by category",
                ['All'] + list(df['category'].unique())
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            mask = (
                filtered_df['filename'].str.contains(search_term, case=False, na=False) |
                filtered_df['summary'].str.contains(search_term, case=False, na=False) |
                filtered_df['category'].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if category_filter != 'All':
            filtered_df = filtered_df[filtered_df['category'] == category_filter]
        
        st.write(f"Found {len(filtered_df)} documents")
        st.dataframe(filtered_df, use_container_width=True)
    
    # Tab 5: Timeline
    with tab5:
        st.subheader("📅 Document Timeline")
        
        if 'due_date' in df.columns:
            timeline_df = df[df['due_date'].notna()].copy()
            timeline_df = timeline_df.sort_values('due_date')
            
            if len(timeline_df) > 0:
                # Create Gantt-style timeline
                fig = go.Figure()
                
                for idx, row in timeline_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row['due_date']],
                        y=[row['category']],
                        mode='markers+text',
                        name=row['filename'],
                        marker=dict(
                            size=15,
                            color='red' if row['action'] == 'URGENT' else 'orange'
                        ),
                        text=f"${row.get('amount', 0):.0f}",
                        textposition="top center",
                        hovertext=f"{row['filename']}<br>{row['summary']}"
                    ))
                
                fig.update_layout(
                    title="Due Dates by Category",
                    xaxis_title="Date",
                    yaxis_title="Category",
                    showlegend=False,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Upcoming due dates
                st.subheader("Upcoming Due Dates")
                next_30 = timeline_df[
                    timeline_df['due_date'] <= datetime.now() + timedelta(days=30)
                ]
                
                if len(next_30) > 0:
                    for _, row in next_30.iterrows():
                        days_until = (row['due_date'] - datetime.now()).days
                        status = "🔴" if days_until < 0 else "🟡" if days_until < 7 else "🟢"
                        st.write(f"{status} **{row['due_date'].strftime('%Y-%m-%d')}** - {row['filename']} - ${row.get('amount', 0):.2f}")
            else:
                st.info("No documents with due dates found")
        else:
            st.info("No due date information available")


if __name__ == '__main__':
    main()

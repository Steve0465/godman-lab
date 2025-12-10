#!/usr/bin/env python3
"""
🔥 PATTERN ANALYSIS SYSTEM
Analyzes receipts for anomalies and patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

# Will use these once installed:
# from pyod.models.knn import KNN
# from pyod.models.iforest import IForest
# from darts import TimeSeries
# from darts.models import Prophet

def load_receipts(csv_path='receipts_tax.csv'):
    """Load receipt data"""
    if not pd.io.common.file_exists(csv_path):
        raise FileNotFoundError(f"Receipt CSV not found: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} receipts")
    return df

def analyze_spending_patterns(df):
    """Basic statistical analysis"""
    print("\n📊 SPENDING ANALYSIS")
    print("=" * 50)
    
    if df is None or len(df) == 0:
        print("No data to analyze")
        return
    
    # Basic stats
    if 'amount' in df.columns:
        print(f"\n💰 Amount Statistics:")
        print(f"  Total:   ${df['amount'].sum():.2f}")
        print(f"  Average: ${df['amount'].mean():.2f}")
        print(f"  Median:  ${df['amount'].median():.2f}")
        print(f"  Max:     ${df['amount'].max():.2f}")
        print(f"  Min:     ${df['amount'].min():.2f}")
    
    # Vendor analysis
    if 'vendor' in df.columns:
        print(f"\n🏪 Top Vendors:")
        top_vendors = df.groupby('vendor')['amount'].sum().sort_values(ascending=False).head(5)
        for vendor, amount in top_vendors.items():
            print(f"  {vendor}: ${amount:.2f}")
    
    # Category analysis
    if 'tax_category' in df.columns:
        print(f"\n📁 Spending by Category:")
        by_category = df.groupby('tax_category')['amount'].sum().sort_values(ascending=False)
        for category, amount in by_category.items():
            print(f"  {category}: ${amount:.2f}")
    
    # Date patterns
    if 'date' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['date'])
            print(f"\n📅 Date Range:")
            print(f"  From: {df['date'].min()}")
            print(f"  To:   {df['date'].max()}")
            print(f"  Days: {(df['date'].max() - df['date'].min()).days}")
        except:
            pass

def detect_anomalies(df):
    """Detect unusual transactions using PyOD"""
    print("\n🔍 ANOMALY DETECTION")
    print("=" * 50)
    
    if df is None or len(df) == 0:
        print("No data to analyze")
        return
    
    try:
        from pyod.models.knn import KNN
        from pyod.models.iforest import IForest
        
        # Prepare data
        if 'amount' not in df.columns:
            print("⚠️  No amount column found")
            return
        
        amounts = df[['amount']].values
        
        # Method 1: K-Nearest Neighbors
        print("\n🎯 Method 1: K-Nearest Neighbors")
        knn = KNN(contamination=0.1)  # Expect 10% anomalies
        knn.fit(amounts)
        labels = knn.labels_  # 0 = normal, 1 = anomaly
        scores = knn.decision_scores_
        
        anomalies = df[labels == 1].copy()
        print(f"  Found {len(anomalies)} unusual transactions")
        
        if len(anomalies) > 0:
            print("\n  🚨 Unusual Transactions:")
            for idx, row in anomalies.head(5).iterrows():
                vendor = row.get('vendor', 'Unknown')
                amount = row.get('amount', 0)
                date = row.get('date', 'Unknown')
                print(f"    ${amount:.2f} at {vendor} on {date}")
        
        # Method 2: Isolation Forest
        print("\n🎯 Method 2: Isolation Forest")
        iforest = IForest(contamination=0.1)
        iforest.fit(amounts)
        labels2 = iforest.labels_
        
        anomalies2 = df[labels2 == 1].copy()
        print(f"  Found {len(anomalies2)} unusual transactions")
        
        # Combine both methods (high confidence)
        high_confidence = df[(labels == 1) & (labels2 == 1)]
        if len(high_confidence) > 0:
            print(f"\n  ⚠️  HIGH CONFIDENCE ANOMALIES: {len(high_confidence)}")
            for idx, row in high_confidence.iterrows():
                vendor = row.get('vendor', 'Unknown')
                amount = row.get('amount', 0)
                print(f"    ${amount:.2f} at {vendor}")
        
        return labels, scores
        
    except ImportError:
        print("⚠️  PyOD not installed yet. Install with: pip install pyod")
        return None, None

def forecast_spending(df):
    """Forecast future spending using Darts"""
    print("\n📈 SPENDING FORECAST")
    print("=" * 50)
    
    if df is None or len(df) == 0:
        print("No data to analyze")
        return
    
    try:
        from darts import TimeSeries
        from darts.models import Prophet
        
        # Need date and amount
        if 'date' not in df.columns or 'amount' not in df.columns:
            print("⚠️  Need date and amount columns")
            return
        
        # Prepare time series
        df_sorted = df.sort_values('date')
        df_sorted['date'] = pd.to_datetime(df_sorted['date'])
        
        # Group by date
        daily_spending = df_sorted.groupby('date')['amount'].sum().reset_index()
        
        if len(daily_spending) < 10:
            print("⚠️  Need more data points for forecasting (have {len(daily_spending)})")
            return
        
        # Create time series
        ts = TimeSeries.from_dataframe(daily_spending, 'date', 'amount')
        
        # Fit model
        print("\n🤖 Training forecasting model...")
        model = Prophet()
        model.fit(ts)
        
        # Forecast next 30 days
        forecast = model.predict(n=30)
        
        print("\n📊 30-Day Forecast:")
        forecast_df = forecast.pd_dataframe()
        print(f"  Predicted total: ${forecast_df['amount'].sum():.2f}")
        print(f"  Average per day: ${forecast_df['amount'].mean():.2f}")
        print(f"  Highest day:     ${forecast_df['amount'].max():.2f}")
        
        return forecast
        
    except ImportError:
        print("⚠️  Darts not installed yet. Install with: pip install darts")
        return None
    except Exception as e:
        print(f"⚠️  Error in forecasting: {e}")
        return None

def create_visualizations(df, anomaly_labels=None, anomaly_scores=None):
    """Create plots"""
    print("\n📊 CREATING VISUALIZATIONS")
    print("=" * 50)
    
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        if df is None or len(df) == 0:
            print("No data to visualize")
            return
        
        # Set style
        sns.set_style("darkgrid")
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Receipt Pattern Analysis', fontsize=16)
        
        # Plot 1: Amount distribution
        if 'amount' in df.columns:
            axes[0, 0].hist(df['amount'], bins=20, edgecolor='black')
            axes[0, 0].set_title('Amount Distribution')
            axes[0, 0].set_xlabel('Amount ($)')
            axes[0, 0].set_ylabel('Frequency')
        
        # Plot 2: Spending by vendor
        if 'vendor' in df.columns:
            top_vendors = df.groupby('vendor')['amount'].sum().sort_values(ascending=False).head(10)
            axes[0, 1].barh(range(len(top_vendors)), top_vendors.values)
            axes[0, 1].set_yticks(range(len(top_vendors)))
            axes[0, 1].set_yticklabels(top_vendors.index)
            axes[0, 1].set_title('Top 10 Vendors')
            axes[0, 1].set_xlabel('Total Amount ($)')
        
        # Plot 3: Anomaly scores
        if anomaly_scores is not None:
            axes[1, 0].scatter(range(len(anomaly_scores)), anomaly_scores, 
                              c=anomaly_labels, cmap='RdYlGn_r', alpha=0.6)
            axes[1, 0].set_title('Anomaly Detection Scores')
            axes[1, 0].set_xlabel('Transaction #')
            axes[1, 0].set_ylabel('Anomaly Score')
        
        # Plot 4: Spending over time
        if 'date' in df.columns:
            try:
                df_sorted = df.copy()
                df_sorted['date'] = pd.to_datetime(df_sorted['date'])
                df_sorted = df_sorted.sort_values('date')
                axes[1, 1].plot(df_sorted['date'], df_sorted['amount'], 'o-', alpha=0.6)
                axes[1, 1].set_title('Spending Over Time')
                axes[1, 1].set_xlabel('Date')
                axes[1, 1].set_ylabel('Amount ($)')
                plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45)
            except:
                pass
        
        plt.tight_layout()
        
        # Save
        output_path = 'receipt_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved visualization to: {output_path}")
        
        # Try to open it
        import subprocess
        subprocess.run(['open', output_path], check=False)
        
    except ImportError:
        print("⚠️  Matplotlib/Seaborn not installed")
    except Exception as e:
        print(f"⚠️  Error creating visualizations: {e}")

def main():
    """Main analysis pipeline"""
    print("🔥 PATTERN ANALYSIS SYSTEM")
    print("=" * 50)
    print()
    
    # Load data
    try:
        df = load_receipts('receipts_tax.csv')
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        print("\n⚠️  No receipt data found!")
        print("Run your receipt processor first to generate receipts_tax.csv")
        return 1
    
    if len(df) == 0:
        print("\n⚠️  Receipt CSV is empty!")
        return 1
    
    # Run analyses
    analyze_spending_patterns(df)
    anomaly_labels, anomaly_scores = detect_anomalies(df)
    forecast_spending(df)
    create_visualizations(df, anomaly_labels, anomaly_scores)
    
    print("\n" + "=" * 50)
    print("✅ ANALYSIS COMPLETE!")
    print("\nGenerated:")
    print("  - Statistical summary")
    print("  - Anomaly detection report")
    print("  - Spending forecast (if enough data)")
    print("  - Visualization plots")
    print("\nNext steps:")
    print("  1. Review anomalies for unusual spending")
    print("  2. Check forecast against budget")
    print("  3. Investigate high-spending categories")
    print("  4. Set up alerts for future anomalies")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

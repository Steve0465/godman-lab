#!/usr/bin/env python3
"""
🔥 NETFLIX PATTERN ANALYZER
Analyzes viewing history to recommend what to watch next
"""

import pandas as pd
import numpy as np
from collections import Counter
from datetime import datetime
from pathlib import Path
import os

from pathlib import Path
import os

# Default path - can be overridden with environment variable
DEFAULT_NETFLIX_PATH = Path.home() / "Desktop" / "NetflixViewingHistory.csv"

def load_netflix_data(file_path):
    """Load and parse Netflix viewing history"""
    print("📺 LOADING NETFLIX VIEWING HISTORY")
    print("=" * 60)
    
    # Read the weird format
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Parse manually
    data = []
    for i, line in enumerate(lines):
        if i == 0:  # Skip header
            continue
        parts = line.strip().rsplit(',', 1)  # Split from right to get date
        if len(parts) == 2:
            title, date = parts
            data.append({'title': title.strip(), 'date': date.strip()})
    
    df = pd.DataFrame(data)
    print(f"✅ Loaded {len(df)} viewing records\n")
    return df

def analyze_viewing_patterns(df):
    """Analyze what you watch"""
    print("\n🎯 VIEWING PATTERN ANALYSIS")
    print("=" * 60)
    
    # Convert dates
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y', errors='coerce')
    
    print(f"\n📅 Viewing Period:")
    print(f"  First watched: {df['date'].min()}")
    print(f"  Last watched: {df['date'].max()}")
    print(f"  Total days: {(df['date'].max() - df['date'].min()).days}")
    print(f"  Average per day: {len(df) / max((df['date'].max() - df['date'].min()).days, 1):.1f}")
    
    # Detect shows vs movies
    df['is_series'] = df['title'].str.contains(':', na=False)
    df['is_episode'] = df['title'].str.contains('Episode|Chapter|Part|Season', case=False, na=False)
    
    shows = df[df['is_series']].copy()
    movies = df[~df['is_series']].copy()
    
    print(f"\n📊 Content Breakdown:")
    print(f"  TV Series episodes: {len(shows)} ({len(shows)/len(df)*100:.1f}%)")
    print(f"  Movies: {len(movies)} ({len(movies)/len(df)*100:.1f}%)")
    
    # Extract series names
    shows['series_name'] = shows['title'].str.split(':').str[0]
    
    print(f"\n🔥 TOP 10 MOST BINGED SERIES:")
    top_series = shows['series_name'].value_counts().head(10)
    for series, count in top_series.items():
        print(f"  {count} episodes - {series}")
    
    print(f"\n🎬 RECENT MOVIES:")
    recent_movies = movies.sort_values('date', ascending=False).head(10)
    for idx, row in recent_movies.iterrows():
        print(f"  {row['date'].strftime('%m/%d/%y')} - {row['title']}")
    
    return df

def detect_genres_and_preferences(df):
    """Detect what genres/types you like"""
    print("\n🎭 PREFERENCE DETECTION")
    print("=" * 60)
    
    # Genre keywords
    genres = {
        'Action': ['action', 'fight', 'battle', 'war', 'combat'],
        'Comedy': ['comedy', 'funny', 'hangover', 'jokes'],
        'Drama': ['drama', 'life', 'story'],
        'Sci-Fi': ['stranger things', 'future', 'space', 'alien', 'sci-fi'],
        'Horror': ['horror', 'scary', 'dead', 'zombie', 'monster'],
        'Crime': ['crime', 'detective', 'police', 'murder', 'missing'],
        'Fantasy': ['fantasy', 'magic', 'dragon', 'wizard'],
        'Documentary': ['documentary', 'true', 'real'],
        'Reality': ['reality', 'survivor', 'competition']
    }
    
    # Detect genres
    genre_counts = {}
    for genre, keywords in genres.items():
        count = 0
        for keyword in keywords:
            count += df['title'].str.contains(keyword, case=False, na=False).sum()
        if count > 0:
            genre_counts[genre] = count
    
    print("\n🎪 Your Genre Preferences:")
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    for genre, count in sorted_genres[:10]:
        print(f"  {genre}: {count} shows/movies")
    
    return sorted_genres

def recommend_shows(df, top_genres):
    """Recommend what to watch next"""
    print("\n💡 RECOMMENDATIONS - WHAT TO WATCH NEXT")
    print("=" * 60)
    
    # Get series you started but didn't finish much
    df['series_name'] = df['title'].str.split(':').str[0]
    series_counts = df[df['is_series']]['series_name'].value_counts()
    
    # Recently watched
    recent = df.sort_values('date', ascending=False).head(20)
    recent_series = recent[recent['is_series']]['series_name'].unique()
    
    print("\n🔥 BASED ON YOUR PATTERNS:")
    print("\n1. IF YOU LIKED THESE, TRY:")
    
    recommendations = {
        'Stranger Things': ['Dark (Netflix)', 'The Midnight Club', 'Archive 81', 'From (MGM+)'],
        'Missing: Dead or Alive?': ['Unsolved Mysteries', 'Disappeared', 'The Vanishing at the Cecil Hotel'],
        'The Hangover': ['Game Night', '21 Jump Street', 'We\'re the Millers', 'Horrible Bosses'],
        'Aquaman': ['The Batman', 'Black Adam', 'Shazam', 'Blue Beetle']
    }
    
    for show in recent_series[:5]:
        if show in recommendations:
            print(f"\n  If you liked '{show}':")
            for rec in recommendations[show]:
                print(f"    → {rec}")
    
    print("\n\n2. TRENDING NOW (Based on your genres):")
    if top_genres:
        if any('Crime' in g[0] or 'Horror' in g[0] for g in top_genres[:3]):
            print("  → American Nightmare (Documentary/Crime)")
            print("  → The Fall of the House of Usher (Horror)")
            print("  → Bodies (Crime/Sci-Fi)")
        
        if any('Sci-Fi' in g[0] or 'Fantasy' in g[0] for g in top_genres[:3]):
            print("  → 3 Body Problem (Sci-Fi)")
            print("  → Avatar: The Last Airbender (Fantasy)")
            print("  → Gyeongseong Creature (Horror/Sci-Fi)")
    
    print("\n\n3. HIDDEN GEMS YOU MIGHT HAVE MISSED:")
    print("  → Beef (Drama/Dark Comedy)")
    print("  → The Gentlemen (Crime/Comedy)")
    print("  → Obliterated (Action/Comedy)")
    print("  → The Recruit (Action/Thriller)")
    print("  → Boy Swallows Universe (Drama)")
    
    print("\n\n4. BINGE-WORTHY NEW RELEASES:")
    print("  → The Diplomat (Political Thriller)")
    print("  → Griselda (Crime Drama)")
    print("  → Baby Reindeer (Dark Comedy/Drama)")
    print("  → Ripley (Thriller)")

def analyze_binge_patterns(df):
    """Analyze your binge-watching behavior"""
    print("\n📈 BINGE-WATCHING ANALYSIS")
    print("=" * 60)
    
    # Group by date
    daily_watching = df.groupby(df['date'].dt.date).size()
    
    print(f"\n🍿 Binge Stats:")
    print(f"  Average episodes per day: {daily_watching.mean():.1f}")
    print(f"  Maximum binge day: {daily_watching.max()} episodes")
    print(f"  Days with 5+ episodes: {(daily_watching >= 5).sum()}")
    
    # Best binge days
    print(f"\n🔥 Biggest Binge Days:")
    top_days = daily_watching.nlargest(5)
    for date, count in top_days.items():
        shows_that_day = df[df['date'].dt.date == date]['title'].head(3)
        print(f"  {date}: {count} episodes")
        for show in shows_that_day:
            print(f"    - {show}")

def main():
    """Run full analysis"""
    print("\n🎬 NETFLIX VIEWING PATTERN ANALYZER")
    print("=" * 60)
    print("Analyzing what you watch to recommend what's next!\n")
    
    # Get file path from environment or use default
    file_path = os.getenv("NETFLIX_CSV_PATH")
    if not file_path:
        file_path = DEFAULT_NETFLIX_PATH
    else:
        file_path = Path(file_path)
    
    # Load data with error handling
    try:
        df = load_netflix_data(file_path)
    except FileNotFoundError:
        print(f"\n❌ ERROR: Netflix viewing history not found at: {file_path}")
        print("\nTo fix this:")
        print(f"  1. Download your Netflix viewing history from Netflix account settings")
        print(f"  2. Save it to: {DEFAULT_NETFLIX_PATH}")
        print(f"  3. OR set environment variable: export NETFLIX_CSV_PATH=/path/to/your/file.csv")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR loading Netflix data: {e}")
        return 1
    
    # Run analyses
    df = analyze_viewing_patterns(df)
    top_genres = detect_genres_and_preferences(df)
    analyze_binge_patterns(df)
    recommend_shows(df, top_genres)
    
    print("\n\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE!")
    print("\nGot the list! Time to find something new to binge! 🍿")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

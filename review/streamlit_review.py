import os
import pandas as pd
import streamlit as st
from datetime import datetime

INPUT_DIR = os.getenv('INPUT_DIR','scans')
METADATA_CSV = os.getenv('METADATA_CSV','receipts.csv')
REVIEW_CSV = os.getenv('REVIEW_CSV','review_queue.csv')
CATEGORIES = os.getenv('CATEGORIES','meals,travel,supplies,office,software,rent,utilities,other').split(',')

st.title('Receipt Review')
st.markdown('Use this app to review parsed receipts and correct values. Changes are written back to receipts.csv')

if not os.path.exists(REVIEW_CSV):
    st.info('No review queue found. Run the processor first.')
else:
    df = pd.read_csv(REVIEW_CSV)
    if df.empty:
        st.success('No receipts need review.')
    else:
        idx = st.selectbox('Select receipt to review', df.index.tolist())
        row = df.loc[idx]
        st.image(row['stored_path']) if os.path.exists(row['stored_path']) else None
        vendor = st.text_input('Vendor', value=row.get('vendor',''))
        date = st.date_input('Date', value=datetime.fromisoformat(row['date']).date())
        total = st.number_input('Total', value=float(row.get('total',0.0)), format='%.2f')
        category = st.selectbox('Category', options=CATEGORIES, index=0)
        notes = st.text_area('Notes', value=row.get('parsed_text_snippet',''))

        if st.button('Save correction'):
            # update receipts.csv
            if os.path.exists(METADATA_CSV):
                meta = pd.read_csv(METADATA_CSV)
            else:
                meta = pd.DataFrame()
            # find by stored_path
            mask = meta['stored_path'] == row['stored_path'] if 'stored_path' in meta.columns else pd.Series([False]*len(meta))
            new_rec = dict(row)
            new_rec.update({
                'vendor': vendor,
                'date': date.isoformat(),
                'total': float(total),
                'category': category,
                'parsed_text_snippet': notes,
                'needs_review': False
            })
            if mask.any():
                meta.loc[mask, list(new_rec.keys())] = list(new_rec.values())
            else:
                meta = pd.concat([meta, pd.DataFrame([new_rec])], ignore_index=True)
            meta.to_csv(METADATA_CSV, index=False)
            # remove from review queue
            df2 = df.drop(index=idx)
            df2.to_csv(REVIEW_CSV, index=False)
            st.success('Saved correction and removed from review queue')

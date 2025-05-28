import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

# Koneksi MongoDB
client = MongoClient('mongodb+srv://ardyrkm15:rI36nIUliwAYySxG@cluster0.sekatch.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['berasa_db']

# Fungsi pembersih teks
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

# Sidebar navigasi
st.sidebar.title("Navigasi")
page = st.sidebar.radio("Pilih Halaman", ["Beranda", "Analisis Berita", "Top 10 Komoditas", "Distribusi Komoditas", "Word Cloud"])

# Beranda
if page == "Beranda":
    st.title("📊 Dashboard Berasa")
    st.markdown("""
    Selamat datang di **Dashboard Berasa**. Pilih halaman dari sidebar untuk melihat visualisasi data:
    - Analisis Berita
    - Top 10 Komoditas
    - Distribusi Komoditas per Subsektor
    - Word Cloud Isi Berita
    """)

# Analisis Berita
elif page == "Analisis Berita":
    st.title("📰 Analisis Berita")
    collection = db["data_donasi"]
    data = list(collection.find())
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'].str.replace("WIB", "").str.strip(), errors='coerce')
    df['views_clean'] = pd.to_numeric(df['views'].str.replace(r'\D', '', regex=True), errors='coerce')
    df['content_length'] = df['content'].apply(lambda x: len(x.split()) if x else 0)

    berita_harian = df.groupby(df['date'].dt.date).size().reset_index(name='jumlah')
    fig = px.bar(berita_harian, x='date', y='jumlah', title='Jumlah Berita per Hari')
    st.plotly_chart(fig)

# Top 10 Komoditas
elif page == "Top 10 Komoditas":
    st.title("📊 Top 10 Komoditas")
    collection = db["data_komoditas"]
    data = list(collection.find())
    df = pd.DataFrame(data)
    df['nilai_max'] = pd.to_numeric(df['nilai_max'], errors='coerce')
    df = df.dropna(subset=['nama', 'nilai_max'])
    df['nama'] = df['nama'].fillna('Tidak Diketahui')
    top10 = df.sort_values(by='nilai_max', ascending=False).head(10)
    fig = px.bar(top10, x='nilai_max', y='nama', orientation='h',
                 title='Top 10 Komoditas Berdasarkan Stok Maksimum',
                 labels={'nilai_max': 'Stok Maksimum (Kwintal)', 'nama': 'Komoditas'})
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig)

# Distribusi Komoditas
elif page == "Distribusi Komoditas":
    st.title("📈 Distribusi Komoditas per Subsektor")
    collection = db["data_komoditas"]
    data = list(collection.find())
    df = pd.DataFrame(data)
    if 'sector_id_desc' in df.columns:
        df['sektor_desc'] = df['sector_id_desc']
    else:
        df['sektor_desc'] = 'Tidak Diketahui'
    dist = df['sektor_desc'].value_counts().reset_index()
    dist.columns = ['Subsektor', 'Jumlah']
    fig = px.bar(dist, x='Subsektor', y='Jumlah', title='Distribusi Komoditas per Subsektor')
    st.plotly_chart(fig)

# Word Cloud
elif page == "Word Cloud":
    st.title("☁️ Word Cloud Isi Berita")
    collection = db["data_donasi"]
    contents = collection.find({}, {"content": 1})
    all_text = ' '.join([clean_text(doc["content"]) for doc in contents if "content" in doc and doc["content"]])
    factory = StopWordRemoverFactory()
    stopwords = set(factory.get_stop_words())
    all_text = ' '.join([word for word in all_text.split() if word not in stopwords])
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_text)
    plt.figure(figsize=(15, 7))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    st.pyplot(plt)

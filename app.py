import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. Configurazione Responsive e Stile
st.set_page_config(page_title="Firenze Smart City", layout="wide")

# CSS personalizzato per colori Firenze (Viola e Oro)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #4B2E83 !important; font-weight: 700; }
    .stMetric { 
        background-color: #ffffff; 
        border-radius: 12px; 
        padding: 20px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 4px solid #D4AF37; 
    }
    div[data-testid="stMetricValue"] { color: #4B2E83; font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df_dip = pd.read_csv('StatisticheDemografiche_IndiceDipendenzaPerQuartiere.csv', sep=';')
    df_vec = pd.read_csv('StatisticheDemografiche_IndiceVecchiaiaPerQuartiere.csv', sep=';')
    df_sal = pd.read_csv('StatisticheDemografiche_MovimentiAnagrafici_Dal_1_Gennaio_SaldoNaturale.csv', sep=';')
    
    for df in [df_dip, df_vec, df_sal]:
        df['ESTRAZIONE'] = pd.to_datetime(df['ESTRAZIONE'].astype(str), format='%Y%m')
        df.sort_values('ESTRAZIONE', inplace=True)

    # De-cumulazione Saldo Naturale
    df_sal = df_sal.copy()
    for col in ['MORTI', 'NATI', 'SALDO_NATURALE']:
        diff = df_sal[col].diff()
        df_sal[f'{col}_REALE'] = diff.where(df_sal['ESTRAZIONE'].dt.month != 1, df_sal[col])
    
    return df_dip, df_vec, df_sal

# Caricamento dati
try:
    df_dip_raw, df_vec_raw, df_sal_raw = load_data()
except Exception as e:
    st.error(f"Errore caricamento file: {e}")
    st.stop()

# --- SIDEBAR: FILTRI ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Coat_of_arms_of_Florence.svg/1200px-Coat_of_arms_of_Florence.svg.png", width=70)
st.sidebar.title("Filtri Analisi")

min_date = df_vec_raw['ESTRAZIONE'].min().to_pydatetime()
max_date = df_vec_raw['ESTRAZIONE'].max().to_pydatetime()
start_date, end_date = st.sidebar.slider("Periodo di riferimento", min_date, max_date, (min_date, max_date), format="MM/YYYY")

# Applicazione filtri
mask_v = (df_vec_raw['ESTRAZIONE'] >= start_date) & (df_vec_raw['ESTRAZIONE'] <= end_date)
mask_d = (df_dip_raw['ESTRAZIONE'] >= start_date) & (df_dip_raw['ESTRAZIONE'] <= end_date)
mask_s = (df_sal_raw['ESTRAZIONE'] >= start_date) & (df_sal_raw['ESTRAZIONE'] <= end_date)

df_vec = df_vec_raw.loc[mask_v].copy()
df_dip = df_dip_raw.loc[mask_d].copy()
df_sal = df_sal_raw.loc[mask_s].copy()

# --- MAIN DASHBOARD ---
st.title("🏙️ Firenze Smart City: Analisi Demografica")

# --- NUOVA SEZIONE: CARD METRICHE (Somme e Medie) ---
st.subheader("📌 Riepilogo Periodo Selezionato")
m1, m2, m3, m4 = st.columns(4)

with m1:
    avg_vec = df_vec['FIRENZE_INDICE_VECCHIAIA'].mean()
    st.metric("Media Indice Vecchiaia", f"{avg_vec:.1f}")

with m2:
    avg_dip = df_dip['FIRENZE_INDICE_DIPENDENZA'].mean()
    st.metric("Media Indice Dipendenza", f"{avg_dip:.1f}")

with m3:
    sum_sal = df_sal['SALDO_NATURALE_REALE'].sum()
    st.metric("Somma Saldo Naturale", f"{int(sum_sal)}")

with m4:
    avg_sal = df_sal['SALDO_NATURALE_REALE'].mean()
    st.metric("Media Saldo Mensile", f"{avg_sal:.1f}")

st.info("""
**IL PARADOSSO FIORENTINO:** Mentre l'indice di dipendenza resta stabile (attorno a 61), l'invecchiamento accelera. 
Il sistema regge numericamente, ma la base giovanile si contrae.
""")

# --- SEZIONE 1: INDICI ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Indice di Vecchiaia")
    df_vec['TREND'] = df_vec['FIRENZE_INDICE_VECCHIAIA'].rolling(window=12, center=True).mean()
    fig_v = go.Figure()
    fig_v.add_trace(go.Scatter(x=df_vec['ESTRAZIONE'], y=df_vec['FIRENZE_INDICE_VECCHIAIA'], name="Dato CSV", line=dict(color='rgba(75, 46, 131, 0.2)')))
    fig_v.add_trace(go.Scatter(x=df_vec['ESTRAZIONE'], y=df_vec['TREND'], name="Trend Reale", line=dict(color='#4B2E83', width=4)))
    fig_v.update_layout(hovermode="x unified", margin=dict(l=10, r=10, t=30, b=10), height=350)
    st.plotly_chart(fig_v, use_container_width=True)

with col2:
    st.subheader("🔗 Indice di Dipendenza")
    fig_d = go.Figure()
    fig_d.add_trace(go.Scatter(x=df_dip['ESTRAZIONE'], y=df_dip['FIRENZE_INDICE_DIPENDENZA'], name="Dipendenza", line=dict(color='#D4AF37', width=3)))
    
    # Annotazione Settembre 2017 (Revisione ISTAT/Comune)
    if not df_dip[df_dip['ESTRAZIONE'] == "2017-09-01"].empty:
        fig_d.add_annotation(x="2017-09-01", y=df_dip[df_dip['ESTRAZIONE'] == "2017-09-01"]['FIRENZE_INDICE_DIPENDENZA'].values[0],
                     text="Revisione Anagrafica", showarrow=True, arrowhead=1)
    
    fig_d.update_layout(hovermode="x unified", margin=dict(l=10, r=10, t=30, b=10), height=350)
    st.plotly_chart(fig_d, use_container_width=True)

# --- SEZIONE 2: SALDO NATURALE ---
st.divider()
st.header("📉 Saldo Naturale Mensile (Nati vs Morti)")

c_txt1, c_txt2 = st.columns(2)
with c_txt1:
    st.warning("**Nota Dati 2012-2015:** Vuoti dovuti a errori tecnici nei file CSV originali.")
with c_txt2:
    st.write("**Mistero Covid:** Impatto bilanciato tra decessi residenti e calo altre cause di morte (incidenti/influenze).")

fig_sal = go.Figure()
fig_sal.add_trace(go.Scatter(x=df_sal['ESTRAZIONE'], y=df_sal['MORTI_REALE'], name="Morti", line=dict(color='#e74c3c', width=2)))
fig_sal.add_trace(go.Scatter(x=df_sal['ESTRAZIONE'], y=df_sal['NATI_REALE'], name="Nati", line=dict(color='#2ecc71', width=2)))
fig_sal.add_trace(go.Scatter(x=df_sal['ESTRAZIONE'], y=df_sal['SALDO_NATURALE_REALE'], name="Saldo", line=dict(color='#4B2E83', dash='dot')))

# Zoom automatico asse Y
y_min = df_sal[['MORTI_REALE', 'NATI_REALE']].min().min() - 15
y_max = df_sal[['MORTI_REALE', 'NATI_REALE']].max().max() + 15

fig_sal.update_layout(
    hovermode="x unified",
    yaxis=dict(range=[y_min, y_max]),
    height=400,
    margin=dict(l=10, r=10, t=20, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig_sal, use_container_width=True)

# --- FOOTER ---
st.divider()
ultimo_vec = df_vec['FIRENZE_INDICE_VECCHIAIA'].iloc[-1] if not df_vec.empty else 0
rapporto = int(round(ultimo_vec / 100))
st.markdown(f"<h1 style='text-align: center;'>👶 vs {'👴' * rapporto}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Rapporto Finale:</b> {rapporto} anziani per ogni bambino a Firenze.</p>", unsafe_allow_html=True)
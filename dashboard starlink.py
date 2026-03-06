import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import os

st.set_page_config(layout="wide", page_title="Dashboard de Consumo")

st.title("📊 Dashboard de Consumo - Bases e Tráfego")

# -------------------------------------------------
# CONVERSÃO (MB, GB, TB → GB)
# -------------------------------------------------
def converter_para_gb(valor):
    if pd.isna(valor):
        return 0

    valor = str(valor).strip().upper().replace(",", ".")

    # Se for apenas número sem unidade, assume GB
    if re.match(r"^\d+(\.\d+)?$", valor):
        return float(valor)

    match = re.match(r"([\d\.]+)\s*(TB|GB|MB)", valor)
    if not match:
        return 0

    numero = float(match.group(1))
    unidade = match.group(2)

    if unidade == "TB":
        return numero * 1024
    elif unidade == "GB":
        return numero
    elif unidade == "MB":
        return numero / 1024
    else:
        return 0

# -------------------------------------------------
# FORMATAR COM UNIDADE
# -------------------------------------------------
def formatar_unidade(valor):
    if valor >= 1024:
        return f"{valor/1024:.2f} TB"
    else:
        return f"{valor:.2f} GB"

# -------------------------------------------------
# LEITURA SEGURA DO CSV
# -------------------------------------------------
def ler_csv_seguro(caminho):
    if not os.path.exists(caminho):
        st.warning(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()
    df = pd.read_csv(caminho)
    df.columns = (
        df.columns
        .str.strip()
        .str.replace("\ufeff", "")
        .str.upper()
    )
    return df

# -------------------------------------------------
# SIDEBAR - MÊS
# -------------------------------------------------
mes = st.sidebar.selectbox(
    "📅 Selecionar Mês",
    ["Fevereiro", "Março"]
)

# -------------------------------------------------
# SIDEBAR - TIPO
# -------------------------------------------------
tipo = st.sidebar.selectbox(
    "📡 Selecionar tipo de dado",
    ["Bases Starlink", "Tráfego de Carros"]
)

# -------------------------------------------------
# CARREGAR DADOS
# -------------------------------------------------
@st.cache_data
def carregar_dados(mes):
    if mes == "Fevereiro":
        arquivo_bases = "bases_fevereiro.csv"
        arquivo_trafego = "carros_fevereiro.csv"
    else:
        arquivo_bases = "bases_marco.csv"
        arquivo_trafego = "carros_marco.csv"

    df_bases = ler_csv_seguro(arquivo_bases)
    df_trafego = ler_csv_seguro(arquivo_trafego)

    # Renomear colunas caso venham diferentes
    df_bases = df_bases.rename(columns={
        "DATA": "DATA_INICIAL",
        "LOCALIDADE / PLACA": "LOCALIDADE"
    })
    df_trafego = df_trafego.rename(columns={
        "DATA": "DATA_INICIAL",
        "LOCALIDADE / PLACA": "PLACA"
    })

    # Criar DATA_FINAL se não existir
    if "DATA_FINAL" not in df_bases.columns and "DATA_INICIAL" in df_bases.columns:
        df_bases["DATA_FINAL"] = df_bases["DATA_INICIAL"]
    if "DATA_FINAL" not in df_trafego.columns and "DATA_INICIAL" in df_trafego.columns:
        df_trafego["DATA_FINAL"] = df_trafego["DATA_INICIAL"]

    # Garantir colunas e converter
    for df in [df_bases, df_trafego]:
        if "CONSUMO_INICIAL" not in df.columns:
            df["CONSUMO_INICIAL"] = "0 GB"
        if "CONSUMO_FINAL" not in df.columns:
            df["CONSUMO_FINAL"] = "0 GB"
        if "NOMES" not in df.columns:
            df["NOMES"] = "Desconhecido"
        if "DATA_INICIAL" not in df.columns:
            df["DATA_INICIAL"] = ""
        if "DATA_FINAL" not in df.columns:
            df["DATA_FINAL"] = ""

        df["CONSUMO_INICIAL_GB"] = df["CONSUMO_INICIAL"].apply(converter_para_gb)
        df["CONSUMO_FINAL_GB"] = df["CONSUMO_FINAL"].apply(converter_para_gb)
        df["DIFERENCA_GB"] = df["CONSUMO_FINAL_GB"] - df["CONSUMO_INICIAL_GB"]

        # Ajuste de datas para formato brasileiro
        if "DATA_INICIAL" in df.columns:
            df["DATA_INICIAL"] = pd.to_datetime(df["DATA_INICIAL"], dayfirst=True, errors="coerce")
        if "DATA_FINAL" in df.columns:
            df["DATA_FINAL"] = pd.to_datetime(df["DATA_FINAL"], dayfirst=True, errors="coerce")

    return df_bases, df_trafego

df_bases, df_trafego = carregar_dados(mes)

# -------------------------------------------------
# SELEÇÃO DO DATAFRAME
# -------------------------------------------------
if tipo == "Bases Starlink":
    df = df_bases.copy()
    label_col = "LOCALIDADE"
else:
    df = df_trafego.copy()
    label_col = "PLACA"

# Garantir coluna antes de ordenar
if "CONSUMO_FINAL_GB" not in df.columns:
    df["CONSUMO_FINAL_GB"] = 0

df = df.sort_values("CONSUMO_FINAL_GB")

data_inicial = df["DATA_INICIAL"].iloc[0] if len(df) > 0 else ""
data_final = df["DATA_FINAL"].iloc[0] if len(df) > 0 else ""

# -------------------------------------------------
# KPIs
# -------------------------------------------------
st.subheader("📌 Indicadores Gerais")

col1, col2, col3, col4 = st.columns(4)

# Consumo total = soma das diferenças (consumo real no período)
col1.metric("Consumo Total", formatar_unidade(df["DIFERENCA_GB"].sum()))

# Maior consumo individual no período
col2.metric("Maior Consumo", formatar_unidade(df["DIFERENCA_GB"].max()))

# Média de consumo no período
col3.metric("Média Consumo", formatar_unidade(df["DIFERENCA_GB"].mean()))

# Quantidade de monitorados
col4.metric("Total Monitorados", df.shape[0])


st.divider()

# -------------------------------------------------
# TABELA
# -------------------------------------------------
st.subheader(f"📋 Consumo detalhado - {tipo} ({mes})")

colunas_exibir = [
    "NOMES",
    "DATA_INICIAL",
    "CONSUMO_INICIAL",
    "DATA_FINAL",
    "CONSUMO_FINAL",
    label_col,
    "DIFERENCA_GB"
]
colunas_existentes = [c for c in colunas_exibir if c in df.columns]

st.dataframe(
    df[colunas_existentes].style.format(
        {"DIFERENCA_GB": lambda x: formatar_unidade(x)}
    ),
    use_container_width=True
)

st.divider()

# -------------------------------------------------
# GRÁFICO COMPARATIVO
# -------------------------------------------------
st.subheader(f"📊 Comparativo de Consumo - {tipo} ({mes})")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["CONSUMO_INICIAL_GB"],
    name=str(data_inicial),
    text=df["CONSUMO_INICIAL_GB"].apply(formatar_unidade),
    textposition="outside",
))
fig.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["CONSUMO_FINAL_GB"],
    name=str(data_final),
    text=df["CONSUMO_FINAL_GB"].apply(formatar_unidade),
    textposition="outside",
))
fig.update_layout(
    template="plotly_dark",
    barmode="group",
    height=650,
    xaxis_tickangle=-45,
    font=dict(size=16),
    yaxis_title="Consumo (GB / TB)",
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# -------------------------------------------------
# CONSUMO REAL
# -------------------------------------------------
st.subheader(f"📈 Consumo Real no Período - {tipo} ({mes})")

fig_diff = go.Figure()
fig_diff.add_trace(go.Bar(
    x=df["NOMES"],
    y=df["DIFERENCA_GB"],
    text=df["DIFERENCA_GB"].apply(formatar_unidade),
    textposition="outside",
))
fig_diff.update_layout(
    template="plotly_dark",
    height=600,
    xaxis_tickangle=-45,
    font=dict(size=16),
    yaxis_title="Consumo no Período",
)
st.plotly_chart(fig_diff, use_container_width=True)

st.divider()

# -------------------------------------------------
# RANKING
# -------------------------------------------------
st.markdown("## 🚨 Maiores consumos do período")

top5 = df.sort_values("DIFERENCA_GB", ascending=False).head(5).reset_index(drop=True)
top5["Ranking"] = top5.index + 1

def icone_alerta(posicao):
    if posicao == 1:
        return "🔴"
    elif posicao in [2, 3]:
        return "🟡"
    else:
        return "🔹"

top5["Alerta"] = top5["Ranking"].apply(icone_alerta)

st.dataframe(
    top5[["Ranking", "Alerta", "NOMES", "DIFERENCA_GB"]].style.format(
        {"DIFERENCA_GB": lambda x: formatar_unidade(x)}
    ),
    use_container_width=True,
)

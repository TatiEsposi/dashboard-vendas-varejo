
import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================

st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Análise de Sazonalidade das Vendas no Varejo")
st.caption("Análise do faturamento, produtos, categorias e eventos comerciais")

# Ordem correta dos meses
ordem_meses = [ 
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro"
]
# =====================================
# 2. CARREGAMENTO DA BASE CSV
# =====================================

arquivo = "vendas_dados2026.csv"
if arquivo is not None:
    df = pd.read_csv(arquivo, sep=",", encoding="utf-8-sig")

    # Limpeza dos nomes das colunas
    df.columns = df.columns.str.strip().str.lower()

    # Conferência das colunas necessárias
    colunas = [
        "produto", "categoria", "quantidade",
        "preco_unitario", "data_venda", "evento"
    ]

    if not all(coluna in df.columns for coluna in colunas):
        st.error("A planilha não possui todas as colunas esperadas.")
        st.stop()

    # Tratamento dos dados
    df["quantidade"] = pd.to_numeric(
        df["quantidade"], errors="coerce"
    )

    df["preco_unitario"] = pd.to_numeric(
        df["preco_unitario"], errors="coerce"
    )

    df["data_venda"] = df["data_venda"].str.strip().str.capitalize()

    df["evento"] = df["evento"].fillna("").str.strip()
    df["categoria"] = df["categoria"].str.strip()
    df["produto"] = df["produto"].str.strip()

    df = df.dropna(
        subset=[
            "produto", "categoria", "quantidade",
            "preco_unitario", "data_venda"
        ]
    )

    df = df[
        (df["quantidade"] > 0) &
        (df["preco_unitario"] > 0) &
        (df["data_venda"].isin(ordem_meses))
    ].copy()

    # Cálculo do faturamento
    df["faturamento"] = (
        df["quantidade"] * df["preco_unitario"]
    )

    # Organizar os meses
    df["data_venda"] = pd.Categorical(
        df["data_venda"],
        categories=ordem_meses,
        ordered=True
    )

    # =====================================
    # 3. FILTROS LATERAIS
    # =====================================

    st.sidebar.header("Filtros")

    meses = st.sidebar.multiselect(
        "Selecione os meses",
        options=[m for m in ordem_meses if m in df["data_venda"].tolist()],
        default=[m for m in ordem_meses if m in df["data_venda"].tolist()]
    )

    categorias = st.sidebar.multiselect(
        "Selecione as categorias",
        options=sorted(df["categoria"].unique()),
        default=sorted(df["categoria"].unique())
    )

    eventos_disponiveis = sorted(
        df.loc[df["evento"] != "", "evento"].unique()
    )

    eventos = st.sidebar.multiselect(
        "Selecione os eventos",
        options=eventos_disponiveis,
        default=eventos_disponiveis
    )

    # Aplicação dos filtros
    dados = df[
        df["data_venda"].isin(meses) &
        df["categoria"].isin(categorias) &
        (
            (df["evento"] == "") |
            (df["evento"].isin(eventos))
        )
    ].copy()
    lista_cat = ["Todas"] + sorted(dados["categoria"].dropna().unique().tolist())
    cat_topo = st.selectbox("Selecione a Categoria", lista_cat)
    if cat_topo != "Todas":   
        dados = dados[dados["categoria"] == cat_topo]
    if dados.empty:
        st.warning("Nenhum registro encontrado para os filtros escolhidos.")
        st.stop()

    # =====================================
    # 4. INDICADORES (KPIs)
    # =====================================

    faturamento_total = dados["faturamento"].sum()
    quantidade_total = dados["quantidade"].sum()
    total_produtos = dados["produto"].nunique()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Faturamento Total",
        f"R$ {faturamento_total:,.2f}"
    )

    col2.metric(
        "Quantidade Vendida",
        f"{quantidade_total:,.0f}"
    )

    col3.metric(
        "Produtos Diferentes",
        total_produtos
    )

    st.divider()

    # =====================================
    # 5. GRÁFICO 1 - LINHAS
    # FATURAMENTO POR MÊS
    # =====================================

    st.subheader("1. Faturamento por mês")

    vendas_mes = (
        dados.groupby("data_venda", observed=False)
        ["faturamento"]
        .sum()
        .reset_index()
        .sort_values("data_venda")
    )

    grafico_linha = px.line(
        vendas_mes,
        x="data_venda",
        y="faturamento",
        markers=True,
        title="Evolução do faturamento mensal",
        labels={
            "data_venda": "Mês",
            "faturamento": "Faturamento (R$)"
        }
    )

    st.plotly_chart(
        grafico_linha,
        use_container_width=True
    )

    # =====================================
    # 6. GRÁFICO 2 - BARRAS
    # FATURAMENTO POR PRODUTO
    # =====================================

    st.subheader("2. Produtos com maior faturamento")

    top_produtos = (
        dados.groupby("produto")["faturamento"]
        .sum()
        .nlargest(10)
        .reset_index()
        .sort_values("faturamento")
    )

    grafico_barras = px.bar(
        top_produtos,
        x="faturamento",
        y="produto",
        orientation="h",
        title="Os 10 produtos com maior faturamento",
        labels={
            "faturamento": "Faturamento (R$)",
            "produto": "Produto"
        }
    )

    st.plotly_chart(
        grafico_barras,
        use_container_width=True
    )

    # =====================================
    # 7. GRÁFICO 3 - COLUNAS
    # QUANTIDADE VENDIDA POR MÊS
    # =====================================

    st.subheader("3. Quantidade de produtos vendidos por mês")

    quantidade_mes = (
        dados.groupby("data_venda", observed=False)
        ["quantidade"]
        .sum()
        .reset_index()
        .sort_values("data_venda")
    )

    grafico_colunas = px.bar(
        quantidade_mes,
        x="data_venda",
        y="quantidade",
        title="Volume de vendas por mês",
        labels={
            "data_venda": "Mês",
            "quantidade": "Quantidade vendida"
        }
    )

    st.plotly_chart(
        grafico_colunas,
        use_container_width=True
    )

    # =====================================
    # 8. GRÁFICO 4 - PIZZA
    # FATURAMENTO POR CATEGORIA
    # =====================================

    st.subheader("4. Participação das categorias no faturamento")

    faturamento_categoria = (
        dados.groupby("categoria")["faturamento"]
        .sum()
        .reset_index()
    )

    grafico_pizza = px.pie(
        faturamento_categoria,
        names="categoria",
        values="faturamento",
        title="Distribuição do faturamento por categoria",
        hole=0.35
    )

    st.plotly_chart(
        grafico_pizza,
        use_container_width=True
    )

    st.success("Dashboard carregado com sucesso!")

    # =====================================
    # 9. VISUALIZAÇÃO DA BASE
    # =====================================

    with st.expander("Consultar dados da planilha"):
        st.dataframe(dados, use_container_width=True)

else:

    st.info(
        "Para visualizar o dashboard, "
        "envie sua planilha CSV pelo menu lateral."
    )

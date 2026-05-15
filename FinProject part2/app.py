# app.py
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

DB_PATH = "data/weather.db"

st.set_page_config(page_title="WeatherInsight: Метеоаналитика", layout="wide")
st.title("Интерактивный анализ погоды")
st.markdown("---")


# -------- ЗАГРУЗКА ДАННЫХ (кэширование) --------
@st.cache_resource
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM weather ORDER BY date", conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Ошибка загрузки базы данных: {e}")
    st.stop()

# ОБРАБОТКА ПРОПУСКОВ
numeric_cols = ["avg_temp", "total_precip", "avg_wind"]
for col in numeric_cols:
    if col in df_raw.columns and df_raw[col].isnull().any():
        df_raw[col] = df_raw[col].fillna(df_raw[col].median())

if "is_rainy" in df_raw.columns:
    df_raw["is_rainy"] = df_raw["is_rainy"].fillna(0).astype(int)


# ПРОИЗВОДНЫЕ СТОЛБЦЫ
def add_derived_columns(df):
    df = df.copy()

    # Категория температуры
    df["temp_category"] = pd.cut(
        df["avg_temp"],
        bins=[-100, 5, 20, 50],
        labels=["🥶 Холодно", "🌤️ Умеренно", "🔥 Жарко"]
    )

    # Уровень осадков
    df["precip_level"] = pd.cut(
        df["total_precip"],
        bins=[-0.1, 0.1, 5, 100],
        labels=["☀️ Без осадков", "💧 Небольшие", "🌧️ Сильные"]
    )

    # Комфортность (бинарная)
    if "is_rainy" in df.columns:
        df["comfort"] = (
                (df["avg_temp"] > 15) &
                (df["avg_temp"] < 25) &
                (df["avg_wind"] < 5) &
                (df["is_rainy"] == 0)
        )
        df["comfort_label"] = df["comfort"].map(
            {True: "😎 Комфортно", False: "😕 Не комфортно"}
        )

    return df


df = add_derived_columns(df_raw)

# БОКОВАЯ ПАНЕЛЬ ФИЛЬТРОВ
st.sidebar.header("Фильтры и настройки")

# Выбор городов
all_cities = sorted(df["city"].unique().tolist())
selected_cities = st.sidebar.multiselect(
    "Выберите город(а)",
    all_cities,
    default=[all_cities[0]] if all_cities else []
)

# Диапазон дат
min_date = df["date"].min().date() if not df.empty else datetime.now().date()
max_date = df["date"].max().date() if not df.empty else datetime.now().date()
date_range = st.sidebar.date_input(
    "Диапазон дат",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = min_date

# Выбор показателя
metric = st.sidebar.selectbox(
    "Показатель для временного ряда",
    ["avg_temp", "total_precip", "avg_wind"],
    format_func=lambda x: {
        "avg_temp": "Температура (°C)",
        "total_precip": "Осадки (мм)",
        "avg_wind": "Скорость ветра (м/с)"
    }[x]
)

# Окно скользящего среднего
window = st.sidebar.slider("Окно скользящего среднего (дни)", 3, 30, 7)

st.sidebar.markdown("---")
st.sidebar.info(
    "Данные содержат: температуру, осадки, ветер, признак дождя.\n"
    "Добавлены: категория температуры, уровень осадков, комфортность, индекс комфорта."
)


if not selected_cities:
    st.warning("Выберите хотя бы один город в боковой панели.")
    st.stop()

# ФИЛЬТРАЦИЯ ДАННЫХ
filtered = df[df["city"].isin(selected_cities)]
filtered = filtered[
    (filtered["date"] >= pd.Timestamp(start_date)) &
    (filtered["date"] <= pd.Timestamp(end_date))
    ]

if filtered.empty:
    st.warning("Нет данных для выбранных фильтров. Измените параметры.")
    st.stop()

# ТАБЛИЦА С ДАННЫМи
st.header("Исходные и производные данные")
st.caption("Таблица с возможностью сортировки и постраничного просмотра")

display_cols = [col for col in ["date", "city", "avg_temp", "total_precip", "avg_wind",
                                "is_rainy", "temp_category", "precip_level",
                                "comfort_label", "comfort_index"] if col in filtered.columns]
st.dataframe(filtered[display_cols], use_container_width=True, height=400)

# EDA
st.header("Разведочный анализ данных (EDA)")
tab1, tab2 = st.tabs(["📈 Распределение признаков", "🌍 Сравнение городов"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        if "avg_temp" in filtered.columns:
            fig_hist = px.histogram(
                filtered, x="avg_temp", nbins=30,
                title="Распределение температуры",
                labels={"avg_temp": "°C"},
                color_discrete_sequence=["#1f77b4"]
            )
            st.plotly_chart(fig_hist, use_container_width=True)
    with col2:
        if "avg_temp" in filtered.columns:
            fig_box = px.box(
                filtered, y="avg_temp", points="all",
                title="Boxplot температуры",
                labels={"avg_temp": "°C"}
            )
            st.plotly_chart(fig_box, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if "total_precip" in filtered.columns:
            fig_precip = px.histogram(
                filtered, x="total_precip", nbins=30,
                title="Распределение осадков",
                labels={"total_precip": "мм"}
            )
            st.plotly_chart(fig_precip, use_container_width=True)
    with col2:
        if "avg_wind" in filtered.columns:
            fig_wind = px.histogram(
                filtered, x="avg_wind", nbins=30,
                title="Распределение ветра",
                labels={"avg_wind": "м/с"}
            )
            st.plotly_chart(fig_wind, use_container_width=True)

with tab2:
    if len(selected_cities) > 1:
        group = filtered.groupby("city")[["avg_temp", "total_precip", "avg_wind"]].mean().reset_index()
        fig_bar = px.bar(
            group, x="city", y=["avg_temp", "total_precip", "avg_wind"],
            barmode="group",
            title="Средние показатели по городам",
            labels={"value": "Значение", "variable": "Показатель", "city": "Город"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("💡 Выберите несколько городов в боковой панели для сравнения.")

# Скользящее окно
st.header("Динамика и прогноз (скользящее среднее)")

fig_time = go.Figure()
for city in selected_cities:
    city_df = filtered[filtered["city"] == city].sort_values("date")
    if len(city_df) > 0 and metric in city_df.columns:
        # Фактические данные
        fig_time.add_trace(go.Scatter(
            x=city_df["date"], y=city_df[metric],
            mode="lines+markers",
            name=f"{city} (факт)",
            line=dict(width=2)
        ))
        # Скользящее среднее
        ma = city_df[metric].rolling(window=window, min_periods=1).mean()
        fig_time.add_trace(go.Scatter(
            x=city_df["date"], y=ma,
            mode="lines",
            name=f"{city} (MA{window})",
            line=dict(dash="dash", width=2)
        ))

y_labels = {
    "avg_temp": "Температура (°C)",
    "total_precip": "Осадки (мм)",
    "avg_wind": "Ветер (м/с)"
}
fig_time.update_layout(
    title=f"Динамика {y_labels[metric]} и скользящее среднее (окно={window} дня)",
    xaxis_title="Дата",
    yaxis_title=y_labels[metric],
    legend_title="Город / тип"
)
st.plotly_chart(fig_time, use_container_width=True)
st.caption("💡 Прогноз основан на скользящем среднем — показывает общий тренд, сглаживая краткосрочные колебания.")

# ДОП ЗАДАНИЕ - ИНДЕКС КОМФОРТА
if "comfort_index" in df.columns:
    st.header("😌 Индекс комфорта")
    st.caption("Чем выше значение — тем комфортнее погода. Формула: -осадки×3 -ветер×0.7 -|температура-20|×0.6")

    fig_comfort = px.line(
        filtered,
        x="date",
        y="comfort_index",
        color="city",
        title=f"Индекс комфорта по городам (чем выше — тем комфортнее)",
        labels={"comfort_index": "Индекс комфорта", "date": "Дата", "city": "Город"},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    st.plotly_chart(fig_comfort, use_container_width=True)

# Интерактив
st.header("📊 Интерактивные метрики")

agg_type = st.radio("🔄 Агрегация по периоду", ("День", "Неделя", "Месяц"), horizontal=True)
freq = {"День": "D", "Неделя": "W", "Месяц": "M"}[agg_type]

if freq != "D" and not filtered.empty:
    filtered_resample = filtered.set_index("date").groupby("city").resample(freq).agg({
        "avg_temp": "mean",
        "total_precip": "sum",
        "avg_wind": "mean",
        "is_rainy": "mean"
    }).reset_index()
else:
    filtered_resample = filtered.copy()

if not filtered_resample.empty and "avg_temp" in filtered_resample.columns:
    fig_agg = px.line(
        filtered_resample, x="date", y="avg_temp", color="city",
        title=f"Средняя температура ({agg_type})",
        labels={"avg_temp": "°C", "date": "Дата"}
    )
    st.plotly_chart(fig_agg, use_container_width=True)

# СВОДНАЯ СТАТИСТИКА
st.subheader("Сводная статистика")
col1, col2, col3, col4 = st.columns(4)

col1.metric("🌡️ Средняя температура", f"{filtered['avg_temp'].mean():.1f}°C")
col2.metric("💧 Сумма осадков", f"{filtered['total_precip'].sum():.1f} мм")
col3.metric("💨 Средний ветер", f"{filtered['avg_wind'].mean():.1f} м/с")
col4.metric("☔ Доля дождливых дней", f"{filtered['is_rainy'].mean():.1%}")

# === МЕТРИКА ИНДЕКСА КОМФОРТА (если есть) ===
if "comfort_index" in filtered.columns:
    col5, col6 = st.columns(2)
    avg_comfort = filtered["comfort_index"].mean()
    max_comfort = filtered["comfort_index"].max()
    col5.metric("😊 Средний комфорт", f"{avg_comfort:.1f}")
    col6.metric("🏆 Макс. комфорт", f"{max_comfort:.1f}")

st.markdown("---")
st.success(
    "Приложение использует реальные данные из weather.db. Меняйте фильтры — графики обновляются автоматически.")


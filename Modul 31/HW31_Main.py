# streamlit run HW31_Main.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# Конфигурация страницы
st.set_page_config(page_title="CSV Анализатор", layout="wide", page_icon=" ")
st.title(" Универсальный анализатор CSV-данных")

# 1. Загрузка и парсинг данных (БЕЗ кеширования для обхода ошибки pickle)
def parse_csv(file):
    """Загружает CSV, подбирает кодировку и парсит только явные даты."""
    encodings = ["utf-8", "cp1251", "latin1", "iso-8859-1"]
    for enc in encodings:
        try:
            df = pd.read_csv(file, encoding=enc, sep=';')
            break
        except UnicodeDecodeError:
            continue
    else:
        st.error(" Не удалось определить кодировку файла.")
        return None

    # Парсим только столбцы с явными подсказками в названии
    date_keywords = ["date", "time", "datetime", "дата", "время"]
    for col in df.columns:
        if any(kw in col.lower() for kw in date_keywords) and df[col].dtype == "object":
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=False)
            except Exception:
                pass  # Оставляем как строку, если не получилось
    return df


# Загрузчик файла
uploaded_file = st.file_uploader(
    " Загрузите CSV-файл для анализа",
    type=["csv"],
    accept_multiple_files=False,
)

if uploaded_file is not None:
    #  Читаем файл в session_state, чтобы не парсить повторно при каждом реране
    if "df" not in st.session_state or st.session_state.get("file_name") != uploaded_file.name:
        df = parse_csv(uploaded_file)
        if df is not None:
            st.session_state["df"] = df
            st.session_state["file_name"] = uploaded_file.name
            st.success(f" Файл загружен: {df.shape[0]} строк, {df.shape[1]} столбцов")
    df = st.session_state["df"]
else:
    st.info(" Загрузите файл, чтобы начать работу.")
    st.stop()


# 2. Отображение данных
st.subheader(" Предпросмотр таблицы")
st.dataframe(df, use_container_width=True, height=350)

# Разделение типов данных
num_cols = df.select_dtypes(include="number").columns.tolist()
all_cols = df.columns.tolist()
date_cols = df.select_dtypes(include="datetime64").columns.tolist()

# 3. Статистический анализ
st.subheader(" Статистика по столбцу")
stat_col = st.selectbox("Выберите столбец для расчёта статистики:", all_cols)

if stat_col in num_cols:
    col_data = df[stat_col].dropna()
    if len(col_data) > 0:
        c1, c2, c3 = st.columns(3)
        c1.metric("Среднее значение", f"{col_data.mean():.2f}")
        c2.metric("Медиана", f"{col_data.median():.2f}")
        c3.metric("Стандартное отклонение", f"{col_data.std():.2f}")

        # Гистограмма распределения (бонус)
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.hist(col_data, bins="auto", color="#4C72B0", edgecolor="black", alpha=0.7)
        ax.set_title(f"Распределение: {stat_col}")
        ax.set_xlabel(stat_col)
        ax.set_ylabel("Частота")
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    else:
        st.warning(" Столбец пуст или содержит только пропуски (NaN).")
else:
    st.info(" Для расчёта статистики выберите столбец числового типа.")

# 4. Визуализация пар столбцов
st.subheader(" Визуализация зависимости")
c1, c2, c3 = st.columns(3)
with c1:
    x_col = st.selectbox("Ось X", all_cols)
with c2:
    y_col = st.selectbox("Ось Y", all_cols)
with c3:
    plot_type = st.selectbox(
        "Тип графика",
        ["scatter", "line"],
        format_func=lambda x: "Точечная диаграмма" if x == "scatter" else "Линейный график"
    )

if x_col and y_col and x_col != y_col:
    plot_df = df[[x_col, y_col]].dropna()

    if len(plot_df) >= 2:
        # Проверка: хотя бы один столбец должен быть числовым или датой
        x_numeric = pd.api.types.is_numeric_dtype(plot_df[x_col]) or pd.api.types.is_datetime64_any_dtype(
            plot_df[x_col])
        y_numeric = pd.api.types.is_numeric_dtype(plot_df[y_col]) or pd.api.types.is_datetime64_any_dtype(
            plot_df[y_col])

        if x_numeric and y_numeric:
            # Для линейного графика сортируем по оси X, если это число или дата
            if plot_type == "line" and (
                    pd.api.types.is_numeric_dtype(plot_df[x_col]) or pd.api.types.is_datetime64_any_dtype(
                    plot_df[x_col])):
                plot_df = plot_df.sort_values(by=x_col)

            # Используем нативные компоненты Streamlit для надёжности
            if plot_type == "scatter":
                st.scatter_chart(plot_df, x=x_col, y=y_col, use_container_width=True)
            else:
                st.line_chart(plot_df.set_index(x_col)[y_col], use_container_width=True)

            # Кнопка скачивания графика (бонус)
            fig, ax = plt.subplots(figsize=(7, 4))
            if plot_type == "scatter":
                ax.scatter(plot_df[x_col], plot_df[y_col], alpha=0.7, edgecolor="w", s=50)
            else:
                ax.plot(plot_df[x_col], plot_df[y_col], marker="o", linestyle="-", linewidth=1)
            ax.set_title(f"{y_col} от {x_col}")
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis="x", rotation=45)
            plt.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
            plt.close(fig)

            st.download_button(
                label=" Скачать график (PNG)",
                data=buf.getvalue(),
                file_name=f"plot_{x_col}_vs_{y_col}.png",
                mime="image/png",
            )
        else:
            st.warning(" Для построения графика хотя бы один столбец должен быть числового типа или datetime.")
    else:
        st.warning(" Недостаточно валидных данных (много пропусков или <2 точек).")
else:
    st.info(" Выберите два разных столбца для построения графика.")





import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Кредитный калькулятор", layout="wide")

st.title("Кредитный калькулятор")

# Ввод данных в боковой панели
with st.sidebar:
    st.header("Параметры кредита")

    amount = st.number_input("Сумма кредита (₽)", min_value=0.0, value=100000.0, step=1000.0)
    rate = st.number_input("Процентная ставка (% годовых)", min_value=0.0, value=10.0, step=0.1)
    term = st.number_input("Срок кредита (месяцев)", min_value=1, value=12, step=1)

    payment_type = st.radio(
        "Тип платежа",
        options=["Аннуитетный", "Дифференцированный"],
        help="Аннуитетный — равные платежи. Дифференцированный — уменьшающиеся платежи."
    )

    first_date = st.date_input("Дата первого платежа", value=datetime.now())

# Проверка ввода
if amount <= 0 or rate <= 0:
    st.error("Пожалуйста, введите корректную сумму и процентную ставку.")
    st.stop()

# Расчетне
monthly_rate = rate / 100 / 12
data = []
balance_start = amount

st.subheader(f"График платежей: {payment_type}")

if payment_type == "Аннуитетный":
    # Формула аннуитета: A = P * (r * (1+r)^n) / ((1+r)^n - 1)
    annuity_payment = amount * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)

    for i in range(term):
        interest_part = balance_start * monthly_rate
        debt_part = annuity_payment - interest_part
        balance_end = balance_start - debt_part

        # Обработка микро-остатков из-за точности float
        if i == term - 1:
            balance_end = 0

        data.append({
            "Дата": (first_date + relativedelta(months=i)).strftime("%d.%m.%Y"),
            "Остаток в начале (₽)": round(balance_start, 2),
            "Платеж (₽)": round(annuity_payment, 2),
            "Проценты (₽)": round(interest_part, 2),
            "Основной долг (₽)": round(debt_part, 2),
            "Остаток в конце (₽)": round(max(0, balance_end), 2)
        })
        balance_start = balance_end

else:  # Дифференцированный
    fixed_debt_part = amount / term

    for i in range(term):
        interest_part = balance_start * monthly_rate
        monthly_payment = fixed_debt_part + interest_part
        balance_end = balance_start - fixed_debt_part

        data.append({
            "Дата": (first_date + relativedelta(months=i)).strftime("%d.%m.%Y"),
            "Остаток в начале (₽)": round(balance_start, 2),
            "Платеж (₽)": round(monthly_payment, 2),
            "Проценты (₽)": round(interest_part, 2),
            "Основной долг (₽)": round(fixed_debt_part, 2),
            "Остаток в конце (₽)": round(max(0, balance_end), 2)
        })
        balance_start = balance_end


df = pd.DataFrame(data)

total_payout = df["Платеж (₽)"].sum()
overpayment = total_payout - amount

col1, col2, col3 = st.columns(3)
col1.metric("Ежемесячный платеж",
            f"{df['Платеж (₽)'].iloc[0]:,.2f} ₽" if payment_type == "Аннуитетный" else "Убывающий")
col2.metric("Общая выплата", f"{total_payout:,.2f} ₽")
col3.metric("Переплата", f"{overpayment:,.2f} ₽", delta_color="inverse")

# Отображение таблицы
with st.expander("Посмотреть подробную таблицу платежей", expanded=True):
    st.dataframe(df, use_container_width=True, hide_index=True)

# Кнопка сброса
if st.button("Сбросить расчеты"):
    st.rerun()

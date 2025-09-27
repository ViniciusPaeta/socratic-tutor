"""
Streamlit dashboard for Socratic Tutor metrics (MVP).

Shows:
- Total steps
- Completion rate (global / por aluno / por problema)
- Top error labels
"""

import sqlite3

import pandas as pd
import streamlit as st


def get_conn(db_path: str = "metrics.sqlite3") -> sqlite3.Connection:
    return sqlite3.connect(db_path)


@st.cache_data(ttl=5)
def load_df(db_path: str = "metrics.sqlite3") -> pd.DataFrame:
    con = get_conn(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM steps", con)
    except Exception:
        df = pd.DataFrame(columns=["ts", "problem_id", "student", "ok", "error_type"])
    finally:
        con.close()
    return df


st.set_page_config(page_title="Socratic Tutor — Metrics", layout="wide")
st.title("📊 Socratic Tutor — Metrics (MVP)")

db_path = st.sidebar.text_input("SQLite path", "metrics.sqlite3")

df = load_df(db_path)
st.sidebar.write(f"Rows: {len(df)}")

if df.empty:
    st.info("No data yet. Use the CLI to record steps.")
    st.stop()

# Global KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total steps", len(df))
with col2:
    ok_rate = (df["ok"].astype(int).sum() / len(df)) if len(df) else 0
    st.metric("Completion rate (steps OK)", f"{100*ok_rate:.1f}%")
with col3:
    st.metric("Distinct students", df["student"].nunique())

st.subheader("Top error labels")
err = df[df["ok"] == 0]["error_type"].value_counts().reset_index()
err.columns = ["error_type", "count"]
st.dataframe(err, use_container_width=True)

st.subheader("By student")
by_student = df.groupby("student")["ok"].mean().reset_index().sort_values("ok", ascending=False)
by_student["ok"] = (100 * by_student["ok"]).round(1)
by_student.columns = ["student", "OK rate (%)"]
st.dataframe(by_student, use_container_width=True)

st.subheader("By problem")
by_problem = df.groupby("problem_id")["ok"].mean().reset_index().sort_values("ok", ascending=False)
by_problem["ok"] = (100 * by_problem["ok"]).round(1)
by_problem.columns = ["problem_id", "OK rate (%)"]
st.dataframe(by_problem, use_container_width=True)

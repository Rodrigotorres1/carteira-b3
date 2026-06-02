import streamlit as st
from supabase import Client, create_client

USER_ID = "default_user"


@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def carregar_dados() -> dict:
    try:
        supabase = get_supabase_client()
        result = supabase.table("carteiras").select("dados").eq("user_id", USER_ID).execute()
        if result.data:
            return result.data[0]["dados"]
        return {}
    except Exception as e:
        st.warning(f"Erro ao carregar dados: {e}")
        return {}


def salvar_dados(dados: dict) -> bool:
    try:
        supabase = get_supabase_client()
        supabase.table("carteiras").upsert({
            "user_id": USER_ID,
            "dados": dados,
            "updated_at": "now()",
        }).execute()
        return True
    except Exception as e:
        st.warning(f"Erro ao salvar dados: {e}")
        return False

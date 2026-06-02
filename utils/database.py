import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_user_id() -> str | None:
    user = st.session_state.get("user")
    if user is not None:
        return user.id
    return None


def is_authenticated() -> bool:
    return get_user_id() is not None


def login(email: str, password: str) -> dict:
    try:
        supabase = get_supabase_client()
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"]    = result.user
        st.session_state["session"] = result.session
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def signup(email: str, password: str) -> dict:
    try:
        supabase = get_supabase_client()
        result = supabase.auth.sign_up({"email": email, "password": password})
        return {"success": True, "user": result.user}
    except Exception as e:
        return {"success": False, "error": str(e)}


def logout() -> None:
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.pop("user", None)
    st.session_state.pop("session", None)


def carregar_dados() -> dict:
    user_id = get_user_id()
    if not user_id:
        return {}
    try:
        supabase = get_supabase_client()
        result = supabase.table("carteiras").select("dados").eq("user_id", user_id).execute()
        if result.data:
            return result.data[0]["dados"]
        return {}
    except Exception as e:
        st.warning(f"Erro ao carregar dados: {e}")
        return {}


def recuperar_sessao_url() -> bool:
    try:
        supabase = get_supabase_client()
        session = supabase.auth.get_session()
        if session and session.user:
            st.session_state["user"]    = session.user
            st.session_state["session"] = session
            return True
        return False
    except Exception:
        return False


def salvar_dados(dados: dict) -> bool:
    user_id = get_user_id()
    if not user_id:
        return False
    try:
        supabase = get_supabase_client()
        supabase.table("carteiras").upsert({
            "user_id": user_id,
            "dados": dados,
            "updated_at": "now()",
        }, on_conflict="user_id").execute()
        return True
    except Exception as e:
        st.warning(f"Erro ao salvar dados: {e}")
        return False

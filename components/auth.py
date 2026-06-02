import streamlit as st

from utils.database import get_supabase_client, login, signup


def get_google_login_url() -> str | None:
    try:
        supabase = get_supabase_client()
        result = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": "https://carteira-b3.streamlit.app"},
        })
        return result.url
    except Exception:
        return None


def render_login() -> None:
    st.title("Carteira B3")
    st.caption("Gerencie seus investimentos com inteligência.")

    st.divider()

    google_url = get_google_login_url()
    if google_url:
        st.link_button("Entrar com Google", google_url, use_container_width=True)
        st.divider()

    tab_login, tab_signup = st.tabs(["Entrar", "Criar conta"])

    with tab_login:
        with st.form("form_login"):
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)

            if submit:
                if not email or not senha:
                    st.error("Preencha email e senha.")
                else:
                    with st.spinner("Entrando..."):
                        result = login(email, senha)
                    if result["success"]:
                        st.rerun()
                    else:
                        erro = result["error"]
                        if "Invalid" in erro or "invalid" in erro:
                            st.error("Email ou senha incorretos.")
                        elif "Email not confirmed" in erro:
                            st.warning(
                                "Confirme seu email antes de entrar. "
                                "Verifique sua caixa de entrada."
                            )
                        else:
                            st.error(f"Erro ao entrar: {erro}")

    with tab_signup:
        with st.form("form_signup"):
            email_new    = st.text_input("Email")
            senha_new    = st.text_input("Senha", type="password", help="Mínimo 6 caracteres")
            senha_confirm = st.text_input("Confirmar senha", type="password")
            submit_new   = st.form_submit_button("Criar conta", use_container_width=True)

            if submit_new:
                if not email_new or not senha_new:
                    st.error("Preencha todos os campos.")
                elif senha_new != senha_confirm:
                    st.error("As senhas não coincidem.")
                elif len(senha_new) < 6:
                    st.error("A senha precisa ter pelo menos 6 caracteres.")
                else:
                    with st.spinner("Criando conta..."):
                        result = signup(email_new, senha_new)
                    if result["success"]:
                        st.success(
                            "Conta criada! Verifique seu email para confirmar "
                            "o cadastro antes de entrar."
                        )
                    else:
                        st.error(f"Erro ao criar conta: {result['error']}")

    st.divider()
    st.caption("Seus dados são privados e isolados por usuário.")

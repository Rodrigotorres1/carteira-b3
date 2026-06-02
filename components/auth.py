import streamlit as st

from utils.database import login, signup


def render_nova_senha() -> None:
    st.title("Carteira B3")
    st.subheader("Definir nova senha")

    with st.form("form_nova_senha"):
        nova_senha = st.text_input("Nova senha", type="password", help="Mínimo 6 caracteres")
        confirmar  = st.text_input("Confirmar nova senha", type="password")
        submit     = st.form_submit_button("Salvar nova senha", use_container_width=True)

        if submit:
            if not nova_senha or not confirmar:
                st.error("Preencha todos os campos.")
            elif len(nova_senha) < 6:
                st.error("A senha precisa ter pelo menos 6 caracteres.")
            elif nova_senha != confirmar:
                st.error("As senhas não coincidem.")
            else:
                from utils.database import atualizar_senha
                with st.spinner("Salvando..."):
                    result = atualizar_senha(nova_senha)
                if result["success"]:
                    st.success("Senha atualizada com sucesso!")
                    st.session_state.pop("recovery_mode", None)
                    st.rerun()
                else:
                    st.error(f"Erro ao atualizar senha: {result['error']}")


def render_login() -> None:
    st.title("Carteira B3")
    st.caption("Gerencie seus investimentos com inteligência.")

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

        st.divider()

        with st.expander("Esqueci minha senha"):
            with st.form("form_reset"):
                email_reset  = st.text_input("Digite seu email cadastrado")
                submit_reset = st.form_submit_button(
                    "Enviar link de redefinição", use_container_width=True
                )

                if submit_reset:
                    if not email_reset:
                        st.error("Digite seu email.")
                    else:
                        from utils.database import resetar_senha
                        with st.spinner("Enviando..."):
                            result = resetar_senha(email_reset)
                        if result["success"]:
                            st.success(
                                "Email enviado! Verifique sua caixa "
                                "de entrada e clique no link para "
                                "redefinir sua senha."
                            )
                        else:
                            st.error(
                                "Erro ao enviar email. "
                                "Verifique se o email está correto."
                            )

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

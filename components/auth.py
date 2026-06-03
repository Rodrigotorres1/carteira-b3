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

        if "reset_email" not in st.session_state:
            with st.expander("Esqueci minha senha"):
                with st.form("form_reset_email"):
                    email_reset = st.text_input("Seu email cadastrado")
                    submit_reset = st.form_submit_button("Enviar código", use_container_width=True)

                    if submit_reset and email_reset:
                        from utils.database import enviar_otp_reset
                        with st.spinner("Enviando..."):
                            result = enviar_otp_reset(email_reset)
                        if result["success"]:
                            st.session_state["reset_email"] = email_reset
                            st.rerun()
                        else:
                            st.error("Email não encontrado.")
        else:
            with st.expander("Esqueci minha senha", expanded=True):
                st.info(f"Código enviado para {st.session_state['reset_email']}")

                with st.form("form_reset_codigo"):
                    codigo     = st.text_input("Código recebido no email",
                                               help="Digite o código de 6 dígitos")
                    nova_senha = st.text_input("Nova senha", type="password")
                    confirmar  = st.text_input("Confirmar senha", type="password")

                    col1, col2 = st.columns(2)
                    with col1:
                        submit   = st.form_submit_button("Confirmar", use_container_width=True)
                    with col2:
                        cancelar = st.form_submit_button("Cancelar", use_container_width=True)

                    if cancelar:
                        st.session_state.pop("reset_email", None)
                        st.rerun()

                    if submit:
                        if not codigo or not nova_senha:
                            st.error("Preencha todos os campos.")
                        elif nova_senha != confirmar:
                            st.error("As senhas não coincidem.")
                        elif len(nova_senha) < 6:
                            st.error("Mínimo 6 caracteres.")
                        else:
                            from utils.database import login as fazer_login, verificar_otp_e_atualizar_senha
                            teste_senha_antiga = fazer_login(st.session_state["reset_email"], nova_senha)
                            if teste_senha_antiga["success"]:
                                st.error("A nova senha não pode ser igual à senha atual.")
                            else:
                                with st.spinner("Verificando..."):
                                    result = verificar_otp_e_atualizar_senha(
                                        st.session_state["reset_email"], codigo, nova_senha
                                    )
                                if result["success"]:
                                    st.success("Senha atualizada!")
                                    st.session_state.pop("reset_email", None)
                                    st.rerun()
                                else:
                                    st.error("Código inválido ou expirado.")

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
                        erro = result["error"]
                        if "rate limit" in erro.lower() or "429" in erro:
                            st.error("Muitas tentativas de cadastro. Tente novamente em alguns minutos.")
                        elif "already registered" in erro.lower():
                            st.error("Este email já possui uma conta cadastrada.")
                        else:
                            st.error(f"Erro ao criar conta: {erro}")

    st.divider()
    st.caption("Seus dados são privados e isolados por usuário.")

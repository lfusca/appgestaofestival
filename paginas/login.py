import streamlit as st

def show():
    st.title("Tela de Login")

    # Campos de entrada com chaves exclusivas
    usuario = st.text_input("Usuário", key="login_usuario")
    senha = st.text_input("Senha", type="password", key="login_senha")

    # Botão para autenticação
    if st.button("Entrar", key="botao_entrar"):
        # Autenticação simples (substitua por uma lógica real)
        if usuario == "admin" and senha == "1234":
            st.session_state['pagina'] = 'menu'  # Atualiza a página no estado
            st.success("Login realizado com sucesso!")
        else:
            st.error("Usuário ou senha inválidos!")

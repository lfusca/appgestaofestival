import streamlit as st

def show():
    st.title("Alterar Senha")

    # Campos para nova senha
    nova_senha = st.text_input("Nova Senha", type="password", key="nova_senha")
    confirmar_senha = st.text_input("Confirmar Senha", type="password", key="confirmar_senha")

    if st.button("Salvar", key="botao_salvar_senha"):
        if nova_senha == confirmar_senha:
            st.success("Senha alterada com sucesso!")
        else:
            st.error("As senhas não coincidem!")

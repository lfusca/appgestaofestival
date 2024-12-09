import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
DB_URL = os.getenv("DB_URL")

def show():
    st.write("# Cadastro de Jurados")

    # Função para carregar anos para o combobox
    def carregar_anos():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT id_ano FROM tbl_anos;')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        # rows é uma lista de tuplas, ex: [(2024,), (2025,)]
        # Vamos extrair apenas o primeiro elemento de cada tupla para ter uma lista de int
        anos = [r[0] for r in rows]
        return anos

    anos_disponiveis = carregar_anos()

    if not anos_disponiveis:
        st.warning("Não há anos cadastrados. Cadastre um ano primeiro para poder cadastrar jurados.")
    else:
        # Combobox para selecionar o ano
        ano_selecionado = st.selectbox("Selecione o ano para cadastrar e visualizar jurados:", anos_disponiveis)

        # Campos para cadastrar jurado
        nome = st.text_input("Nome do jurado:", key="campo_nome")
        login = st.text_input("Login do jurado:", key="campo_login")
        senha = st.text_input("Senha do jurado:", type="password", key="campo_senha")

        if st.button("Salvar", key="btn_salvar_jurado"):
            if nome and login and senha and ano_selecionado:
                try:
                    conn = psycopg2.connect(DB_URL)
                    cursor = conn.cursor()
                    query = "INSERT INTO tbl_jurados (nome, login, senha, id_ano) VALUES (%s, %s, %s, %s)"
                    cursor.execute(query, (nome, login, senha, int(ano_selecionado)))
                    conn.commit()
                    st.success(f"Jurado '{nome}' inserido com sucesso no ano {ano_selecionado}!")

                except errors.UniqueViolation:
                    st.error(f"Erro: O login '{login}' já existe no banco de dados.")
                except Exception as e:
                    st.error(f"Ocorreu um erro ao inserir o jurado: {e}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
            else:
                st.warning("Por favor, preencha todos os campos e selecione um ano.")

    st.title("Jurados Cadastrados")

    def apagar_jurado(login_jurado):
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        delete_query = "DELETE FROM tbl_jurados WHERE login = %s;"
        cursor.execute(delete_query, (login_jurado,))
        conn.commit()
        cursor.close()
        conn.close()

    def carregar_jurados():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = 'SELECT nome, login, senha, id_ano FROM tbl_jurados;'
        cursor.execute(query)
        rows = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        df = pd.DataFrame(rows, columns=colunas)
        # Converter id_ano para int nativo
        if not df.empty:
            df["id_ano"] = df["id_ano"].apply(lambda x: int(x))
        return df

    # Se há um jurado a apagar no estado, apague antes de carregar os dados
    if 'delete_jurado' in st.session_state:
        apagar_jurado(st.session_state['delete_jurado'])
        del st.session_state['delete_jurado']

    df_jurados = carregar_jurados()

    # Filtra o DataFrame pelo ano selecionado
    if anos_disponiveis:
        df_filtrado = df_jurados[df_jurados["id_ano"] == ano_selecionado]
    else:
        df_filtrado = df_jurados

    if df_filtrado.empty:
        st.write(f"Não há jurados cadastrados para o ano {ano_selecionado}.")
    else:
        # Cabeçalhos da tabela
        col_tit_nome, col_tit_login, col_tit_senha, col_tit_ano, col_tit_acao = st.columns([2,2,2,1,1])
        col_tit_nome.write("**Nome**")
        col_tit_login.write("**Login**")
        col_tit_senha.write("**Senha**")
        col_tit_ano.write("**Ano**")
        col_tit_acao.write("**Ação**")

        # Exibição linha a linha do df_filtrado
        for index, row in df_filtrado.iterrows():
            nome_val = row["nome"]
            login_val = row["login"]
            # senha_val = row["senha"] # não usaremos a senha real
            ano_val = row["id_ano"]

            col_nome, col_login, col_senha, col_ano, col_acao = st.columns([2,2,2,1,1])
            col_nome.write(nome_val)
            col_login.write(login_val)
            # Mostra asteriscos no lugar da senha
            col_senha.write("xxxxxxx")
            col_ano.write(ano_val)

            if col_acao.button("Apagar", key=f"apagar_{login_val}"):
                st.session_state['delete_jurado'] = login_val

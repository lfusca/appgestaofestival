# paginas/cadastro_equipe.py

import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

def show():
    st.write("# Cadastro de Equipes")

    # Carrega as variáveis de ambiente
    load_dotenv()
    DB_URL = os.getenv("DB_URL")

    # Função para carregar anos disponíveis
    def carregar_anos():
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            cursor.execute('SELECT id_ano FROM tbl_anos ORDER BY id_ano;')
            rows = cursor.fetchall()
            anos = [r[0] for r in rows]
        except Exception as e:
            st.error(f"Erro ao carregar anos: {e}")
            anos = []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return anos

    # Função para carregar modalidades por ano
    def carregar_modalidades_por_ano(ano):
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            cursor.execute('SELECT id_modalidade, nome FROM tbl_modalidades WHERE id_ano = %s ORDER BY nome;', (ano,))
            rows = cursor.fetchall()
            modalidades = rows  # (id_modalidade, nome)
        except Exception as e:
            st.error(f"Erro ao carregar modalidades: {e}")
            modalidades = []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return modalidades

    # Função para carregar equipes
    def carregar_equipes():
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            query = '''
                SELECT 
                    id_equipe, 
                    id_modalidade, 
                    nome, 
                    ordem_apresentacao,
                    grau,
                    ficha_tecnica
                FROM tbl_equipes;
            '''
            cursor.execute(query)
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=colunas)
        except Exception as e:
            st.error(f"Erro ao carregar equipes: {e}")
            df = pd.DataFrame()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return df

    # Função para apagar equipe
    def apagar_equipe(id_equipe):
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            delete_query = "DELETE FROM tbl_equipes WHERE id_equipe = %s;"
            cursor.execute(delete_query, (id_equipe,))
            conn.commit()
            st.success("Equipe apagada com sucesso.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao apagar a equipe: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Carregar anos disponíveis
    anos_disponiveis = carregar_anos()

    if not anos_disponiveis:
        st.warning("Não há anos cadastrados. Cadastre um ano primeiro para poder cadastrar equipes.")
    else:
        # Combobox para selecionar o ano
        ano_selecionado = st.selectbox("Selecione o ano para cadastrar e visualizar equipes:", anos_disponiveis)

        # Carregar modalidades para o ano selecionado
        modalidades = carregar_modalidades_por_ano(ano_selecionado)
        if not modalidades:
            st.warning("Não há modalidades cadastradas para o ano selecionado. Cadastre uma modalidade primeiro.")
        else:
            # Criar dicionário de modalidade para fácil acesso
            modalidade_dict = {nome: mid for (mid, nome) in modalidades}
            modalidade_nomes = list(modalidade_dict.keys())

            # Combobox para selecionar modalidade
            modalidade_selecionada_nome = st.selectbox("Selecione a modalidade:", modalidade_nomes)
            id_modalidade_selecionada = modalidade_dict[modalidade_selecionada_nome]

            st.markdown("---")

            # Formulário para cadastrar equipe
            with st.form(key="form_cadastro_equipe"):
                st.write("## Cadastrar Equipe")
                nome_equipe = st.text_input("Nome da equipe:")
                ordem_apresentacao = st.text_input("Ordem de apresentação (número):")
                grau_options = ["Ensino Fundamental", "Ensino Médio"]
                grau_selecionado = st.selectbox("Selecione o grau:", grau_options)
                ficha_tecnica = st.text_area("Ficha Técnica:", height=200)
                submit_button = st.form_submit_button(label="Salvar Equipe")

                if submit_button:
                    # Validação dos campos
                    if nome_equipe and ordem_apresentacao and grau_selecionado and ficha_tecnica:
                        try:
                            ordem_int = int(ordem_apresentacao)
                            if ordem_int <= 0:
                                st.error("Ordem de apresentação deve ser um número positivo.")
                                st.stop()
                        except ValueError:
                            st.error("Ordem de apresentação deve ser um número.")
                            st.stop()

                        try:
                            conn = psycopg2.connect(DB_URL)
                            cursor = conn.cursor()
                            query = """
                                INSERT INTO tbl_equipes 
                                    (nome, ordem_apresentacao, id_modalidade, grau, ficha_tecnica) 
                                VALUES (%s, %s, %s, %s, %s)
                            """
                            cursor.execute(query, (nome_equipe, ordem_int, id_modalidade_selecionada, grau_selecionado, ficha_tecnica))
                            conn.commit()
                            st.success(f"Equipe '{nome_equipe}' inserida com sucesso na modalidade '{modalidade_selecionada_nome}'!")
                            # Limpar os campos após o sucesso
                            st.session_state['nome_equipe'] = ""
                            st.session_state['ordem_apresentacao'] = ""
                            st.session_state['grau_equipe'] = "Ensino Fundamental"
                            st.session_state['ficha_tecnica_equipe'] = ""
                        except errors.UniqueViolation:
                            st.error(f"Erro: A equipe '{nome_equipe}' já existe nessa modalidade.")
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao inserir a equipe: {e}")
                        finally:
                            if cursor:
                                cursor.close()
                            if conn:
                                conn.close()
                    else:
                        st.warning("Por favor, preencha todos os campos.")

            st.markdown("---")
            st.title("Equipes Cadastradas")

            # Apagar equipe se houver
            if 'delete_equipe' in st.session_state:
                apagar_equipe(st.session_state['delete_equipe']['id_equipe'])
                del st.session_state['delete_equipe']

            # Carregar equipes
            df_equipes = carregar_equipes()
            df_filtrado = df_equipes[df_equipes["id_modalidade"] == id_modalidade_selecionada]

            if df_filtrado.empty:
                st.write(f"Não há equipes cadastradas para a modalidade '{modalidade_selecionada_nome}'.")
            else:
                # Cabeçalhos da tabela
                col_tit_nome, col_tit_ordem, col_tit_grau, col_tit_ficha, col_tit_acao = st.columns([2,1,1,3,1])
                col_tit_nome.write("**Nome**")
                col_tit_ordem.write("**Ordem**")
                col_tit_grau.write("**Grau**")
                col_tit_ficha.write("**Ficha Técnica**")
                col_tit_acao.write("**Ação**")

                # Exibir equipes
                for index, row in df_filtrado.iterrows():
                    id_equipe_val = row["id_equipe"]
                    nome_val = row["nome"]
                    ordem_val = row["ordem_apresentacao"]
                    grau_val = row["grau"]
                    ficha_val = row["ficha_tecnica"]

                    col_nome, col_ordem, col_grau, col_ficha, col_acao = st.columns([2,1,1,3,1])
                    col_nome.write(nome_val)
                    col_ordem.write(ordem_val)
                    col_grau.write(grau_val)
                    col_ficha.write(ficha_val)

                    if col_acao.button("Apagar", key=f"apagar_{id_equipe_val}"):
                        st.session_state['delete_equipe'] = {"id_equipe": id_equipe_val}

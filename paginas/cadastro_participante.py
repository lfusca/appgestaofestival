import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

def show():
    st.write("# Cadastro de Participantes")

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

    # Função para carregar equipes por modalidade e grau
    def carregar_equipes_por_modalidade_e_grau(id_modalidade, grau):
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            cursor.execute('SELECT id_equipe, nome FROM tbl_equipes WHERE id_modalidade = %s AND grau = %s ORDER BY nome;', (id_modalidade, grau))
            rows = cursor.fetchall()
            equipes = rows  # (id_equipe, nome)
        except Exception as e:
            st.error(f"Erro ao carregar equipes: {e}")
            equipes = []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return equipes

    # Função para carregar participantes com dados da equipe (incluindo grau)
    def carregar_participantes(grau_filtro):
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            query = '''
                SELECT 
                    p.id_participante, 
                    p.nome, 
                    p.turma, 
                    e.grau, 
                    p.id_equipe 
                FROM tbl_participantes p
                JOIN tbl_equipes e ON p.id_equipe = e.id_equipe
                WHERE LOWER(TRIM(e.grau)) = LOWER(TRIM(%s))
                ORDER BY p.nome;
            '''
            cursor.execute(query, (grau_filtro.strip(),))
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=colunas)
        except Exception as e:
            st.error(f"Erro ao carregar participantes: {e}")
            df = pd.DataFrame()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return df

    # Função para apagar participante
    def apagar_participante(id_participante):
        try:
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            delete_query = "DELETE FROM tbl_participantes WHERE id_participante = %s;"
            cursor.execute(delete_query, (id_participante,))
            conn.commit()
            st.success("Participante apagado com sucesso.")
            # Remover st.stop() para permitir que o script continue executando
        except Exception as e:
            st.error(f"Ocorreu um erro ao apagar o participante: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Inicializa um contador para o form key, para resetar o formulário
    if 'form_counter' not in st.session_state:
        st.session_state['form_counter'] = 0

    # Opções para grau
    grau_options = [
        "Ensino Fundamental",
        "Ensino Médio"
    ]

    # Carregar anos disponíveis
    anos_disponiveis = carregar_anos()

    if not anos_disponiveis:
        st.warning("Não há anos cadastrados. Cadastre um ano primeiro para poder cadastrar participantes.")
    else:
        # Combobox para selecionar o ano
        ano_selecionado = st.selectbox("Selecione o ano para cadastrar e visualizar participantes:", anos_disponiveis)

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

            # Remover a opção "Todos" do filtro de grau
            grau_filtro = st.selectbox("Selecione o grau:", grau_options)

            # Carregar equipes para a modalidade e grau selecionados
            equipes = carregar_equipes_por_modalidade_e_grau(id_modalidade_selecionada, grau_filtro)
            if not equipes:
                st.warning("Não há equipes cadastradas para os critérios selecionados. Cadastre uma equipe primeiro.")
            else:
                # Criar dicionário de equipe para fácil acesso
                equipe_dict = {nome: eid for (eid, nome) in equipes}
                equipe_nomes = list(equipe_dict.keys())

                # Combobox para selecionar equipe
                equipe_selecionada_nome = st.selectbox("Selecione a equipe:", equipe_nomes)
                id_equipe_selecionada = equipe_dict[equipe_selecionada_nome]

                st.markdown("---")

                # Formulário para cadastrar participante
                form_key = f'form_cadastro_participante_{st.session_state["form_counter"]}'
                with st.form(key=form_key):
                    st.write("### Cadastrar Participante")
                    nome_participante = st.text_input("Nome do participante:", max_chars=100)
                    turma_participante = st.text_input("Turma do participante:", max_chars=50)
                    # Remover o campo 'grau_participante'
                    submit_button = st.form_submit_button(label='Salvar Participante')

                    if submit_button:
                        if nome_participante.strip() and turma_participante.strip() and id_equipe_selecionada:
                            try:
                                conn = psycopg2.connect(DB_URL)
                                cursor = conn.cursor()
                                # Inserir sem o campo 'grau'
                                query = "INSERT INTO tbl_participantes (nome, turma, id_equipe) VALUES (%s, %s, %s)"
                                cursor.execute(query, (nome_participante.strip(), turma_participante.strip(), id_equipe_selecionada))
                                conn.commit()
                                st.success(f"Participante '{nome_participante}' inserido com sucesso na equipe '{equipe_selecionada_nome}'!")

                                # Incrementar o contador para resetar o formulário
                                st.session_state['form_counter'] += 1
                            except errors.UniqueViolation:
                                st.error(f"Erro: O participante '{nome_participante}' já existe nesta equipe.")
                            except Exception as e:
                                st.error(f"Ocorreu um erro ao inserir o participante: {e}")
                            finally:
                                if cursor:
                                    cursor.close()
                                if conn:
                                    conn.close()
                        else:
                            st.warning("Por favor, preencha todos os campos corretamente.")

                st.markdown("---")
                st.title("Participantes Cadastrados")

                # Apagar participante se houver
                if 'delete_participante' in st.session_state:
                    apagar_participante(st.session_state['delete_participante']['id_participante'])
                    del st.session_state['delete_participante']
                    # Incrementar o contador para atualizar a lista
                    st.session_state['form_counter'] += 1

                # Carregar participantes com base no filtro de grau
                df_participantes = carregar_participantes(grau_filtro)

                # Filtrar participantes pela equipe selecionada
                df_filtrado = df_participantes[df_participantes["id_equipe"] == id_equipe_selecionada]

                if df_filtrado.empty:
                    st.write(f"Não há participantes cadastrados para a equipe '{equipe_selecionada_nome}'.")
                else:
                    # Cabeçalhos da tabela, exibindo 'Grau da Equipe'
                    col_tit_nome, col_tit_turma, col_tit_grau, col_tit_acao = st.columns([2,2,1,1])
                    col_tit_nome.write("**Nome**")
                    col_tit_turma.write("**Turma**")
                    col_tit_grau.write("**Grau da Equipe**")
                    col_tit_acao.write("**Ação**")

                    # Exibir participantes
                    for index, row in df_filtrado.iterrows():
                        id_participante_val = row["id_participante"]
                        nome_val = row["nome"]
                        turma_val = row["turma"]
                        grau_val = row["grau"]  # Obtido via JOIN com tbl_equipes

                        col_nome, col_turma, col_grau, col_acao = st.columns([2,2,1,1])
                        col_nome.write(nome_val)
                        col_turma.write(turma_val)
                        col_grau.write(grau_val)

                        if col_acao.button("Apagar", key=f"apagar_{id_participante_val}"):
                            st.session_state['delete_participante'] = {"id_participante": id_participante_val}

import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

def show():
    st.write("# Controle das Votações")
    
    # Carrega as variáveis de ambiente
    load_dotenv()
    DB_URL = os.getenv("DB_URL")
    
    # Função para conectar ao banco de dados
    def get_connection():
        try:
            conn = psycopg2.connect(DB_URL)
            return conn
        except Exception as e:
            st.error(f"Erro na conexão com o banco de dados: {e}")
            return None
    
    # Função para carregar anos disponíveis
    def carregar_anos():
        try:
            conn = get_connection()
            if not conn:
                return []
            cursor = conn.cursor()
            cursor.execute('SELECT id_ano FROM tbl_anos ORDER BY id_ano;')
            rows = cursor.fetchall()
            anos = [r[0] for r in rows]
            return anos
        except Exception as e:
            st.error(f"Erro ao carregar anos: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para carregar modalidades por ano
    def carregar_modalidades(ano):
        try:
            conn = get_connection()
            if not conn:
                return []
            cursor = conn.cursor()
            cursor.execute('SELECT id_modalidade, nome FROM tbl_modalidades WHERE id_ano = %s ORDER BY nome;', (ano,))
            rows = cursor.fetchall()
            modalidades = rows  # (id_modalidade, nome)
            return modalidades
        except Exception as e:
            st.error(f"Erro ao carregar modalidades: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para carregar graus disponíveis
    def carregar_graus():
        # Supondo que os graus são fixos conforme o seu exemplo
        return ["Ensino Fundamental", "Ensino Médio"]
    
    # Função para carregar equipes com base nos filtros (corrigido)
    def carregar_equipes(id_modalidade, grau):
        try:
            conn = get_connection()
            if not conn:
                return pd.DataFrame()
            cursor = conn.cursor()
            query = '''
                SELECT 
                    id_equipe, 
                    nome, 
                    ordem_apresentacao, 
                    status_votacao 
                FROM tbl_equipes 
                WHERE id_modalidade = %s AND LOWER(grau) = LOWER(%s)
                ORDER BY ordem_apresentacao;
            '''
            cursor.execute(query, (id_modalidade, grau))
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=colunas)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar equipes: {e}")
            return pd.DataFrame()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para carregar participantes de uma equipe
    def carregar_participantes(id_equipe):
        try:
            conn = get_connection()
            if not conn:
                return pd.DataFrame()
            cursor = conn.cursor()
            query = '''
                SELECT 
                    p.nome, 
                    p.turma 
                FROM tbl_participantes p
                WHERE p.id_equipe = %s
                ORDER BY p.nome;
            '''
            cursor.execute(query, (id_equipe,))
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(rows, columns=colunas)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar participantes: {e}")
            return pd.DataFrame()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para carregar jurados de um ano
    def carregar_jurados(id_ano):
        try:
            conn = get_connection()
            if not conn:
                return []
            cursor = conn.cursor()
            query = '''
                SELECT id_jurado, nome 
                FROM tbl_jurados 
                WHERE id_ano = %s
                ORDER BY nome;
            '''
            cursor.execute(query, (id_ano,))
            rows = cursor.fetchall()
            jurados = rows  # (id_jurado, nome)
            return jurados
        except Exception as e:
            st.error(f"Erro ao carregar jurados: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para carregar critérios de uma modalidade e ano
    def carregar_criterios(id_modalidade):
        try:
            conn = get_connection()
            if not conn:
                return []
            cursor = conn.cursor()
            query = '''
                SELECT id_criterio, nome 
                FROM tbl_criterios 
                WHERE id_modalidade = %s
                ORDER BY nome;
            '''
            cursor.execute(query, (id_modalidade,))
            rows = cursor.fetchall()
            criterios = rows  # (id_criterio, nome)
            return criterios
        except Exception as e:
            st.error(f"Erro ao carregar critérios: {e}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para iniciar votação
    def iniciar_votacao(id_ano, id_modalidade, id_equipe):
        try:
            conn = get_connection()
            if not conn:
                return
            cursor = conn.cursor()
            # Atualizar status_votacao para 'votando'
            update_query = '''
                UPDATE tbl_equipes 
                SET status_votacao = 'votando' 
                WHERE id_equipe = %s;
            '''
            cursor.execute(update_query, (id_equipe,))
            
            # Obter jurados e critérios
            jurados = carregar_jurados(id_ano)
            criterios = carregar_criterios(id_modalidade)
            
            # Inserir registros na tbl_notas
            insert_query = '''
                INSERT INTO tbl_notas (status, nota, id_ano, id_modalidade, id_equipe, id_jurado, id_criterio)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            '''
            for jurado in jurados:
                id_jurado, nome_jurado = jurado
                for criterio in criterios:
                    id_criterio, nome_criterio = criterio
                    cursor.execute(insert_query, ('liberado', None, id_ano, id_modalidade, id_equipe, id_jurado, id_criterio))
            
            conn.commit()
            st.success("Votação iniciada com sucesso para a equipe.")
            st.experimental_rerun()  # Força a atualização da página após iniciar a votação
        except Exception as e:
            st.error(f"Erro ao iniciar votação: {e}")
            conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para resetar votação
    def resetar_votacao(id_equipe):
        try:
            conn = get_connection()
            if not conn:
                return
            cursor = conn.cursor()
            # Atualizar status_votacao para 'aguardando'
            update_query = '''
                UPDATE tbl_equipes 
                SET status_votacao = 'aguardando' 
                WHERE id_equipe = %s;
            '''
            cursor.execute(update_query, (id_equipe,))
            
            # Deletar registros na tbl_notas
            delete_query = '''
                DELETE FROM tbl_notas 
                WHERE id_equipe = %s;
            '''
            cursor.execute(delete_query, (id_equipe,))
            
            conn.commit()
            st.success("Votação resetada com sucesso para a equipe.")
            st.experimental_rerun()  # Força a atualização da página após resetar a votação
        except Exception as e:
            st.error(f"Erro ao resetar votação: {e}")
            conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para adicionar jurado a uma equipe (inserir na tbl_notas)
    def adicionar_jurado(id_ano, id_modalidade, id_equipe, id_jurado):
        try:
            conn = get_connection()
            if not conn:
                return
            cursor = conn.cursor()
            
            # Verificar se já existe registro para o jurado e critérios
            criterios = carregar_criterios(id_modalidade)
            insert_query = '''
                INSERT INTO tbl_notas (status, nota, id_ano, id_modalidade, id_equipe, id_jurado, id_criterio)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            '''
            for criterio in criterios:
                id_criterio, nome_criterio = criterio
                # Evitar duplicatas
                check_query = '''
                    SELECT COUNT(*) 
                    FROM tbl_notas 
                    WHERE id_equipe = %s AND id_jurado = %s AND id_criterio = %s;
                '''
                cursor.execute(check_query, (id_equipe, id_jurado, id_criterio))
                count = cursor.fetchone()[0]
                if count == 0:
                    cursor.execute(insert_query, ('liberado', None, id_ano, id_modalidade, id_equipe, id_jurado, id_criterio))
            
            conn.commit()
            st.success("Jurado adicionado com sucesso à equipe.")
            st.experimental_rerun()  # Força a atualização da página após adicionar um jurado
        except Exception as e:
            st.error(f"Erro ao adicionar jurado: {e}")
            conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Função para bloquear ou liberar jurado
    def alternar_status_jurado(id_equipe, id_jurado, status_atual):
        try:
            # Converter para int se necessário
            if isinstance(id_equipe, (pd._libs.tslibs.nattype.NaTType,)):
                st.error("id_equipe inválido.")
                return
            if isinstance(id_jurado, (pd._libs.tslibs.nattype.NaTType,)):
                st.error("id_jurado inválido.")
                return
            
            id_equipe = int(id_equipe)
            id_jurado = int(id_jurado)
            
            conn = get_connection()
            if not conn:
                return
            cursor = conn.cursor()
            
            if status_atual.lower() == 'liberado':
                # Bloquear: atualizar status para 'bloqueado' e limpar 'nota'
                update_query = '''
                    UPDATE tbl_notas 
                    SET status = 'bloqueado', nota = NULL 
                    WHERE id_equipe = %s AND id_jurado = %s;
                '''
                cursor.execute(update_query, (id_equipe, id_jurado))
                conn.commit()
                st.success("Juror bloqueado com sucesso.")
            elif status_atual.lower() == 'bloqueado':
                # Liberar: atualizar status para 'liberado' (mantendo 'nota' como NULL)
                update_query = '''
                    UPDATE tbl_notas 
                    SET status = 'liberado' 
                    WHERE id_equipe = %s AND id_jurado = %s;
                '''
                cursor.execute(update_query, (id_equipe, id_jurado))
                conn.commit()
                st.success("Juror liberado com sucesso.")
            else:
                st.warning("Status desconhecido.")
            
            st.experimental_rerun()  # Força a atualização da página após a alteração
        except Exception as e:
            st.error(f"Erro ao alternar status do jurado: {e}")
            conn.rollback()
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                conn.close()
    
    # Inicializa estados de sessão para ações
    if 'action' not in st.session_state:
        st.session_state['action'] = {}
    
    # Carregar anos disponíveis
    anos_disponiveis = carregar_anos()
    
    if not anos_disponiveis:
        st.warning("Não há anos cadastrados. Cadastre um ano primeiro.")
        return
    else:
        # Combobox para selecionar o ano
        ano_selecionado = st.selectbox("Selecione o Ano:", anos_disponiveis)
    
    # Carregar modalidades para o ano selecionado
    modalidades = carregar_modalidades(ano_selecionado)
    
    if not modalidades:
        st.warning("Não há modalidades cadastradas para o ano selecionado.")
        return
    else:
        # Criar dicionário de modalidade para fácil acesso
        modalidade_dict = {nome: mid for (mid, nome) in modalidades}
        modalidade_nomes = list(modalidade_dict.keys())
    
        # Combobox para selecionar modalidade
        modalidade_selecionada_nome = st.selectbox("Selecione a Modalidade:", modalidade_nomes)
        id_modalidade_selecionada = modalidade_dict[modalidade_selecionada_nome]
    
    # Carregar graus disponíveis
    graus_disponiveis = carregar_graus()
    
    # Combobox para selecionar grau
    grau_selecionado = st.selectbox("Selecione o Grau:", graus_disponiveis)
    
    st.markdown("---")
    
    # Carregar equipes com base nos filtros (corrigido)
    equipes_df = carregar_equipes(id_modalidade_selecionada, grau_selecionado)
    
    if equipes_df.empty:
        st.info("Não há equipes cadastradas para os filtros selecionados.")
    else:
        for index, equipe in equipes_df.iterrows():
            id_equipe = equipe['id_equipe']
            nome_equipe = equipe['nome']
            ordem_apresentacao = equipe['ordem_apresentacao']
            status_votacao = equipe['status_votacao']
            
            with st.expander(f"Equipe: {nome_equipe} | Ordem: {ordem_apresentacao} | Status: {status_votacao}", expanded=False):
                col1, col2 = st.columns([1,1])
                
                with col1:
                    # Botões para Iniciar e Resetar Votação
                    iniciar_key = f"iniciar_{id_equipe}"
                    resetar_key = f"resetar_{id_equipe}"
                    
                    if status_votacao.lower() != 'votando':
                        if st.button("Iniciar Votação", key=iniciar_key):
                            iniciar_votacao(ano_selecionado, id_modalidade_selecionada, id_equipe)
                    else:
                        if st.button("Resetar Votação", key=resetar_key):
                            resetar_votacao(id_equipe)
                
                with col2:
                    # Botão para Adicionar Jurado
                    if status_votacao.lower() == 'votando':
                        jurados_disponiveis = carregar_jurados(ano_selecionado)
                        if not jurados_disponiveis:
                            st.warning("Não há jurados cadastrados para este ano.")
                        else:
                            jurado_dict = {nome: jid for (jid, nome) in jurados_disponiveis}
                            jurado_nomes = list(jurado_dict.keys())
                            
                            # Seleção de jurado a ser adicionado
                            jurado_selecionado = st.selectbox(f"Adicionar Jurado para {nome_equipe}:", jurado_nomes, key=f"jurado_{id_equipe}")
                            id_jurado_selecionado = jurado_dict[jurado_selecionado]
                            
                            if st.button("Adicionar Jurado", key=f"add_jurado_{id_equipe}"):
                                adicionar_jurado(ano_selecionado, id_modalidade_selecionada, id_equipe, id_jurado_selecionado)
    
                st.markdown("### Participantes")
                participantes_df = carregar_participantes(id_equipe)
                if participantes_df.empty:
                    st.write("Nenhum participante cadastrado para esta equipe.")
                else:
                    for idx, participante in participantes_df.iterrows():
                        st.write(f"- {participante['nome']} ({participante['turma']})")
                
                if status_votacao.lower() == 'votando':
                    st.markdown("### Notas")
                    try:
                        conn = get_connection()
                        if conn:
                            cursor = conn.cursor()
                            query = '''
                                SELECT 
                                    j.id_jurado,
                                    j.nome AS jurado, 
                                    n.status, 
                                    c.nome AS criterio, 
                                    CASE 
                                        WHEN e.id_jurado IS NOT NULL THEN 'Sim' 
                                        ELSE 'Não' 
                                    END AS especialista, 
                                    n.nota
                                FROM tbl_notas n
                                JOIN tbl_jurados j ON n.id_jurado = j.id_jurado
                                JOIN tbl_criterios c ON n.id_criterio = c.id_criterio
                                LEFT JOIN tbl_especialistas e 
                                    ON j.id_jurado = e.id_jurado 
                                    AND c.id_modalidade = e.id_modalidade 
                                    AND e.id_ano = n.id_ano
                                WHERE n.id_equipe = %s
                                ORDER BY j.nome, c.nome;
                            '''
                            cursor.execute(query, (id_equipe,))
                            rows = cursor.fetchall()
                            colunas = [desc[0] for desc in cursor.description]
                            notas_df = pd.DataFrame(rows, columns=colunas)
                            
                            if notas_df.empty:
                                st.write("Nenhuma nota cadastrada.")
                            else:
                                # Agrupar notas por jurado
                                jurados = notas_df.groupby(['id_jurado', 'jurado', 'status', 'especialista'])
                                
                                for (id_jurado, jurado_nome, status_nota, especialista), group in jurados:
                                    st.write(f"**Juror:** {jurado_nome} | **Status:** {status_nota} | **Especialista:** {especialista}")
                                    
                                    # Botão Bloquear/Liberar
                                    botao_label = "Bloquear" if status_nota.lower() == 'liberado' else "Liberar"
                                    botao_key = f"botao_bloquear_{id_equipe}_{id_jurado}"
                                    
                                    if st.button(botao_label, key=botao_key):
                                        alternar_status_jurado(id_equipe, id_jurado, status_nota)
                                    
                                    # Checkbox para mostrar/ocultar critérios
                                    mostrar_criterios = st.checkbox("Mostrar Critérios", key=f"mostrar_{id_equipe}_{id_jurado}")
                                    
                                    if mostrar_criterios:
                                        st.table(group[['criterio', 'nota']].rename(columns={'criterio': 'Critério', 'nota': 'Nota'}))
                    except Exception as e:
                        st.error(f"Erro ao carregar notas: {e}")
                    finally:
                        if 'cursor' in locals():
                            cursor.close()
                        if conn:
                            conn.close()

# Para rodar esta página como uma aplicação Streamlit, salve este código em um arquivo chamado `controle_votacoes.py` e execute:
# streamlit run controle_votacoes.py

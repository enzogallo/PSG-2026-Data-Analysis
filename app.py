import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import base64
import os
from streamlit_card import card

# ----------------------------
# FONCTIONS FBREF
# ----------------------------
@st.cache_data
def load_fbref_data():
    """Charge les données FBref du PSG pour la saison 2024-2025"""
    standard_stats = pd.read_csv('PSG Standard Stats.csv')
    shooting_stats = pd.read_csv('PSG Shooting.csv')
    passing_stats = pd.read_csv('PSG Passing.csv')
    possession_stats = pd.read_csv('PSG Possession.csv')
    playing_time = pd.read_csv('PSG Playing Time.csv')
    
    # Nettoyage des données
    for df in [standard_stats, shooting_stats, passing_stats, possession_stats, playing_time]:
        df['Player'] = df['Player'].str.strip()
        df['Pos'] = df['Pos'].str.strip()
    
    return {
        'standard': standard_stats,
        'shooting': shooting_stats,
        'passing': passing_stats,
        'possession': possession_stats,
        'playing_time': playing_time
    }

def render_overview():
    """Affiche la vue d'ensemble des performances de l'équipe"""
    data = load_fbref_data()
    
    # Conversion des colonnes numériques
    numeric_columns = ['Gls', 'Ast', 'xG', 'xAG', 'Min', 'MP']
    for col in numeric_columns:
        if col in data['standard'].columns:
            data['standard'][col] = pd.to_numeric(data['standard'][col], errors='coerce')
    
    # Calcul des statistiques par 90 minutes
    data['standard']['Gls/90'] = (data['standard']['Gls'] * 90) / data['standard']['Min']
    data['standard']['Ast/90'] = (data['standard']['Ast'] * 90) / data['standard']['Min']
    
    # Statistiques globales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_goals = data['standard']['Gls'].sum()
        total_assists = data['standard']['Ast'].sum()
        st.metric("Buts marqués", int(total_goals))
        st.metric("Passes décisives", int(total_assists))
    
    with col2:
        avg_xg = data['standard']['xG'].mean()
        avg_xag = data['standard']['xAG'].mean()
        st.metric("xG moyen par joueur", round(avg_xg, 2))
        st.metric("xAG moyen par joueur", round(avg_xag, 2))
    
    with col3:
        total_minutes = data['standard']['Min'].sum()
        total_matches = data['standard']['MP'].sum()
        st.metric("Minutes jouées", int(total_minutes))
        st.metric("Matches joués", int(total_matches))
    
    # Top 5 buteurs
    st.subheader("Top 5 Buteurs")
    top_scorers = data['standard'].nlargest(5, 'Gls')[['Player', 'Gls', 'xG', 'Gls/90']]
    fig_scorers = px.bar(top_scorers, x='Player', y='Gls',
                        title='Top 5 Buteurs',
                        color='Gls',
                        color_continuous_scale='Blues')
    st.plotly_chart(fig_scorers, use_container_width=True)
    
    # Top 5 passeurs
    st.subheader("Top 5 Passeurs")
    top_assists = data['standard'].nlargest(5, 'Ast')[['Player', 'Ast', 'xAG', 'Ast/90']]
    fig_assists = px.bar(top_assists, x='Player', y='Ast',
                        title='Top 5 Passeurs',
                        color='Ast',
                        color_continuous_scale='Greens')
    st.plotly_chart(fig_assists, use_container_width=True)

def render_player_analysis():
    """Affiche l'analyse détaillée par joueur"""
    data = load_fbref_data()
    
    # Sélection du joueur
    player_names = data['standard']['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names)
    
    # Informations de base
    player_data = data['standard'][data['standard']['Player'] == selected_player].iloc[0]
    player_shooting = data['shooting'][data['shooting']['Player'] == selected_player].iloc[0]
    player_passing = data['passing'][data['passing']['Player'] == selected_player].iloc[0]
    
    # Métriques principales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Matches joués", player_data['MP'])
        st.metric("Minutes jouées", player_data['Min'])
        st.metric("Buts", player_data['Gls'])
        st.metric("Passes décisives", player_data['Ast'])
    
    with col2:
        st.metric("xG", round(player_data['xG'], 2))
        st.metric("xAG", round(player_data['xAG'], 2))
        st.metric("Tirs", player_shooting['Sh'])
        st.metric("Tirs cadrés", player_shooting['SoT'])
    
    with col3:
        st.metric("Précision des passes", f"{player_passing['Cmp%']}%")
        st.metric("Passes progressives", player_passing['PrgP'])
        st.metric("Passes clés", player_passing['KP'])
        st.metric("Centres", player_passing['CrsPA'])
    
    # Graphiques de performance
    st.subheader("Performance offensive")
    fig_offensive = go.Figure()
    
    fig_offensive.add_trace(go.Bar(
        name='Réalisé',
        x=['Buts', 'Passes décisives'],
        y=[player_data['Gls'], player_data['Ast']],
        marker_color=['#1f77b4', '#ff7f0e']
    ))
    
    fig_offensive.add_trace(go.Bar(
        name='Attendu',
        x=['xG', 'xAG'],
        y=[player_data['xG'], player_data['xAG']],
        marker_color=['#2ca02c', '#d62728']
    ))
    
    fig_offensive.update_layout(
        title='Performance offensive',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_offensive, use_container_width=True)

def render_position_analysis():
    """Affiche l'analyse par position"""
    data = load_fbref_data()
    
    # Conversion des colonnes numériques
    numeric_columns = ['Gls', 'Ast', 'xG', 'xAG', 'Min', 'MP']
    for col in numeric_columns:
        if col in data['standard'].columns:
            data['standard'][col] = pd.to_numeric(data['standard'][col], errors='coerce')
    
    # Sélection de la position
    positions = ['FW', 'MF', 'DF', 'GK']
    selected_position = st.selectbox("Sélectionnez une position", positions)
    
    # Filtrage des joueurs par position
    position_players = data['standard'][data['standard']['Pos'].str.contains(selected_position, na=False)]
    
    # Statistiques moyennes par position
    st.subheader(f"Statistiques moyennes - {selected_position}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Buts moyens", round(position_players['Gls'].mean(), 2))
        st.metric("Passes décisives moyennes", round(position_players['Ast'].mean(), 2))
    
    with col2:
        st.metric("xG moyen", round(position_players['xG'].mean(), 2))
        st.metric("xAG moyen", round(position_players['xAG'].mean(), 2))
    
    with col3:
        st.metric("Minutes jouées moyennes", round(position_players['Min'].mean(), 2))
        st.metric("Matches joués moyens", round(position_players['MP'].mean(), 2))
    
    # Création du graphique de dispersion avec gestion des valeurs NaN
    fig_scatter = go.Figure()
    
    # Ajout des points pour chaque joueur
    for _, player in position_players.iterrows():
        if pd.notna(player['Min']):  # Vérification que les minutes ne sont pas NaN
            fig_scatter.add_trace(go.Scatter(
                x=[player['Gls']],
                y=[player['Ast']],
                mode='markers+text',
                name=player['Player'],
                text=[player['Player']],
                textposition="top center",
                marker=dict(
                    size=player['Min']/100,  # Ajustement de la taille pour une meilleure visualisation
                    color=player['Gls'],
                    colorscale='Blues',
                    showscale=True
                ),
                hovertemplate=(
                    f"Joueur: {player['Player']}<br>"
                    f"Buts: {player['Gls']}<br>"
                    f"Passes décisives: {player['Ast']}<br>"
                    f"xG: {player['xG']:.2f}<br>"
                    f"xAG: {player['xAG']:.2f}<br>"
                    f"Minutes: {player['Min']}"
                )
            ))
    
    fig_scatter.update_layout(
        title=f'Buts vs Passes décisives - {selected_position}',
        xaxis_title='Buts',
        yaxis_title='Passes décisives',
        showlegend=False
    )
    
    st.plotly_chart(fig_scatter, use_container_width=True)

def render_comparisons():
    """Affiche les comparaisons entre joueurs"""
    data = load_fbref_data()
    
    # Sélection des joueurs à comparer
    player_names = data['standard']['Player'].tolist()
    selected_players = st.multiselect("Sélectionnez les joueurs à comparer", player_names, max_selections=3)
    
    if len(selected_players) > 0:
        # Filtrage des données pour les joueurs sélectionnés
        comparison_data = data['standard'][data['standard']['Player'].isin(selected_players)]
        
        # Création du graphique de comparaison
        metrics = ['Gls', 'Ast', 'xG', 'xAG', 'PrgC', 'PrgP', 'PrgR']
        metric_names = ['Buts', 'Passes décisives', 'xG', 'xAG', 'Progrès porté', 'Progrès reçu', 'Progrès dribbles']
        
        fig_comparison = go.Figure()
        
        for i, player in enumerate(selected_players):
            player_metrics = comparison_data[comparison_data['Player'] == player][metrics].iloc[0]
            fig_comparison.add_trace(go.Bar(
                name=player,
                x=metric_names,
                y=player_metrics,
                text=player_metrics.round(2),
                textposition='auto',
            ))
        
        fig_comparison.update_layout(
            title='Comparaison des performances',
            barmode='group',
            showlegend=True
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)

def render_home():
    """Fonction principale de l'application"""
    st.title("PSG Data Center - Saison 2024-2025")
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "Vue d'ensemble",
        "Analyse par joueur",
        "Analyse par position",
        "Comparaisons"
    ])
    
    with tab1:
        render_overview()
    
    with tab2:
        render_player_analysis()
    
    with tab3:
        render_position_analysis()
    
    with tab4:
        render_comparisons()

if __name__ == "__main__":
    render_home()

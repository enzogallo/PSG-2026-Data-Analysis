import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import base64
import os
from streamlit_card import card

# Configuration de la page
st.set_page_config(
    page_title="PSG Data Center 2024-2025",
    page_icon="⚽",
    layout="wide"
)

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

def create_scatter_plot(data, x_col, y_col, color_col, size_col, title, hover_data=None):
    """Crée un graphique de dispersion personnalisé"""
    fig = go.Figure()
    
    for _, row in data.iterrows():
        if pd.notna(row[size_col]):
            fig.add_trace(go.Scatter(
                x=[row[x_col]],
                y=[row[y_col]],
                mode='markers+text',
                name=row['Player'],
                text=[row['Player']],
                textposition="top center",
                marker=dict(
                    size=float(row[size_col])/100,
                    color=float(row[color_col]),
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title=color_col)
                ),
                hovertemplate=(
                    f"Joueur: {row['Player']}<br>"
                    + "<br>".join([f"{col}: {row[col]}" for col in hover_data])
                )
            ))
    
    fig.update_layout(
        title=title,
        xaxis_title=x_col,
        yaxis_title=y_col,
        showlegend=False
    )
    
    return fig

def display_player_metrics(player_data, player_passing, player_shooting):
    """Affiche les métriques d'un joueur"""
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

def display_position_metrics(position_players):
    """Affiche les métriques moyennes par position"""
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
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="player_analysis_select")
    
    # Informations de base
    player_data = data['standard'][data['standard']['Player'] == selected_player].iloc[0]
    player_shooting = data['shooting'][data['shooting']['Player'] == selected_player].iloc[0]
    player_passing = data['passing'][data['passing']['Player'] == selected_player].iloc[0]
    
    # Affichage des métriques
    display_player_metrics(player_data, player_passing, player_shooting)
    
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
    selected_position = st.selectbox("Sélectionnez une position", positions, key="position_analysis_select")
    
    # Filtrage des joueurs par position
    position_players = data['standard'][data['standard']['Pos'].str.contains(selected_position, na=False)]
    
    # Statistiques moyennes par position
    st.subheader(f"Statistiques moyennes - {selected_position}")
    display_position_metrics(position_players)
    
    # Graphique de dispersion
    fig = create_scatter_plot(
        position_players,
        'Gls', 'Ast', 'Gls', 'Min',
        f'Buts vs Passes décisives - {selected_position}',
        ['Gls', 'Ast', 'xG', 'xAG', 'Min']
    )
    
    st.plotly_chart(fig, use_container_width=True)

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

def analyze_tactical_performance():
    """Analyse des performances tactiques de l'équipe"""
    data = load_fbref_data()
    
    st.header("Analyse Tactique")
    
    # Analyse des phases de jeu
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Possession et Progression")
        possession_metrics = {
            "Passes progressives": f"{data['passing']['PrgP'].mean():.1f}",
            "Passes complétées": f"{data['passing']['Cmp'].mean():.1f}",
            "Précision des passes": f"{data['passing']['Cmp%'].mean():.1f}%",
            "Distance totale des passes": f"{data['passing']['TotDist'].mean():.1f}"
        }
        for metric, value in possession_metrics.items():
            st.metric(metric, value)
    
    with col2:
        st.subheader("Efficacité offensive")
        offensive_metrics = {
            "xG par match": f"{data['standard']['xG'].mean():.2f}",
            "Précision des tirs": f"{data['shooting']['SoT%'].mean():.1f}%",
            "Passes clés": f"{data['passing']['KP'].mean():.1f}",
            "Centres réussis": f"{data['passing']['CrsPA'].mean():.1f}"
        }
        for metric, value in offensive_metrics.items():
            st.metric(metric, value)
    
    # Analyse des profils de joueurs
    st.subheader("Profils de Joueurs")
    
    # Création d'un radar chart pour les profils
    positions = ['FW', 'MF', 'DF']
    selected_pos = st.selectbox("Sélectionnez une position pour l'analyse des profils", positions)
    
    position_players = data['standard'][data['standard']['Pos'].str.contains(selected_pos, na=False)]
    
    # Calcul des métriques normalisées pour chaque joueur
    metrics = ['Gls', 'Ast', 'xG', 'xAG', 'PrgP', 'PrgC']
    metric_names = ['Buts', 'Passes', 'xG', 'xAG', 'Progression', 'Création']
    
    for _, player in position_players.iterrows():
        values = []
        for metric in metrics:
            if metric in player:
                # Normalisation par rapport à la moyenne de la position
                normalized_value = (player[metric] - position_players[metric].mean()) / position_players[metric].std()
                values.append(max(0, normalized_value + 2))  # Ajustement pour avoir des valeurs positives
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metric_names,
            fill='toself',
            name=player['Player']
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 4]
                )
            ),
            title=f"Profil de {player['Player']}",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def analyze_team_strengths():
    """Analyse des forces et faiblesses de l'équipe"""
    data = load_fbref_data()
    
    st.header("Analyse des Forces et Faiblesses")
    
    # Analyse des forces
    st.subheader("Forces de l'Équipe")
    
    # Création d'un graphique en barres pour les statistiques clés
    key_stats = {
        'Buts': data['standard']['Gls'].sum(),
        'xG': data['standard']['xG'].sum(),
        'Passes décisives': data['standard']['Ast'].sum(),
        'xAG': data['standard']['xAG'].sum(),
        'Passes progressives': data['passing']['PrgP'].sum(),
        'Dribbles réussis': data['possession']['Succ'].sum()
    }
    
    fig_strengths = go.Figure(data=[
        go.Bar(
            x=list(key_stats.keys()),
            y=list(key_stats.values()),
            marker_color='#1f77b4'
        )
    ])
    
    fig_strengths.update_layout(
        title="Statistiques Offensives",
        xaxis_title="Métriques",
        yaxis_title="Valeur Totale"
    )
    
    st.plotly_chart(fig_strengths, use_container_width=True)
    
    # Analyse des profils de position
    st.subheader("Analyse par Position")
    
    positions = ['FW', 'MF', 'DF']
    for pos in positions:
        pos_players = data['standard'][data['standard']['Pos'].str.contains(pos, na=False)]
        
        st.write(f"### {pos}")
        
        # Calcul des moyennes par position
        pos_metrics = {
            'Buts': pos_players['Gls'].mean(),
            'Passes décisives': pos_players['Ast'].mean(),
            'xG': pos_players['xG'].mean(),
            'xAG': pos_players['xAG'].mean()
        }
        
        col1, col2, col3, col4 = st.columns(4)
        for (metric, value), col in zip(pos_metrics.items(), [col1, col2, col3, col4]):
            with col:
                st.metric(metric, f"{value:.2f}")

def analyze_player_roles():
    """Analyse des rôles et profils des joueurs"""
    data = load_fbref_data()
    
    st.header("Analyse des Rôles et Profils")
    
    # Sélection du joueur
    player_names = data['standard']['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="player_roles_select")
    
    # Récupération des données du joueur
    player_data = data['standard'][data['standard']['Player'] == selected_player].iloc[0]
    player_passing = data['passing'][data['passing']['Player'] == selected_player].iloc[0]
    player_shooting = data['shooting'][data['shooting']['Player'] == selected_player].iloc[0]
    
    # Profil du joueur
    st.subheader(f"Profil de {selected_player}")
    
    # Création d'un graphique radar pour le profil
    metrics = {
        'Buts': player_data['Gls'],
        'Passes décisives': player_data['Ast'],
        'xG': player_data['xG'],
        'xAG': player_data['xAG'],
        'Passes clés': player_passing['KP'],
        'Tirs cadrés': player_shooting['SoT']
    }
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(metrics.values()),
        theta=list(metrics.keys()),
        fill='toself',
        name=selected_player
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(metrics.values()) * 1.2]
            )
        ),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Affichage des métriques
    display_player_metrics(player_data, player_passing, player_shooting)

def analyze_team_dynamics():
    """Analyse des dynamiques d'équipe"""
    data = load_fbref_data()
    
    st.header("Dynamiques d'Équipe")
    
    # Conversion des colonnes numériques
    numeric_columns = ['Gls', 'Ast', 'xG', 'xAG', 'Min', 'MP']
    for col in numeric_columns:
        if col in data['standard'].columns:
            data['standard'][col] = pd.to_numeric(data['standard'][col], errors='coerce')
    
    # Analyse des duos
    st.subheader("Duos les Plus Efficaces")
    
    # Création d'un graphique en barres pour les meilleurs buteurs
    top_scorers = data['standard'].nlargest(5, 'Gls')[['Player', 'Gls', 'Ast']]
    fig_scorers = px.bar(top_scorers, 
                        x='Player', 
                        y=['Gls', 'Ast'],
                        title='Top 5 Buteurs et Leurs Passes Décisives',
                        barmode='group',
                        color_discrete_sequence=['#1f77b4', '#ff7f0e'])
    
    st.plotly_chart(fig_scorers, use_container_width=True)
    
    # Analyse des profils de position
    st.subheader("Profils par Position")
    
    positions = ['FW', 'MF', 'DF']
    selected_position = st.selectbox("Sélectionnez une position", positions, key="position_dynamics_select")
    
    pos_players = data['standard'][data['standard']['Pos'].str.contains(selected_position, na=False)]
    
    st.write(f"### {selected_position}")
    display_position_metrics(pos_players)
    
    # Graphique de dispersion
    fig = create_scatter_plot(
        pos_players,
        'Gls', 'Ast', 'xG', 'Min',
        f'Buts vs Passes décisives - {selected_position}',
        ['Gls', 'Ast', 'xG', 'xAG', 'Min']
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analyze_tactical_patterns():
    """Analyse des patterns tactiques de l'équipe"""
    data = load_fbref_data()
    
    st.header("Analyse Tactique Avancée")
    
    # Analyse des phases de jeu
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Phases de Jeu")
        # Calcul des métriques de pressing avec les colonnes disponibles
        pressing_metrics = {
            "Passes complétées": data['passing']['Cmp'].mean(),
            "Précision des passes": f"{data['passing']['Cmp%'].mean():.1f}%",
            "Passes progressives": data['passing']['PrgP'].mean(),
            "Passes clés": data['passing']['KP'].mean()
        }
        
        for metric, value in pressing_metrics.items():
            st.metric(metric, value)
    
    with col2:
        st.subheader("Progression du Jeu")
        progression_metrics = {
            "Passes progressives": data['passing']['PrgP'].mean(),
            "Progression portée": data['standard']['PrgC'].mean(),
            "Progression reçue": data['standard']['PrgR'].mean(),
            "Distance totale des passes": f"{data['passing']['TotDist'].mean():.1f}"
        }
        
        for metric, value in progression_metrics.items():
            st.metric(metric, value)
    
    # Analyse des zones de jeu
    st.subheader("Zones d'Influence")
    
    # Création d'une heatmap des zones de jeu
    positions = ['FW', 'MF', 'DF']
    selected_pos = st.selectbox("Sélectionnez une position", positions, key="tactical_position_select")
    
    pos_players = data['standard'][data['standard']['Pos'].str.contains(selected_pos, na=False)]
    
    # Création d'une matrice de zones (simulation)
    zones = np.zeros((5, 5))
    for _, player in pos_players.iterrows():
        # Simulation de l'influence dans différentes zones basée sur les statistiques disponibles
        influence = (player['Gls'] + player['Ast'] + player['PrgP']) / 3
        zones += influence
    
    fig = go.Figure(data=go.Heatmap(
        z=zones,
        colorscale='Viridis',
        showscale=True
    ))
    
    fig.update_layout(
        title=f'Zones d\'influence - {selected_pos}',
        xaxis_title='Largeur du terrain',
        yaxis_title='Longueur du terrain'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analyze_defensive_metrics():
    """Analyse des performances défensives"""
    data = load_fbref_data()
    
    st.header("Analyse Défensive")
    
    # Métriques défensives
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Progression")
        defensive_metrics = {
            "Progression portée": data['standard']['PrgC'].mean(),
            "Progression reçue": data['standard']['PrgR'].mean(),
            "Passes progressives": data['passing']['PrgP'].mean()
        }
        for metric, value in defensive_metrics.items():
            st.metric(metric, f"{value:.1f}")
    
    with col2:
        st.subheader("Possession")
        possession_metrics = {
            "Passes complétées": data['passing']['Cmp'].mean(),
            "Passes progressives": data['passing']['PrgP'].mean(),
            "Progression portée": data['standard']['PrgC'].mean()
        }
        for metric, value in possession_metrics.items():
            st.metric(metric, f"{value:.1f}")
    
    with col3:
        st.subheader("Distribution")
        distribution_metrics = {
            "Passes complétées": data['passing']['Cmp'].mean(),
            "Passes progressives": data['passing']['PrgP'].mean(),
            "Progression reçue": data['standard']['PrgR'].mean()
        }
        for metric, value in distribution_metrics.items():
            st.metric(metric, f"{value:.1f}")
    
    # Graphique des performances par position
    st.subheader("Performances par Position")
    
    positions = ['DF', 'MF']
    defensive_data = data['standard'][data['standard']['Pos'].str.contains('|'.join(positions), na=False)]
    
    fig = go.Figure()
    
    for pos in positions:
        pos_players = defensive_data[defensive_data['Pos'].str.contains(pos, na=False)]
        fig.add_trace(go.Bar(
            name=pos,
            x=['Progression', 'Passes', 'Réception'],
            y=[
                pos_players['PrgC'].mean(),
                pos_players['PrgP'].mean(),
                pos_players['PrgR'].mean()
            ]
        ))
    
    fig.update_layout(
        title='Métriques par position',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def analyze_match_performance():
    """Analyse des performances match par match"""
    data = load_fbref_data()
    
    st.header("Analyse Match par Match")
    
    # Analyse des performances par joueur
    st.subheader("Performances par Joueur")
    
    # Sélection du joueur
    player_names = data['standard']['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="match_performance_select")
    
    # Récupération des données du joueur
    player_data = data['standard'][data['standard']['Player'] == selected_player].iloc[0]
    player_shooting = data['shooting'][data['shooting']['Player'] == selected_player].iloc[0]
    player_passing = data['passing'][data['passing']['Player'] == selected_player].iloc[0]
    
    # Affichage des statistiques
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
        st.metric("Passes complétées", player_passing['Cmp'])
        st.metric("Passes progressives", player_passing['PrgP'])
        st.metric("Progression portée", player_data['PrgC'])
        st.metric("Progression reçue", player_data['PrgR'])
    
    # Graphique de performance
    st.subheader("Profil de Performance")
    
    metrics = {
        'Buts': player_data['Gls'],
        'Passes décisives': player_data['Ast'],
        'xG': player_data['xG'],
        'xAG': player_data['xAG'],
        'Tirs cadrés': player_shooting['SoT'],
        'Passes progressives': player_passing['PrgP']
    }
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(metrics.keys()),
        y=list(metrics.values()),
        marker_color='#1f77b4'
    ))
    
    fig.update_layout(
        title=f'Profil de performance - {selected_player}',
        xaxis_title='Métriques',
        yaxis_title='Valeur',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison avec la moyenne de l'équipe
    st.subheader("Comparaison avec la Moyenne de l'Équipe")
    
    team_avg = {
        'Buts': data['standard']['Gls'].mean(),
        'Passes décisives': data['standard']['Ast'].mean(),
        'xG': data['standard']['xG'].mean(),
        'xAG': data['standard']['xAG'].mean(),
        'Tirs cadrés': data['shooting']['SoT'].mean(),
        'Passes progressives': data['passing']['PrgP'].mean()
    }
    
    comparison_data = pd.DataFrame({
        'Métrique': list(metrics.keys()),
        'Joueur': list(metrics.values()),
        'Moyenne Équipe': [team_avg[m] for m in metrics.keys()]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Joueur',
        x=comparison_data['Métrique'],
        y=comparison_data['Joueur'],
        marker_color='#1f77b4'
    ))
    
    fig.add_trace(go.Bar(
        name='Moyenne Équipe',
        x=comparison_data['Métrique'],
        y=comparison_data['Moyenne Équipe'],
        marker_color='#ff7f0e'
    ))
    
    fig.update_layout(
        title='Comparaison avec la moyenne de l\'équipe',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_home():
    """Fonction principale de l'application"""
    st.title("PSG Data Center - Saison 2024-2025")
    
    # Onglets principaux
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "Vue d'ensemble",
        "Analyse par joueur",
        "Analyse par position",
        "Comparaisons",
        "Analyse Tactique",
        "Forces et Faiblesses",
        "Rôles et Profils",
        "Dynamiques d'Équipe",
        "Patterns Tactiques",
        "Analyse Défensive",
        "Performances par Match"
    ])
    
    with tab1:
        render_overview()
    
    with tab2:
        render_player_analysis()
    
    with tab3:
        render_position_analysis()
    
    with tab4:
        render_comparisons()
        
    with tab5:
        analyze_tactical_performance()
        
    with tab6:
        analyze_team_strengths()
        
    with tab7:
        analyze_player_roles()
        
    with tab8:
        analyze_team_dynamics()
        
    with tab9:
        analyze_tactical_patterns()
        
    with tab10:
        analyze_defensive_metrics()
        
    with tab11:
        analyze_match_performance()

if __name__ == "__main__":
    render_home()

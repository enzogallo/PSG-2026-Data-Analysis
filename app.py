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

# Chargement du CSS
try:
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.error("Le fichier styles.css est introuvable. Assurez-vous qu'il est dans le même répertoire que app.py.")

# ----------------------------
# FONCTIONS FBREF
# ----------------------------
@st.cache_data
def load_fbref_data():
    """Charge les données FBref du PSG pour la saison 2024-2025"""
    standard_stats = pd.read_csv('data/PSG Standard Stats.csv')
    shooting_stats = pd.read_csv('data/PSG Shooting.csv')
    passing_stats = pd.read_csv('data/PSG Passing.csv')
    possession_stats = pd.read_csv('data/PSG Possession.csv')
    playing_time = pd.read_csv('data/PSG Playing Time.csv')
    goalkeeping_stats = pd.read_csv('data/PSG Goalkeeping.csv')
    
    # Nettoyage des données
    for df in [standard_stats, shooting_stats, passing_stats, possession_stats, playing_time, goalkeeping_stats]:
        df['Player'] = df['Player'].str.strip()
        if 'Pos' in df.columns:
            df['Pos'] = df['Pos'].str.strip()
    
    return {
        'standard': standard_stats,
        'shooting': shooting_stats,
        'passing': passing_stats,
        'possession': possession_stats,
        'playing_time': playing_time,
        'goalkeeping': goalkeeping_stats
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
        # Arrondissement des valeurs
        pressing_metrics = {
            "Passes complétées": round(data['passing']['Cmp'].mean(), 2),
            "Précision des passes": f"{data['passing']['Cmp%'].mean():.1f}%",
            "Passes progressives": round(data['passing']['PrgP'].mean(), 2),
            "Passes clés": round(data['passing']['KP'].mean(), 2)
        }

        for metric, value in pressing_metrics.items():
            st.metric(metric, value)

    with col2:
        st.subheader("Progression du Jeu")
        # Arrondissement des valeurs
        progression_metrics = {
            "Passes progressives": round(data['passing']['PrgP'].mean(), 2),
            "Progression portée": round(data['standard']['PrgC'].mean(), 2),
            "Progression reçue": round(data['standard']['PrgR'].mean(), 2),
            "Distance totale des passes": f"{data['passing']['TotDist'].mean():.1f}"
        }

        for metric, value in progression_metrics.items():
            st.metric(metric, value)

    # Analyse de la Progression par Position
    st.subheader("Progression par Position")

    positions = ['FW', 'MF', 'DF']
    progression_data = data['standard'][data['standard']['Pos'].str.contains('|'.join(positions), na=False)].copy()

    # Assurez-vous que les colonnes de progression sont numériques
    progression_cols = ['PrgC', 'PrgP', 'PrgR']
    for col in progression_cols:
        if col in progression_data.columns:
            progression_data[col] = pd.to_numeric(progression_data[col], errors='coerce').fillna(0)

    # Calculer les moyennes par position
    avg_progression_by_pos = progression_data.groupby('Pos')[progression_cols].mean().reset_index()

    # Renommer les colonnes pour le graphique
    avg_progression_by_pos = avg_progression_by_pos.rename(columns={
        'PrgC': 'Progression portée',
        'PrgP': 'Passes progressives',
        'PrgR': 'Progression reçue'
    })

    # Créer un graphique en barres groupées
    fig_progression = px.bar(avg_progression_by_pos,
                             x='Pos',
                             y=['Progression portée', 'Passes progressives', 'Progression reçue'],
                             title='Progression Moyenne par Position',
                             barmode='group')

    st.plotly_chart(fig_progression, use_container_width=True)

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

def analyze_goalkeeping_performance():
    """Analyse des performances des gardiens"""
    data = load_fbref_data()
    
    st.header("Analyse des Gardiens")
    
    goalkeepers = data['goalkeeping'].copy() # Utiliser une copie pour éviter SettingWithCopyWarning
    
    if goalkeepers.empty:
        st.info("Aucune donnée de gardien disponible.")
        return
    
    # Conversion des colonnes numériques (spécifiques aux gardiens)
    # J'ai mis à jour la liste des colonnes en fonction du fichier CSV disponible
    numeric_gk_columns = [
        'GA', 'GA90', 'SoTA', 'Saves', 'Save%', 'W', 'D', 'L', 'CS', 'CS%', 'PKatt', 'PKA', 'PKsv', 'PKm', 'Save%.1'
    ]
    
    for col in numeric_gk_columns:
        if col in goalkeepers.columns:
            # Convertir en numérique et remplir les NaN avec 0
            goalkeepers[col] = pd.to_numeric(goalkeepers[col], errors='coerce').fillna(0)
            
    # Sélection du gardien
    gk_names = goalkeepers['Player'].tolist()
    selected_gk = st.selectbox("Sélectionnez un gardien", gk_names, key="goalkeeper_select")
    
    selected_gk_data = goalkeepers[goalkeepers['Player'] == selected_gk].iloc[0]
    
    # Affichage des métriques clés
    st.subheader(f"Statistiques pour {selected_gk}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Matches joués", selected_gk_data['MP'])
        st.metric("Minutes jouées", selected_gk_data['Min'])
        st.metric("Buts encaissés", selected_gk_data['GA'])
        st.metric("Buts encaissés p90", round(selected_gk_data['GA90'], 2))
    
    with col2:
        st.metric("Arrêts", selected_gk_data['Saves'])
        st.metric("Pourcentage d\'arrêts", f"{round(selected_gk_data['Save%'], 1)}%")
        st.metric("Clean Sheets", selected_gk_data['CS'])
        st.metric("Pourcentage Clean Sheets", f"{round(selected_gk_data['CS%'], 1)}%")
        
    with col3:
        st.metric("Arrêts penalty", selected_gk_data['PKsv'])
        st.metric("Tentatives penalty subies", selected_gk_data['PKatt'])
        st.metric("Penalty manqués subis", selected_gk_data['PKm'])
        st.metric("Pourcentage d\'arrêts penalty", f"{round(selected_gk_data['Save%.1'], 1)}%")
        
    # Graphique de comparaison des arrêts
    st.subheader("Arrêts vs Buts encaissés p90")
    
    fig_gk = go.Figure()
    fig_gk.add_trace(go.Bar(
        name='Arrêts',
        x=[selected_gk],
        y=[selected_gk_data['Saves']],
        marker_color='#2ca02c'
    ))
    fig_gk.add_trace(go.Bar(
        name='Buts encaissés p90',
        x=[selected_gk],
        y=[selected_gk_data['GA90']],
        marker_color='#d62728'
    ))
    
    fig_gk.update_layout(
        title=f'Comparaison Arrêts vs Buts encaissés p90 - {selected_gk}',
        yaxis_title='Valeur',
        showlegend=True
    )
    
    st.plotly_chart(fig_gk, use_container_width=True)

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
        'Tirs cadrés': player_data['SoT'],
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

@st.cache_data
def load_ucl_data():
    """Charge les données des matchs de Ligue des Champions"""
    # Définition de l'ordre chronologique des matchs, leurs phases et leurs scores
    match_order = {
        # Phase de Ligue
        'PSG - Girona': {'phase': 'Phase de Ligue', 'ordre': 1, 'score': '1-0'},
        'Arsenal - PSG': {'phase': 'Phase de Ligue', 'ordre': 2, 'score': '2-0'},
        'PSG -PSV': {'phase': 'Phase de Ligue', 'ordre': 3, 'score': '1-1'},
        'PSG - Atletico': {'phase': 'Phase de Ligue', 'ordre': 4, 'score': '1-2'},
        'Bayern - PSG': {'phase': 'Phase de Ligue', 'ordre': 5, 'score': '1-0'},
        'Salzburg - PSG': {'phase': 'Phase de Ligue', 'ordre': 6, 'score': '0-3'},
        'PSG - Manchester City': {'phase': 'Phase de Ligue', 'ordre': 7, 'score': '4-2'},
        'Stuttgart - PSG': {'phase': 'Phase de Ligue', 'ordre': 8, 'score': '1-4'},
        # Barrages
        'Brest - PSG': {'phase': 'Barrages', 'ordre': 9, 'score': '0-3'},
        'PSG - Brest': {'phase': 'Barrages', 'ordre': 10, 'score': '7-0'},
        # 1/8 de finale
        'PSG - Liverpool': {'phase': '1/8 de finale', 'ordre': 11, 'score': '0-1'},
        'Liverpool - PSG': {'phase': '1/8 de finale', 'ordre': 12, 'score': '1-0 (4-1 pen)'},
        # 1/4 de finale
        'PSG - Aston Villa': {'phase': '1/4 de finale', 'ordre': 13, 'score': '3-1'},
        'Aston Villa - PSG': {'phase': '1/4 de finale', 'ordre': 14, 'score': '3-2'},
        # 1/2 finale
        'Arsenal - PSG 2': {'phase': '1/2 finale', 'ordre': 15, 'score': '0-1'},
        'PSG - Arsenal ': {'phase': '1/2 finale', 'ordre': 16, 'score': '2-1'},
        # Finale
        'PSG - Inter': {'phase': 'Finale', 'ordre': 17, 'score': '5-0'}
    }
    
    ucl_data = {}
    
    for file in os.listdir('data/PSG UCL Games'):
        if file.endswith('.csv'):
            match_name = file.replace('PSG UCL Games - ', '').replace('.csv', '')
            if match_name in match_order:
                df = pd.read_csv(f'data/PSG UCL Games/{file}', skiprows=1)
                df = df.rename(columns={
                    'Performance': 'Player',
                    'Gls': 'Gls',
                    'Ast': 'Ast',
                    'Sh': 'Sh',
                    'SoT': 'SoT',
                    'xG': 'xG',
                    'xAG': 'xAG',
                    'SCA': 'SCA',
                    'GCA': 'GCA',
                    'PrgP': 'PrgP',
                    'PrgC': 'PrgC',
                    'Min': 'Min'
                })
                df['Phase'] = match_order[match_name]['phase']
                df['Ordre'] = match_order[match_name]['ordre']
                df['Score'] = match_order[match_name]['score']
                ucl_data[match_name] = df
    
    return ucl_data

def analyze_ucl_progression():
    """Analyse de la progression dans la Ligue des Champions"""
    data = load_ucl_data()
    
    st.subheader("Progression dans la compétition")
    
    # Calcul des statistiques cumulées
    cumulative_stats = {
        'Gls': [],
        'Ast': [],
        'xG': [],
        'xAG': [],
        'Sh': [],
        'SoT': [],
        'SCA': [],
        'GCA': []
    }
    
    match_names = []
    phases = []
    scores = []
    
    for match_name, match_data in sorted(data.items(), key=lambda x: x[1]['Ordre'].iloc[0]):
        match_names.append(match_name)
        phases.append(match_data['Phase'].iloc[0])
        scores.append(match_data['Score'].iloc[0])
        for stat in cumulative_stats.keys():
            cumulative_stats[stat].append(match_data[stat].sum())
    
    # Création d'un DataFrame pour les statistiques cumulées
    progression_df = pd.DataFrame({
        'Match': match_names,
        'Phase': phases,
        'Score': scores,
        **cumulative_stats
    })
    
    # Graphique de progression des buts et xG
    fig_goals = go.Figure()
    fig_goals.add_trace(go.Scatter(
        name='Buts',
        x=progression_df['Match'],
        y=progression_df['Gls'],
        mode='lines+markers',
        marker=dict(color='#1f77b4'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>Buts: %{y}<extra></extra>"
    ))
    fig_goals.add_trace(go.Scatter(
        name='xG',
        x=progression_df['Match'],
        y=progression_df['xG'],
        mode='lines+markers',
        marker=dict(color='#ff7f0e'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>xG: %{y}<extra></extra>"
    ))
    
    fig_goals.update_layout(
        title='Progression des buts et xG',
        xaxis_title='Match',
        yaxis_title='Valeur',
        showlegend=True,
        xaxis=dict(tickangle=45)
    )
    
    st.plotly_chart(fig_goals, use_container_width=True)
    
    # Graphique de progression des actions de création
    fig_creation = go.Figure()
    fig_creation.add_trace(go.Scatter(
        name='Actions de création',
        x=progression_df['Match'],
        y=progression_df['SCA'],
        mode='lines+markers',
        marker=dict(color='#2ca02c'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>SCA: %{y}<extra></extra>"
    ))
    fig_creation.add_trace(go.Scatter(
        name='Actions de création de buts',
        x=progression_df['Match'],
        y=progression_df['GCA'],
        mode='lines+markers',
        marker=dict(color='#d62728'),
        text=progression_df['Score'],
        hovertemplate="Match: %{x}<br>Score: %{text}<br>GCA: %{y}<extra></extra>"
    ))
    
    fig_creation.update_layout(
        title='Progression des actions de création',
        xaxis_title='Match',
        yaxis_title='Valeur',
        showlegend=True,
        xaxis=dict(tickangle=45)
    )
    
    st.plotly_chart(fig_creation, use_container_width=True)
    
    # Analyse des performances par phase
    st.subheader("Performances par phase")
    
    phase_stats = progression_df.groupby('Phase').agg({
        'Gls': 'sum',
        'Ast': 'sum',
        'xG': 'sum',
        'Sh': 'sum',
        'SCA': 'sum',
        'GCA': 'sum'
    }).reset_index()
    
    fig_phase = go.Figure()
    fig_phase.add_trace(go.Bar(
        name='Buts',
        x=phase_stats['Phase'],
        y=phase_stats['Gls'],
        marker_color='#1f77b4'
    ))
    fig_phase.add_trace(go.Bar(
        name='Passes décisives',
        x=phase_stats['Phase'],
        y=phase_stats['Ast'],
        marker_color='#ff7f0e'
    ))
    
    fig_phase.update_layout(
        title='Buts et Passes décisives par phase',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_phase, use_container_width=True)
    


def analyze_ucl_key_players():
    """Analyse des performances clés des joueurs en Ligue des Champions"""
    data = load_ucl_data()
    
    st.subheader("Performances clés des joueurs")
    
    # Calcul des statistiques cumulées par joueur
    player_stats = {}
    
    for match_data in data.values():
        for _, player in match_data.iterrows():
            player_name = player['Player']
            if player_name not in player_stats:
                player_stats[player_name] = {
                    'Gls': 0, 'Ast': 0, 'xG': 0, 'xAG': 0,
                    'Sh': 0, 'SoT': 0, 'SCA': 0, 'GCA': 0,
                    'Min': 0, 'Matches': 0
                }
            
            player_stats[player_name]['Gls'] += player['Gls']
            player_stats[player_name]['Ast'] += player['Ast']
            player_stats[player_name]['xG'] += player['xG']
            player_stats[player_name]['xAG'] += player['xAG']
            player_stats[player_name]['Sh'] += player['Sh']
            player_stats[player_name]['SoT'] += player['SoT']
            player_stats[player_name]['SCA'] += player['SCA']
            player_stats[player_name]['GCA'] += player['GCA']
            player_stats[player_name]['Min'] += player['Min']
            player_stats[player_name]['Matches'] += 1
    
    # Conversion en DataFrame
    key_players_df = pd.DataFrame.from_dict(player_stats, orient='index')
    key_players_df = key_players_df.reset_index().rename(columns={'index': 'Player'})
    
    # Calcul des statistiques par 90 minutes
    key_players_df['Gls/90'] = (key_players_df['Gls'] * 90) / key_players_df['Min']
    key_players_df['Ast/90'] = (key_players_df['Ast'] * 90) / key_players_df['Min']
    key_players_df['xG/90'] = (key_players_df['xG'] * 90) / key_players_df['Min']
    key_players_df['xAG/90'] = (key_players_df['xAG'] * 90) / key_players_df['Min']
    key_players_df['SCA/90'] = (key_players_df['SCA'] * 90) / key_players_df['Min']
    key_players_df['GCA/90'] = (key_players_df['GCA'] * 90) / key_players_df['Min']
    
    # Sélection des joueurs avec au moins 90 minutes jouées
    key_players_df = key_players_df[key_players_df['Min'] >= 90]
    
    # Top 5 buteurs
    st.write("### Top 5 Buteurs")
    top_scorers = key_players_df.nlargest(5, 'Gls')[['Player', 'Gls', 'Gls/90', 'xG', 'xG/90']]
    
    fig_scorers = go.Figure()
    fig_scorers.add_trace(go.Bar(
        name='Buts',
        x=top_scorers['Player'],
        y=top_scorers['Gls'],
        marker_color='#1f77b4'
    ))
    fig_scorers.add_trace(go.Bar(
        name='xG',
        x=top_scorers['Player'],
        y=top_scorers['xG'],
        marker_color='#ff7f0e'
    ))
    
    fig_scorers.update_layout(
        title='Top 5 Buteurs',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_scorers, use_container_width=True)
    
    # Top 5 passeurs
    st.write("### Top 5 Passeurs")
    top_assists = key_players_df.nlargest(5, 'Ast')[['Player', 'Ast', 'Ast/90', 'xAG', 'xAG/90']]
    
    fig_assists = go.Figure()
    fig_assists.add_trace(go.Bar(
        name='Passes décisives',
        x=top_assists['Player'],
        y=top_assists['Ast'],
        marker_color='#2ca02c'
    ))
    fig_assists.add_trace(go.Bar(
        name='xAG',
        x=top_assists['Player'],
        y=top_assists['xAG'],
        marker_color='#d62728'
    ))
    
    fig_assists.update_layout(
        title='Top 5 Passeurs',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_assists, use_container_width=True)
    
    # Top 5 créateurs de chances
    st.write("### Top 5 Créateurs de Chances")
    top_creators = key_players_df.nlargest(5, 'SCA')[['Player', 'SCA', 'GCA', 'SCA/90', 'GCA/90']]
    
    fig_creators = go.Figure()
    fig_creators.add_trace(go.Bar(
        name='Actions de création',
        x=top_creators['Player'],
        y=top_creators['SCA'],
        marker_color='#9467bd'
    ))
    fig_creators.add_trace(go.Bar(
        name='Actions de création de buts',
        x=top_creators['Player'],
        y=top_creators['GCA'],
        marker_color='#8c564b'
    ))
    
    fig_creators.update_layout(
        title='Top 5 Créateurs de Chances',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_creators, use_container_width=True)

def analyze_ucl_player_match():
    """Analyse détaillée des performances par joueur pour chaque match de Ligue des Champions"""
    data = load_ucl_data()
    
    st.subheader("Analyse détaillée par joueur")
    
    # Sélection du match
    match_names = sorted(data.keys(), key=lambda x: data[x]['Ordre'].iloc[0])
    selected_match = st.selectbox("Sélectionnez un match", match_names, key="ucl_player_match_select")
    
    match_data = data[selected_match]
    
    # Affichage du score et de la phase
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Score", match_data['Score'].iloc[0])
    with col2:
        st.metric("Phase", match_data['Phase'].iloc[0])
    
    # Sélection du joueur
    player_names = match_data['Player'].tolist()
    selected_player = st.selectbox("Sélectionnez un joueur", player_names, key="ucl_player_select")
    
    player_data = match_data[match_data['Player'] == selected_player].iloc[0]
    
    # Métriques détaillées
    st.write("### Métriques détaillées")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Minutes jouées", player_data['Min'])
        st.metric("Buts", player_data['Gls'])
        st.metric("xG", f"{player_data['xG']:.2f}")
        st.metric("Tirs", player_data['Sh'])
        st.metric("Tirs cadrés", player_data['SoT'])
    
    with col2:
        st.metric("Passes décisives", player_data['Ast'])
        st.metric("xAG", f"{player_data['xAG']:.2f}")
        st.metric("Actions de création", player_data['SCA'])
        st.metric("Actions de création de buts", player_data['GCA'])
    
    with col3:
        st.metric("Passes progressives", player_data['PrgP'])
        st.metric("Progression portée", player_data['PrgC'])
    
    # Graphique radar des performances
    st.write("### Profil de performance")
    
    # Utilisation des noms de colonnes exacts
    metrics = {
        'Gls': player_data['Gls'],
        'Ast': player_data['Ast'],
        'xG': player_data['xG'],
        'xAG': player_data['xAG'],
        'SoT': player_data['SoT'],
        'SCA': player_data['SCA'],
        'GCA': player_data['GCA'],
        'PrgP': player_data['PrgP']
    }
    
    # Noms d'affichage pour le graphique
    display_names = {
        'Gls': 'Buts',
        'Ast': 'Passes décisives',
        'xG': 'xG',
        'xAG': 'xAG',
        'SoT': 'Tirs cadrés',
        'SCA': 'Actions de création',
        'GCA': 'Actions de création de buts',
        'PrgP': 'Passes progressives'
    }
    
    # Normalisation des valeurs pour le graphique radar
    max_values = {
        'Gls': 3,
        'Ast': 2,
        'xG': 2,
        'xAG': 2,
        'SoT': 5,
        'SCA': 8,
        'GCA': 3,
        'PrgP': 15
    }
    
    normalized_metrics = {display_names[k]: (v / max_values[k]) * 100 for k, v in metrics.items()}
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(normalized_metrics.values()),
        theta=list(normalized_metrics.keys()),
        fill='toself',
        name=selected_player
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title=f'Profil de performance - {selected_player} vs {selected_match} ({match_data["Score"].iloc[0]})',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Comparaison avec la moyenne de l'équipe pour ce match
    st.write("### Comparaison avec la moyenne de l'équipe")
    
    team_avg = match_data[metrics.keys()].mean()
    
    comparison_data = pd.DataFrame({
        'Métrique': [display_names[k] for k in metrics.keys()],
        'Joueur': list(metrics.values()),
        'Moyenne Équipe': team_avg.values
    })
    
    fig_comparison = go.Figure()
    fig_comparison.add_trace(go.Bar(
        name='Joueur',
        x=comparison_data['Métrique'],
        y=comparison_data['Joueur'],
        marker_color='#1f77b4'
    ))
    
    fig_comparison.add_trace(go.Bar(
        name='Moyenne Équipe',
        x=comparison_data['Métrique'],
        y=comparison_data['Moyenne Équipe'],
        marker_color='#ff7f0e'
    ))
    
    fig_comparison.update_layout(
        title=f'Comparaison avec la moyenne de l\'équipe - {selected_match} ({match_data["Score"].iloc[0]})',
        barmode='group',
        showlegend=True
    )
    
    st.plotly_chart(fig_comparison, use_container_width=True)

def analyze_ucl_performance():
    """Analyse des performances en Ligue des Champions"""
    data = load_ucl_data()
    
    st.header("Analyse Ligue des Champions")
    
    analysis_type = st.radio(
        "Choisissez une analyse :",
        ("Analyse Match par Match", "Progression dans la compétition", "Performances clés des joueurs", "Analyse détaillée par joueur"),
        key="ucl_analysis_radio"
    )
    
    if analysis_type == "Analyse Match par Match":
        # Sélection du match
        match_names = sorted(data.keys(), key=lambda x: data[x]['Ordre'].iloc[0])
        selected_match = st.selectbox("Sélectionnez un match", match_names, key="ucl_match_select")
        
        match_data = data[selected_match]
        
        # Affichage du score et de la phase
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Score", match_data['Score'].iloc[0])
        with col2:
            st.metric("Phase", match_data['Phase'].iloc[0])
        
        # Statistiques du match
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_goals = match_data['Gls'].sum()
            total_xg = match_data['xG'].sum()
            st.metric("Buts marqués", total_goals)
            st.metric("xG total", f"{total_xg:.2f}")
        
        with col2:
            total_assists = match_data['Ast'].sum()
            total_xag = match_data['xAG'].sum()
            st.metric("Passes décisives", total_assists)
            st.metric("xAG total", f"{total_xag:.2f}")
        
        with col3:
            total_shots = match_data['Sh'].sum()
            shots_on_target = match_data['SoT'].sum()
            st.metric("Tirs totaux", total_shots)
            st.metric("Tirs cadrés", shots_on_target)
        
        # Graphique des performances individuelles
        st.subheader("Performances individuelles")
        
        performance_data = match_data[['Player', 'Gls', 'Ast', 'xG', 'xAG', 'Sh', 'SoT']]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Buts',
            x=performance_data['Player'],
            y=performance_data['Gls'],
            marker_color='#1f77b4'
        ))
        fig.add_trace(go.Bar(
            name='Passes décisives',
            x=performance_data['Player'],
            y=performance_data['Ast'],
            marker_color='#ff7f0e'
        ))
        
        fig.update_layout(
            title=f'Buts et Passes décisives par joueur - {selected_match} ({match_data["Score"].iloc[0]})',
            barmode='group',
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Analyse des actions de création
        st.subheader("Actions de création")
        
        creation_data = match_data[['Player', 'SCA', 'GCA', 'PrgP', 'PrgC']]
        
        fig_creation = go.Figure()
        fig_creation.add_trace(go.Bar(
            name='Actions de création',
            x=creation_data['Player'],
            y=creation_data['SCA'],
            marker_color='#2ca02c'
        ))
        fig_creation.add_trace(go.Bar(
            name='Actions de création de buts',
            x=creation_data['Player'],
            y=creation_data['GCA'],
            marker_color='#d62728'
        ))
        
        fig_creation.update_layout(
            title=f'Actions de création par joueur - {selected_match} ({match_data["Score"].iloc[0]})',
            barmode='group',
            showlegend=True
        )
        
        st.plotly_chart(fig_creation, use_container_width=True)
    
    elif analysis_type == "Progression dans la compétition":
        analyze_ucl_progression()
    
    elif analysis_type == "Performances clés des joueurs":
        analyze_ucl_key_players()
    
    else:  # Analyse détaillée par joueur
        analyze_ucl_player_match()

def render_home():
    # Enveloppement du logo et du titre dans un conteneur centré via HTML/CSS
    centered_header = """
    <div style='text-align: center;'>
        <img src='https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg' width='100' style='display: block; margin: 0 auto;'>
        <h1 style='text-align: center;'>PSG Data Center - Saison 2024-2025</h1>
    </div>
    """
    st.markdown(centered_header, unsafe_allow_html=True)

    # Onglets principaux regroupés
    tab_overview, tab_individual, tab_collective, tab_ucl, tab_goalkeeping = st.tabs([
        "Vue d'ensemble",
        "Analyse individuelle",
        "Analyse collective",
        "🏆 Ligue des Champions",
        "🧤 Analyse Gardiens"
    ])

    with tab_overview:
        render_overview()

    with tab_individual:
        st.subheader("Analyse individuelle des joueurs")
        analysis_type = st.radio(
            "Choisissez une analyse :",
            ("Analyse par joueur", "Comparaisons", "Rôles et Profils", "Performances par Match"),
            key="individual_analysis_radio"
        )
        if analysis_type == "Analyse par joueur":
            render_player_analysis()
        elif analysis_type == "Comparaisons":
            render_comparisons()
        elif analysis_type == "Rôles et Profils":
            analyze_player_roles()
        elif analysis_type == "Performances par Match":
            analyze_match_performance()

    with tab_collective:
        st.subheader("Analyse collective et tactique")
        analysis_type = st.radio(
            "Choisissez une analyse :",
            ("Analyse par position", "Analyse Tactique", "Forces et Faiblesses", "Dynamiques d'Équipe", "Patterns Tactiques", "Analyse Défensive"),
            key="collective_analysis_radio"
        )
        if analysis_type == "Analyse par position":
            render_position_analysis()
        elif analysis_type == "Analyse Tactique":
            analyze_tactical_performance()
        elif analysis_type == "Forces et Faiblesses":
            analyze_team_strengths()
        elif analysis_type == "Dynamiques d'Équipe":
            analyze_team_dynamics()
        elif analysis_type == "Patterns Tactiques":
            analyze_tactical_patterns()
        elif analysis_type == "Analyse Défensive":
            analyze_defensive_metrics()

    with tab_ucl:
        analyze_ucl_performance()

    with tab_goalkeeping:
        analyze_goalkeeping_performance()

if __name__ == "__main__":
    render_home()

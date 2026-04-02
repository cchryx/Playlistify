"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

Visualizes the song recommendation algorithm as an interactive 3D graph,
showing seed songs, their neighbours, and final recommendations as
colour-coded nodes. Built using NetworkX and Plotly.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

from __future__ import annotations

import networkx as nx
import plotly.graph_objects as go

from song_graph import Song, SongGraph

# Constants
LINE_COLOUR = 'rgb(210, 210, 210)'
VERTEX_BORDER_COLOUR = 'rgb(50, 50, 50)'

SEED_COLOUR = 'rgb(105, 89, 205)'  # Purple: seed songs
NEIGHBOUR_COLOUR = 'rgb(89, 175, 205)'  # Blue: seed song neighbours
FINAL_COLOUR = 'rgb(89, 205, 105)'  # Green: songs in final recommendation


def build_graph_nx(seed_songs: list[Song],
                   song_graph: SongGraph,
                   final_songs: set[Song]) -> tuple[nx.Graph, dict]:
    """Build and return a NetworkX graph of the seed songs and its neighbours.

    Also returns a dictionary, where keys are nodes of the returned graph,
    and values are their respective colour based on whether it's a seed, final
    recommendation song or neighbour.
    """
    graph_nx = nx.Graph()
    colours = {}

    # add seed nodes
    for song in seed_songs:
        graph_nx.add_node(song.track_id, song=song)
        colours[song.track_id] = SEED_COLOUR

    # add neighbour nodes and edges
    for song in seed_songs:
        _add_neighbours_to_graph(song, song_graph, graph_nx, colours, final_songs)

    return graph_nx, colours


def _add_neighbours_to_graph(song: Song, song_graph: SongGraph,
                             graph_nx: nx.Graph, colours: dict,
                             final_songs: set[Song]) -> None:
    """Helper to process and add all neighbours of a song to the NetworkX graph.

    This flattens the nested loops in build_graph_nx to pass PythonTA.
    """
    for neighbour in song_graph.get_neighbours(song):
        weight = song_graph.get_weight(song, neighbour)

        if neighbour.track_id not in graph_nx:
            graph_nx.add_node(neighbour.track_id, song=neighbour)

            # Determine color
            if neighbour in final_songs:
                colours[neighbour.track_id] = FINAL_COLOUR
            else:
                colours[neighbour.track_id] = NEIGHBOUR_COLOUR

        graph_nx.add_edge(song.track_id, neighbour.track_id, weight=weight)


def build_hover_labels(graph_nx: nx.Graph,
                       seed_ids: set[str]) -> list[str]:
    """Return a list of hover labels for each node in graph_nx.

    Each label contains the track name, artist, genre, popularity and similarity
    scores (only for neighbours).
    """
    labels = []

    for node_id in graph_nx.nodes:
        song = graph_nx.nodes[node_id]['song']

        if node_id in seed_ids:
            # Seed song label logic
            label = (
                f"<b>{song.track_name}</b><br>"
                f"Artist: {song.artist_name}<br>"
                f"Genre: {song.genre}<br>"
                f"Popularity: {song.popularity}<br>"
                f"[Seed song]"
            )
        else:
            # Neighbour song label logic (similarity calculated in helper)
            highest_weight = _get_highest_similarity(graph_nx, node_id, seed_ids)
            label = (
                f"<b>{song.track_name}</b><br>"
                f"Artist: {song.artist_name}<br>"
                f"Genre: {song.genre}<br>"
                f"Popularity: {song.popularity}<br>"
                f"Similarity: {highest_weight:.4f}"
            )

        labels.append(label)

    return labels


def _get_highest_similarity(graph_nx: nx.Graph, node_id: str,
                            seed_ids: set[str]) -> float:
    """Return the highest edge weight between node_id and any of the seed_ids.

    Used to calculate the similarity score for neighbour nodes in the 3D graph.
    """
    highest_weight = 0.0
    for seed_id in seed_ids:
        if graph_nx.has_edge(node_id, seed_id):
            weight = float(graph_nx.edges[node_id, seed_id]['weight'])
            if weight > highest_weight:
                highest_weight = weight
    return highest_weight


def run_visualization(seed_songs: list[Song],
                      graph: SongGraph,
                      final_songs: set[Song]) -> None:
    """Use plotly and networkx to build a 3D visualization of the given graph.

    The graph opens on the user's web browser, supports zoom and 360-degree rotation.
    """
    seed_ids = {song.track_id for song in seed_songs}
    graph_nx, colours = build_graph_nx(seed_songs, graph, final_songs)

    # 1. Compute Layout and Coordinates
    pos = nx.spring_layout(graph_nx, dim=3, seed=37)
    node_data = _get_node_coordinates(graph_nx, pos)
    edge_coords = _get_edge_coordinates(graph_nx, pos)

    # 2. Build Hover Labels and Colors
    labels = build_hover_labels(graph_nx, seed_ids)
    color_list = [colours[k] for k in graph_nx.nodes]
    sizes = [8 if colours[k] == SEED_COLOUR else 4 for k in graph_nx.nodes]

    # 3. Create Traces via Helpers
    edge_trace = _build_edge_trace(edge_coords)
    node_trace = _build_node_trace(node_data, color_list, sizes, labels)

    # 4. Final Figure Assembly
    fig = go.Figure(data=[edge_trace, node_trace])
    _apply_layout_styling(fig, len(graph_nx.nodes), len(seed_songs))
    fig.show()


def _get_node_coordinates(graph_nx: nx.Graph, pos: dict) -> tuple:
    """Extract x, y, z coordinates for nodes from the layout position."""
    x_vals = [float(pos[k][0]) for k in graph_nx.nodes]
    y_vals = [float(pos[k][1]) for k in graph_nx.nodes]
    z_vals = [float(pos[k][2]) for k in graph_nx.nodes]
    return (x_vals, y_vals, z_vals)


def _get_edge_coordinates(graph_nx: nx.Graph, pos: dict) -> tuple:
    """Extract x, y, z coordinates for edges, using None to break line segments."""
    x_e, y_e, z_e = [], [], []
    for edge in graph_nx.edges:
        x_e += [float(pos[edge[0]][0]), float(pos[edge[1]][0]), None]
        y_e += [float(pos[edge[0]][1]), float(pos[edge[1]][1]), None]
        z_e += [float(pos[edge[0]][2]), float(pos[edge[1]][2]), None]
    return (x_e, y_e, z_e)


def _build_edge_trace(coords: tuple) -> go.Scatter3d:
    """Return the Plotly Scatter3d trace for graph edges."""
    return go.Scatter3d(
        x=coords[0], y=coords[1], z=coords[2],
        mode='lines', name='edges',
        line={'color': LINE_COLOUR, 'width': 0.5},
        hoverinfo='none'
    )


def _build_node_trace(coords: tuple, colors: list,
                      sizes: list, labels: list) -> go.Scatter3d:
    """Return the Plotly Scatter3d trace for graph nodes."""
    return go.Scatter3d(
        x=coords[0], y=coords[1], z=coords[2],
        mode='markers', name='nodes',
        marker={
            'size': sizes,
            'color': colors,
            'opacity': 0.9,
            'line': {'color': VERTEX_BORDER_COLOUR, 'width': 0.3}
        },
        text=labels, hovertemplate='%{text}<extra></extra>',
        hoverlabel={'namelength': -1}
    )


def _apply_layout_styling(fig: go.Figure, total: int, seeds: int) -> None:
    """Apply visual styling and titles to the Plotly figure."""
    title_text = (f'Playlistify - Recommendation Graph | '
                  f'{total} nodes | {total - seeds} neighbours')

    fig.update_layout(
        title={
            'text': title_text,
            'font': {'size': 14, 'color': 'white'}
        },
        showlegend=False,
        paper_bgcolor='rgb(20, 20, 35)',
        scene={
            'bgcolor': 'rgb(20, 20, 35)',
            'xaxis': {'showgrid': False, 'zeroline': False, 'visible': False},
            'yaxis': {'showgrid': False, 'zeroline': False, 'visible': False},
            'zaxis': {'showgrid': False, 'zeroline': False, 'visible': False},
        }
    )


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['networkx', 'plotly.graph_objects', 'song_graph'],
        'allowed-io': [],
    })

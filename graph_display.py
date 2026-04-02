"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

Visualizes the song recommendation algorithm as an interactive 3D graph,
showing seed songs, their neighbours, and final recommendations as
colour-coded nodes. Built using NetworkX and Plotly.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

from __future__ import annotations

import networkx as nx
from plotly.graph_objs import Figure, Scatter3d

from song_graph import Song, SongGraph

# constants
LINE_COLOUR = 'rgb(210, 210, 210)'
VERTEX_BORDER_COLOUR = 'rgb(50, 50, 50)'

SEED_COLOUR = 'rgb(105, 89, 205)'  # purple: seed songs
NEIGHBOUR_COLOUR = 'rgb(89, 175, 205)'  # blue: seed song neighbours
FINAL_COLOUR = 'rgb(89, 205, 105)'  # green: songs in final recommendation


def build_graph_nx(seed_songs: list[Song],
                   song_graph: SongGraph,
                   final_songs: set[Song]) -> tuple[nx.Graph, dict]:
    """Build and return a NetworkX graph of the seed songs and its neighbours.

    Also returns a dictionary, where keys are nodes of the returned grpah,
    and values are their respective colour based on whether its a seed, final
    recommenation song or neighbour

    """
    graph_nx = nx.Graph()
    colours = {}

    # add seed nodes
    for song in seed_songs:
        graph_nx.add_node(song.track_id, song=song)
        colours[song.track_id] = SEED_COLOUR

    # add neighbour nodes and edges
    for song in seed_songs:
        for neighbour in song_graph.get_neighbours(song):
            weight = song_graph.get_weight(song, neighbour)

            if neighbour.track_id not in graph_nx:
                graph_nx.add_node(neighbour.track_id, song=neighbour)

                if neighbour in final_songs:
                    colours[neighbour.track_id] = FINAL_COLOUR
                else:
                    colours[neighbour.track_id] = NEIGHBOUR_COLOUR

            graph_nx.add_edge(song.track_id, neighbour.track_id, weight=weight)

    return graph_nx, colours


def build_hover_labels(graph_nx: nx.Graph,
                       seed_ids: set[str]) -> list[str]:
    """Return a list of hover labels for each node in graph_nx.

    Each label contains the track name, artist, genre, popularity and similarity
    scores (only for neighbours).
    """

    labels = []

    for node_id in graph_nx.nodes:
        song = graph_nx.nodes[node_id]['song']

        if node_id in seed_ids:  # if this node is a seed
            label = (
                f"<b>{song.track_name}</b><br>"
                f"Artist: {song.artist_name}<br>"
                f"Genre: {song.genre}<br>"
                f"Popularity: {song.popularity}<br>"
                f"[Seed song]"
            )
        else:  # if this node is a neighbour, need its weight
            highest_weight = 0.0
            for seed_id in seed_ids:
                if graph_nx.has_edge(node_id, seed_id):
                    weight = float(graph_nx.edges[node_id, seed_id]['weight'])
                    if weight > highest_weight:
                        highest_weight = weight

            label = (
                f"<b>{song.track_name}</b><br>"
                f"Artist: {song.artist_name}<br>"
                f"Genre: {song.genre}<br>"
                f"Popularity: {song.popularity}<br>"
                f"Similarity: {highest_weight:.4f}"
            )

        labels.append(label)

    return labels


def run_visualization(seed_songs: list[Song],
                      graph: SongGraph,
                      final_songs: set[Song]) -> None:
    """Use plotly and networkx to build a 3D visualization of the given graph.

    The graph opens on the user's web browser, supports zoom and 360-degree rotation

    Nodes are colours by song type:
        - Purple: seed songs generated using the recommendation algorithm
        - Green: final recommended songs
        - Blue: other seed song neighbours that were explored but not on the final recommendation

    Hovering over any node shows its song information, including the track name, artist, genre, popularity and similarity
    scores (only for neighbours)
    """

    seed_ids = {song.track_id for song in seed_songs}

    graph_nx, colours = build_graph_nx(seed_songs, graph, final_songs)

    # builds 3D spring layout with a constant seed
    pos = nx.spring_layout(graph_nx, dim=3, seed=37)

    # x/y/z coords
    x_values = [float(pos[k][0]) for k in graph_nx.nodes]
    y_values = [float(pos[k][1]) for k in graph_nx.nodes]
    z_values = [float(pos[k][2]) for k in graph_nx.nodes]

    # colour list
    color_list = [colours[k] for k in graph_nx.nodes]

    # build hover labels
    labels = build_hover_labels(graph_nx, seed_ids)

    # edge connections
    x_edges = []
    y_edges = []
    z_edges = []
    for edge in graph_nx.edges:
        x_edges += [float(pos[edge[0]][0]), float(pos[edge[1]][0]), None]
        y_edges += [float(pos[edge[0]][1]), float(pos[edge[1]][1]), None]
        z_edges += [float(pos[edge[0]][2]), float(pos[edge[1]][2]), None]

    # trace 1: edges
    edge_trace = Scatter3d(
        x=x_edges,
        y=y_edges,
        z=z_edges,
        mode='lines',
        name='edges',
        line=dict(color=LINE_COLOUR, width=0.5),
        hoverinfo='none'
    )

    # trace 2: nodes
    node_trace = Scatter3d(
        x=x_values,
        y=y_values,
        z=z_values,
        mode='markers',
        name='nodes',
        marker=dict(
            size=[8 if colours[k] == SEED_COLOUR else 4 for k in graph_nx.nodes],
            color=color_list,
            line=dict(color=VERTEX_BORDER_COLOUR, width=0.3),
            opacity=0.9
        ),
        text=labels,
        hovertemplate='%{text}<extra></extra>',
        hoverlabel={'namelength': -1}
    )

    # titles
    total_nodes = len(graph_nx.nodes)
    total_neighbours = total_nodes - len(seed_songs)

    fig = Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=dict(
            text=(
                f'Playlistify - Song Recommendation Graph  |  '
                f'{total_nodes} nodes  |  {total_neighbours} neighbours explored'
            ),
            font=dict(size=14, color='white')
        ),
        showlegend=False,
        paper_bgcolor='rgb(20, 20, 35)',
        scene=dict(
            bgcolor='rgb(20, 20, 35)',
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            zaxis=dict(showgrid=False, zeroline=False, visible=False),
        )
    )

    fig.show()

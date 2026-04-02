"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

GUI module — white-themed multi-page survey with genre tree explorer,
user preference collection, and playlist results display.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

import math
import threading
import tkinter as tk
from tkinter import font as tkfont
from typing import Optional

from genre_tree import GENRE_HIERARCHY, GenreTree, load_genre_tree
import graph_visualization
import song_graph as sg

# ── Palette (white theme) ──────────────────────────────────────────────────────
BG = "#FFFFFF"
SURFACE = "#F5F5F5"
BORDER = "#E0E0E0"
BORDER_DARK = "#BDBDBD"
ACCENT = "#1DB954"
ACCENT_DIM = "#158a3e"
TEXT = "#212121"
TEXT_DIM = "#757575"
TAG_BG = "#E8F5E9"
TAG_BORDER = "#1DB954"
DROP_BG = "#FFFFFF"

BUBBLE_COLORS = {
    0: ("#E8F5E9", "#1B5E20"),
    1: ("#E8F5E9", "#1B5E20"),
    2: ("#F1F8E9", "#33691E"),
}

ALL_GENRES = sorted(GENRE_HIERARCHY.keys())
MAX_DROP = 6
VIRAL_THRESHOLD = 10


# ── Build children map ────────────────────────────────────────────────────────
def _build_children() -> dict[str, list[str]]:
    """Build and return a mapping from each genre to its list of direct child genres.

    Iterates over GENRE_HIERARCHY to invert the child->parent relationship into a
    parent->[children] lookup. The special 'root' key collects all top-level genres.
    """
    children: dict[str, list[str]] = {"root": []}
    for genre in GENRE_HIERARCHY:
        children[genre] = []
    for genre, parent in GENRE_HIERARCHY.items():
        children[parent].append(genre)
    return children


CHILDREN = _build_children()


class PlaylistifyApp(tk.Tk):
    """The root Tkinter window for the Playlistify application.

    Manages a stack of pages (tk.Frame instances) that are shown and hidden
    one at a time. Pages are indexed as follows:
        0 — Genre selection (search bar + tag chips)
        1 — Genre tree explorer (bubble canvas, accessible via Browse button only)
        2 — Viral / popularity preference
        3 — Energy level slider
        4 — Playlist size input + Generate button
        5 — Results (scrollable playlist)

    Instance Attributes:
        - preferred_genres: The list of genre strings selected by the user.
        - preferred_viral: Whether the user wants popular songs (popularity >= VIRAL_THRESHOLD).
        - preferred_energy: The minimum energy level the user wants, normalized to [0.0, 1.0].
        - recommend_n_songs: The number of songs to include in the final playlist.
        - pages: The ordered list of page frames registered in the window.
        - current_page: The index of the currently visible page.

    Representation Invariants:
        - 0 <= self.current_page < len(self.pages)
        - 0.0 <= self.preferred_energy <= 1.0
        - self.recommend_n_songs >= 0
    """

    # Instance Attributes
    # User preferences
    preferred_genres: list[str]
    preferred_viral: bool
    preferred_energy: float
    recommend_n_songs: int

    # Data structures (None until first Generate run)
    _tree_genre: Optional[GenreTree]
    _graph_song: Optional[sg.SongGraph]
    _seed_songs: list[tuple[int, sg.Song]]
    _final_songs: list[tuple[float, str, str]]

    # Genre tree explorer state
    _tree_path: list[str]
    _tree_current: str

    # Page management
    pages: list[tk.Frame]
    current_page: int
    dots: list[tk.Label]

    # Font attributes (assigned in _build_fonts)
    font_title: tkfont.Font
    font_label: tkfont.Font
    font_small: tkfont.Font
    font_input: tkfont.Font
    font_nav: tkfont.Font
    font_tag: tkfont.Font
    font_bubble: tkfont.Font
    font_result: tkfont.Font
    font_big_num: tkfont.Font

    # Navigation bar (assigned in _build_nav)
    dot_frame: tk.Frame
    dots: list[tk.Label]

    # Page 0 - Genre selection (assigned in _build_page_genre)
    genre_var: tk.StringVar
    search_entry: tk.Entry
    drop_frame: tk.Frame
    drop_lb: tk.Listbox
    tag_frame: tk.Frame

    # Page 1 - Genre tree explorer (assigned in _build_page_tree)
    tree_back_btn: tk.Button
    tree_breadcrumb: tk.Label
    tree_canvas: tk.Canvas

    # Page 2 - Viral preference (assigned in _build_page_viral)
    _viral_yes: tk.Button
    _viral_no: tk.Button

    # Page 3 - Energy level (assigned in _build_page_energy)
    energy_var: tk.IntVar
    energy_label: tk.Label

    # Page 4 - Playlist size + Generate (assigned in _build_page_count)
    count_var: tk.StringVar
    gen_btn: tk.Button
    gen_status: tk.Label

    # Page 5 - Results (assigned in _build_page_results)
    results_subtitle: tk.Label
    results_canvas: tk.Canvas
    results_inner: tk.Frame
    viz_btn: tk.Button

    def __init__(self) -> None:
        """Initialize the Playlistify window, build all pages, and display page 0.

        Sets up the fixed 720x820 window, initializes user preference state to
        sensible defaults, builds all six pages and the bottom navigation bar,
        and shows the genre selection page.
        """
        super().__init__()
        self.title("Playlistify")
        self.geometry("720x820")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.preferred_genres = []
        self.preferred_viral = False
        self.preferred_energy = 0.5
        self.recommend_n_songs = 10

        self._tree_genre = None
        self._graph_song = None
        self._seed_songs = []
        self._final_songs = []

        self._tree_path = []
        self._tree_current = "root"

        self._build_fonts()

        self.pages = []
        self.current_page = 0

        self._build_page_genre()  # 0
        self._build_page_tree()  # 1
        self._build_page_viral()  # 2
        self._build_page_energy()  # 3
        self._build_page_count()  # 4
        self._build_page_results()  # 5
        self._build_nav()

        self._show_page(0)

    # fonts
    def _build_fonts(self) -> None:
        """Initialize and store all tkinter Font objects used across the application.

        Fonts are assigned as instance attributes so every page builder method
        can reference them without re-creating Font objects repeatedly.
        """
        self.font_title = tkfont.Font(family="Georgia", size=24, weight="bold")
        self.font_label = tkfont.Font(family="Georgia", size=16)
        self.font_small = tkfont.Font(family="Georgia", size=12)
        self.font_input = tkfont.Font(family="Courier New", size=16)
        self.font_nav = tkfont.Font(family="Georgia", size=18, weight="bold")
        self.font_tag = tkfont.Font(family="Georgia", size=12, weight="bold")
        self.font_bubble = tkfont.Font(family="Georgia", size=12, weight="bold")
        self.font_result = tkfont.Font(family="Georgia", size=14)
        self.font_big_num = tkfont.Font(family="Georgia", size=44, weight="bold")

    # navigation
    def _build_nav(self) -> None:
        """Build and place the bottom navigation bar with back/forward arrows and progress dots.

        The bar is fixed at the bottom of the window. Page 1 (genre tree explorer)
        is excluded from arrow navigation and is only reachable via the Browse button
        on page 0. The four dots track progress across pages 0, 2, 3, and 4/5.
        """
        nav = tk.Frame(self, bg=SURFACE, height=64,
                       highlightbackground=BORDER, highlightthickness=1)
        nav.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0, height=64)

        tk.Button(nav, text="←", font=self.font_nav, bg=SURFACE, fg=TEXT,
                  relief="flat", bd=0, activebackground=BORDER,
                  activeforeground=ACCENT, cursor="hand2",
                  command=self._prev_page, width=3
                  ).place(x=16, rely=0.5, anchor="w")

        tk.Button(nav, text="→", font=self.font_nav, bg=SURFACE, fg=TEXT,
                  relief="flat", bd=0, activebackground=BORDER,
                  activeforeground=ACCENT, cursor="hand2",
                  command=self._next_page, width=3
                  ).place(relx=1.0, x=-16, rely=0.5, anchor="e")

        self.dot_frame = tk.Frame(nav, bg=SURFACE)
        self.dot_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.dots = []
        for _ in range(4):
            d = tk.Label(self.dot_frame, text="●", bg=SURFACE,
                         font=tkfont.Font(size=8))
            d.pack(side="left", padx=4)
            self.dots.append(d)
        self._update_dots()

    def _dot_index(self) -> int:
        """Return the progress-dot index (0–3) corresponding to the current page.

        Pages 0 and 1 both map to dot 0, since the tree explorer is a side-branch
        of page 0. Page 5 (results) shares dot 3 with page 4 (generate).
        """
        return {0: 0, 1: 0, 2: 1, 3: 2, 4: 3, 5: 3}.get(self.current_page, 0)

    def _update_dots(self) -> None:
        """Highlight the progress dot that corresponds to the current page.

        The active dot is colored with ACCENT; all others use BORDER_DARK.
        """
        di = self._dot_index()
        for i, d in enumerate(self.dots):
            d.configure(fg=ACCENT if i == di else BORDER_DARK)

    def _show_page(self, index: int) -> None:
        """Hide every page and display the page at the given index.

        Also updates the progress dots to reflect the new current page.

        Preconditions:
            - 0 <= index < len(self.pages)
        """
        for p in self.pages:
            p.place_forget()
        self.pages[index].place(x=0, y=0, width=720, height=756)
        self.current_page = index
        self._update_dots()

    def _prev_page(self) -> None:
        """Navigate to the previous page, skipping page 1 (genre tree explorer).

        Page 1 is only reachable via the Browse button on page 0, not by arrow
        navigation. From page 2 the back arrow therefore returns to page 0 directly.
        """
        # Page 1 (tree explorer) is only reachable via the Browse button, not arrow nav
        if self.current_page == 2:
            self._show_page(0)
        elif self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _next_page(self) -> None:
        """Navigate to the next page, skipping page 1 (genre tree explorer).

        Page 1 is only reachable via the Browse button on page 0, not by arrow
        navigation. From page 0 the next arrow therefore jumps to page 2 directly.
        """
        # Skip page 1 (tree explorer) when using arrow nav
        if self.current_page == 0:
            self._show_page(2)
        elif self.current_page < len(self.pages) - 1:
            self._show_page(self.current_page + 1)

    # page 0 - Genre selection
    def _build_page_genre(self) -> None:
        """Build and register page 0 — the genre selection page.

        Contains a search bar with live-filtered dropdown, a Browse button that
        opens the genre tree explorer (page 1), and a tag-chip area showing all
        currently selected genres. Users may add genres by typing and pressing
        Enter or by clicking a dropdown suggestion, and remove them via the x chip.
        """
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Playlistify", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=78, anchor="center")
        tk.Label(page, text="What genres are you in the mood for?",
                 font=self.font_label, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=118, anchor="center")

        # search bar
        sf = tk.Frame(page, bg=BORDER_DARK, padx=1, pady=1)
        sf.place(relx=0.5, y=178, anchor="center", width=520, height=54)
        inner = tk.Frame(sf, bg=BG)
        inner.pack(fill="both", expand=True)

        self.genre_var = tk.StringVar()
        self.genre_var.trace_add("write", self._on_genre_type)

        self.search_entry = tk.Entry(inner, textvariable=self.genre_var,
                                     font=self.font_input, bg=BG, fg=TEXT_DIM,
                                     insertbackground=ACCENT, relief="flat", bd=8)
        self.search_entry.pack(fill="both", expand=True)
        self.search_entry.insert(0, "Search genres…")
        self.search_entry.bind("<Return>", self._on_genre_enter)
        self.search_entry.bind("<Down>", self._drop_focus_first)
        self.search_entry.bind("<Escape>", lambda _: self._hide_dropdown())
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)

        # dropdown
        self.drop_frame = tk.Frame(page, bg=BORDER_DARK, padx=1, pady=1)
        self.drop_lb = tk.Listbox(self.drop_frame, font=self.font_input,
                                  bg=DROP_BG, fg=TEXT,
                                  selectbackground=ACCENT, selectforeground=BG,
                                  relief="flat", bd=0, activestyle="none",
                                  highlightthickness=0, exportselection=False)
        self.drop_lb.pack(fill="both", expand=True, padx=1, pady=1)
        self.drop_lb.bind("<Return>", self._on_drop_select)
        self.drop_lb.bind("<Double-Button-1>", self._on_drop_select)
        self.drop_lb.bind("<Escape>", lambda _: self._hide_dropdown())
        self.drop_lb.bind("<Up>", self._drop_up)

        # browse button
        tk.Button(page, text="🎵  Browse genre tree  →",
                  font=self.font_label, bg=SURFACE, fg=ACCENT,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=BORDER, activeforeground=ACCENT_DIM,
                  highlightbackground=BORDER_DARK, highlightthickness=1,
                  padx=18, pady=10,
                  command=lambda: self._show_page(1)
                  ).place(relx=0.5, y=250, anchor="center")

        # divider
        tk.Frame(page, bg=BORDER, height=1).place(
            relx=0.5, y=292, anchor="center", width=520)

        tk.Label(page, text="Selected genres", font=self.font_label,
                 bg=BG, fg=TEXT).place(x=100, y=312)

        self.tag_frame = tk.Frame(page, bg=BG)
        self.tag_frame.place(x=100, y=348, width=520, height=250)

        tk.Label(page, text="Press Enter to add  ·  Click × to remove",
                 font=self.font_small, bg=BG, fg=BORDER_DARK
                 ).place(relx=0.5, y=620, anchor="center")

    def _clear_placeholder(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """Clear the placeholder text when the search entry gains focus."""
        if self.search_entry.get() == "Search genres…":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg=TEXT)

    def _restore_placeholder(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """Restore the placeholder text when the search entry loses focus if empty."""
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search genres…")
            self.search_entry.configure(fg=TEXT_DIM)

    def _on_genre_type(self, *_: object) -> None:
        """Update the dropdown list each time the user types in the search entry.

        Filters ALL_GENRES by substring match against the current query and shows
        up to MAX_DROP results. Hides the dropdown if the query is empty or yields
        no matches.
        """
        query = self.genre_var.get().strip().lower()
        if not query or query == "search genres…":
            self._hide_dropdown()
            return
        matches = [g for g in ALL_GENRES if query in g][:MAX_DROP]
        if not matches:
            self._hide_dropdown()
            return
        self.drop_lb.delete(0, "end")
        for m in matches:
            self.drop_lb.insert("end", m)
        h = min(len(matches), MAX_DROP) * 34 + 2
        self.drop_frame.place(relx=0.5, y=205, anchor="n", width=520, height=h)
        self.drop_frame.lift()

    def _hide_dropdown(self) -> None:
        """Hide the genre search dropdown by removing it from the layout.

        Does nothing if drop_frame has not yet been created, which can occur
        when the StringVar trace fires during widget initialization.
        """
        if hasattr(self, 'drop_frame'):
            self.drop_frame.place_forget()

    def _on_genre_enter(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """Handle the Return key in the search entry.

        If a dropdown item is highlighted it is used; otherwise the raw typed
        text is attempted as a genre name.
        """
        typed = self.genre_var.get().strip().lower()
        sel = self.drop_lb.curselection()
        genre = self.drop_lb.get(sel[0]) if sel else typed
        self._try_add_genre(genre)

    def _on_drop_select(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """Add the currently highlighted dropdown item to the selected genres."""
        sel = self.drop_lb.curselection()
        if sel:
            self._try_add_genre(self.drop_lb.get(sel[0]))

    def _drop_focus_first(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """Move keyboard focus from the search entry into the dropdown listbox.

        Called when the user presses the Down arrow key while the entry is focused,
        allowing them to navigate suggestions without using the mouse.
        """
        if self.drop_lb.size() > 0:
            self.drop_lb.focus_set()
            self.drop_lb.selection_set(0)

    def _drop_up(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        """Return keyboard focus to the search entry when Up is pressed on the first dropdown item."""
        sel = self.drop_lb.curselection()
        if sel and sel[0] == 0:
            self.search_entry.focus_set()

    def _try_add_genre(self, genre: str) -> None:
        """Attempt to add genre to the selected genres list and refresh the tag display.

        The genre is only added if it exists in GENRE_HIERARCHY and has not already
        been selected. After attempting to add, the search entry is cleared and
        the dropdown is hidden.
        """
        if genre in GENRE_HIERARCHY and genre not in self.preferred_genres:
            self.preferred_genres.append(genre)
            self._render_tags()
        self.genre_var.set("")
        self._hide_dropdown()
        self.search_entry.configure(fg=TEXT)
        self.search_entry.focus_set()

    def _render_tags(self) -> None:
        """Re-draw the genre tag chips inside the tag frame on page 0.

        Destroys all existing chip widgets and recreates them from preferred_genres,
        wrapping to a new row when chips would overflow the available width.
        Each chip shows the genre name and an x button that calls _remove_genre.
        """
        for w in self.tag_frame.winfo_children():
            w.destroy()

        x, y = 0, 0
        row_height = 44

        for genre in self.preferred_genres:
            chip = tk.Frame(self.tag_frame, bg=TAG_BG,
                            highlightbackground=TAG_BORDER, highlightthickness=1,
                            bd=0)
            chip.place(x=x, y=y)

            tk.Label(chip, text=genre, font=self.font_tag,
                     bg=TAG_BG, fg=ACCENT_DIM, padx=10, pady=8).pack(side="left")
            tk.Button(chip, text="×", font=self.font_tag,
                      bg=TAG_BG, fg=TEXT_DIM, relief="flat", bd=0,
                      activebackground=TAG_BG, activeforeground="#D32F2F",
                      cursor="hand2", padx=8,
                      command=lambda g=genre: self._remove_genre(g)
                      ).pack(side="left")

            chip.update_idletasks()
            cw = chip.winfo_reqwidth()

            if x + cw > 510 and x > 0:
                x = 0
                y += row_height
                chip.place(x=x, y=y)

            x += cw + 12

    # page 1 - Genre tree explorer
    def _build_page_tree(self) -> None:
        """Build and register page 1 — the genre tree explorer."""
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Explore Genres", font=self.font_title,
                 bg=BG, fg=TEXT).place(relx=0.5, y=48, anchor="center")

        tk.Button(page, text="← Back to Search",
                  font=self.font_small, bg=SURFACE, fg=ACCENT,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=BORDER, highlightbackground=BORDER_DARK,
                  highlightthickness=1,
                  command=lambda: self._show_page(0)
                  ).place(x=30, y=74)

        self.tree_back_btn = tk.Button(page, text="↑ Up",
                                       font=self.font_small, bg=SURFACE, fg=TEXT_DIM,
                                       relief="flat", bd=0, cursor="hand2",
                                       activebackground=BORDER,
                                       highlightbackground=BORDER_DARK,
                                       highlightthickness=1,
                                       command=self._tree_drill_up)
        self.tree_back_btn.place(x=176, y=74)

        self.tree_breadcrumb = tk.Label(page, text="root",
                                        font=self.font_small, bg=BG, fg=TEXT_DIM)
        self.tree_breadcrumb.place(relx=0.5, y=84, anchor="center")

        tk.Label(page,
                 text="Click a bubble to explore sub-genres or select a leaf genre",
                 font=self.font_small, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=112, anchor="center")

        self.tree_canvas = tk.Canvas(page, bg=BG, highlightthickness=0,
                                     width=720, height=600)
        self.tree_canvas.place(x=0, y=132)

        self._tree_render()

    def _tree_render(self) -> None:
        """Redraw the genre tree canvas for the current node (_tree_current)."""
        self.tree_canvas.delete("all")
        children = CHILDREN.get(self._tree_current, [])

        if not children:
            self.tree_canvas.create_text(
                360, 300, text="No sub-genres available.",
                font=self.font_label, fill=TEXT_DIM)
        else:
            depth = len(self._tree_path)
            _, text_col = BUBBLE_COLORS.get(depth, ("#E8F5E9", "#1B5E20"))
            n = len(children)
            w, h = 720, 600
            r = max(28, min(56, int(180 / max(n, 1) ** 0.5)))
            cols = max(1, math.ceil(math.sqrt(n * 1.6)))
            rows = math.ceil(n / cols)
            pad_x = w / (cols + 1)
            pad_y = h / (rows + 1)

            for idx, genre in enumerate(children):
                col = idx % cols
                row = idx // cols
                cx = pad_x * (col + 1)
                cy = pad_y * (row + 1)

                has_ch = bool(CHILDREN.get(genre))
                outline = BORDER_DARK
                lw = 2

                # darker fill for genres with sub-genres, lighter fill for leaf genres
                if has_ch:
                    bubble_fill = "#CFEBD6"
                else:
                    bubble_fill = "#EAF7EE"

                # soft shadow
                self.tree_canvas.create_oval(
                    cx - r + 4, cy - r + 6, cx + r + 4, cy + r + 6,
                    fill="#DADADA", outline=""
                )

                # main bubble
                oid = self.tree_canvas.create_oval(
                    cx - r, cy - r, cx + r, cy + r,
                    fill=bubble_fill, outline=outline, width=lw
                )

                lbl = genre if len(genre) <= 14 else genre[:13] + "…"
                tid = self.tree_canvas.create_text(
                    cx, cy, text=lbl, font=self.font_bubble, fill=text_col, width=r * 1.5
                )

                for item in (oid, tid):
                    self.tree_canvas.tag_bind(
                        item, "<Button-1>",
                        lambda _, g=genre: self._tree_drill_down(g)
                    )
                    self.tree_canvas.tag_bind(
                        item, "<Enter>",
                        lambda _, o=oid: self.tree_canvas.itemconfigure(
                            o, outline=ACCENT, width=3)
                    )
                    self.tree_canvas.tag_bind(
                        item, "<Leave>",
                        lambda _, o=oid, ol=outline, lw2=lw:
                        self.tree_canvas.itemconfigure(o, outline=ol, width=lw2)
                    )

                # only genres with sub-genres get a plus badge for direct selection
                if has_ch:
                    bx, by = cx + r - 12, cy - r + 12

                    self.tree_canvas.create_oval(
                        bx - 10 + 2, by - 10 + 2, bx + 10 + 2, by + 10 + 2,
                        fill="#CFCFCF", outline=""
                    )
                    bid = self.tree_canvas.create_oval(
                        bx - 10, by - 10, bx + 10, by + 10,
                        fill=ACCENT, outline=BORDER_DARK, width=1
                    )
                    pid = self.tree_canvas.create_text(
                        bx, by, text="+",
                        font=tkfont.Font(size=11, weight="bold"), fill="white"
                    )

                    for item in (bid, pid):
                        self.tree_canvas.tag_bind(
                            item, "<Button-1>",
                            lambda _, g=genre: self._tree_add_genre(g)
                        )

        crumb = " › ".join(["root"] + self._tree_path) if self._tree_path else "root"
        self.tree_breadcrumb.configure(text=crumb)
        self.tree_back_btn.configure(
            state="normal" if self._tree_path else "disabled",
            fg=ACCENT if self._tree_path else BORDER_DARK)

    def _tree_drill_down(self, genre: str) -> None:
        """Navigate into genre's sub-genres, or add it directly if it is a leaf.

        If genre has no children in CHILDREN, it is treated as a leaf and added
        to the selected genres via _tree_add_genre. Otherwise, the tree path is
        extended and the canvas is redrawn for the new current node.
        """
        if not CHILDREN.get(genre):
            self._tree_add_genre(genre)
            return
        self._tree_path.append(genre)
        self._tree_current = genre
        self._tree_render()

    def _tree_drill_up(self) -> None:
        """Navigate one level up in the genre tree, returning to the parent node.

        If already at the root level this method does nothing. The canvas is
        redrawn for the new current node after popping the last entry from the path.
        """
        if self._tree_path:
            self._tree_path.pop()
            self._tree_current = self._tree_path[-1] if self._tree_path else "root"
            self._tree_render()

    def _tree_add_genre(self, genre: str) -> None:
        """Add genre to the selected genres list from the tree explorer page.

        If genre is already selected or not in GENRE_HIERARCHY, it is not added
        again. A brief confirmation message is shown on the canvas for 1.8 seconds
        and the tag chips on page 0 are refreshed so the new selection is visible
        when the user returns.
        """
        if genre in GENRE_HIERARCHY and genre not in self.preferred_genres:
            self.preferred_genres.append(genre)
            self._render_tags()
        msg = self.tree_canvas.create_text(
            360, 590, text=f"✓  '{genre}' added to your selection",
            font=self.font_small, fill=ACCENT)
        self.tree_canvas.after(1800, self.tree_canvas.delete, msg)

    # page 2 - Viral preference
    def _build_page_viral(self) -> None:
        """Build and register page 2 — the viral / popularity preference page.

        Presents two pill buttons: 'Yes — give me hits' and 'No — surprise me'.
        The selected button is highlighted in ACCENT. The default selection is
        False (no popularity filter), matching main.py's default.
        """
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Playlistify", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=78, anchor="center")
        tk.Label(page, text="Do you want popular songs?",
                 font=self.font_label, bg=BG, fg=TEXT
                 ).place(relx=0.5, y=250, anchor="center")
        tk.Label(page,
                 text=f"Popular songs have a Spotify popularity score of {VIRAL_THRESHOLD}+  (out of 100)",
                 font=self.font_small, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=286, anchor="center")

        btn_frame = tk.Frame(page, bg=BG)
        btn_frame.place(relx=0.5, y=392, anchor="center")

        self._viral_yes = self._pill_btn(btn_frame, "Yes — give me hits",
                                         lambda: self._set_viral(True))
        self._viral_yes.pack(side="left", padx=18)

        self._viral_no = self._pill_btn(btn_frame, "No — surprise me",
                                        lambda: self._set_viral(False))
        self._viral_no.pack(side="left", padx=18)

        self._set_viral(False)

    def _pill_btn(self, parent: tk.Frame, text: str, cmd: object) -> tk.Button:
        """Create and return a styled pill-shaped button."""
        return tk.Button(parent, text=text, font=self.font_label,
                         relief="raised", bd=2, cursor="hand2",
                         activebackground=ACCENT, activeforeground=BG,
                         highlightbackground=BORDER_DARK, highlightthickness=2,
                         padx=26, pady=14, command=cmd)  # type: ignore[arg-type]

    def _set_viral(self, value: bool) -> None:
        """Set the viral preference and update the pill button visuals to match."""
        self.preferred_viral = value
        active = {
            "bg": ACCENT,
            "fg": BG,
            "activebackground": ACCENT_DIM,
            "activeforeground": BG,
            "highlightbackground": BORDER_DARK,
            "highlightthickness": 2,
            "relief": "raised",
            "bd": 2
        }
        inactive = {
            "bg": "#DDEFE3",
            "fg": TEXT,
            "activebackground": "#CFE6D7",
            "activeforeground": TEXT,
            "highlightbackground": BORDER_DARK,
            "highlightthickness": 2,
            "relief": "raised",
            "bd": 2
        }
        self._viral_yes.configure(**(active if value else inactive))  # type: ignore[arg-type]
        self._viral_no.configure(**(inactive if value else active))  # type: ignore[arg-type]

    # page 3 - energy level
    def _build_page_energy(self) -> None:
        """Build and register page 3 — the energy level page.

        Presents a horizontal slider from 1 to 10, with a large numeric readout
        that updates live as the slider moves. The chosen value is divided by 10
        to produce a normalized float in [0.1, 1.0] stored in preferred_energy,
        matching the normalization applied in main.py.
        """
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Playlistify", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")
        tk.Label(page, text="What's your energy level?",
                 font=self.font_label, bg=BG, fg=TEXT
                 ).place(relx=0.5, y=180, anchor="center")
        tk.Label(page, text="1 = calm & relaxed    ·    10 = high intensity",
                 font=self.font_small, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=206, anchor="center")

        self.energy_var = tk.IntVar(value=5)
        self.energy_label = tk.Label(page, text="5", font=self.font_big_num,
                                     bg=BG, fg=ACCENT)
        self.energy_label.place(relx=0.5, y=290, anchor="center")

        tk.Label(page, text="CALM", font=self.font_small, bg=BG,
                 fg=TEXT_DIM).place(relx=0.5, y=356, anchor="center", x=-220)
        tk.Label(page, text="INTENSE", font=self.font_small, bg=BG,
                 fg=TEXT_DIM).place(relx=0.5, y=356, anchor="center", x=220)

        tk.Scale(page, from_=1, to=10, orient="horizontal",
                 variable=self.energy_var, command=self._on_energy_change,
                 bg=BG, fg=TEXT, troughcolor=BORDER, activebackground=ACCENT,
                 highlightthickness=0, bd=0, sliderlength=28,
                 length=440, showvalue=False
                 ).place(relx=0.5, y=336, anchor="center")

    def _on_energy_change(self, val: str) -> None:
        """Update preferred_energy and the numeric readout when the slider moves.

        val is the string representation of the slider's integer position (1–10).
        It is normalized to [0.1, 1.0] by dividing by 10, matching main.py's
        energy_value / 10 conversion.
        """
        self.preferred_energy = int(val) / 10
        self.energy_label.configure(text=val)

    # page 4 - playlist size + generate button

    def _build_page_count(self) -> None:
        """Build and register page 4 — the playlist size and generation page.

        Contains a large numeric entry for the desired playlist length (default 10)
        and the 'Generate Playlist' button that triggers the full recommendation
        pipeline. A status label below the button shows loading feedback and any
        validation errors.
        """
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Playlistify", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=78, anchor="center")
        tk.Label(page, text="How many songs in your playlist?",
                 font=self.font_label, bg=BG, fg=TEXT
                 ).place(relx=0.5, y=228, anchor="center")

        self.count_var = tk.StringVar(value="10")
        cf = tk.Frame(page, bg=BORDER_DARK, padx=1, pady=1)
        cf.place(relx=0.5, y=332, anchor="center", width=210, height=74)
        tk.Entry(cf, textvariable=self.count_var, font=self.font_big_num,
                 bg=BG, fg=ACCENT, insertbackground=ACCENT,
                 justify="center", relief="flat", bd=8
                 ).pack(fill="both", expand=True)

        tk.Label(page, text="Enter a number greater than 0",
                 font=self.font_small, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=398, anchor="center")

        self.gen_btn = tk.Button(page, text="Generate Playlist  →",
                                 font=self.font_label, bg=ACCENT, fg=BG,
                                 relief="raised", bd=2, cursor="hand2",
                                 activebackground=ACCENT_DIM, activeforeground=BG,
                                 highlightbackground=BORDER_DARK,
                                 highlightthickness=2,
                                 padx=36, pady=16, command=self._generate)

        self.gen_btn.place(relx=0.5, y=520, anchor="center")

        self.gen_status = tk.Label(page, text="", font=self.font_small,
                                   bg=BG, fg=TEXT_DIM, wraplength=500)
        self.gen_status.place(relx=0.5, y=584, anchor="center")

    # pgae 5: results
    def _build_page_results(self) -> None:
        """Build and register page 5 — the scrollable playlist results page."""
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Your Playlist", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=42, anchor="center")

        self.results_subtitle = tk.Label(page, text="",
                                         font=self.font_label, bg=BG, fg=TEXT_DIM)
        self.results_subtitle.place(relx=0.5, y=82, anchor="center")

        tk.Frame(page, bg=BORDER, height=1).place(
            relx=0.5, y=112, anchor="center", width=620)

        self.viz_btn = tk.Button(page, text="🔍  Visualize Recommendation Graph",
                                 font=self.font_label, bg=SURFACE, fg=ACCENT,
                                 relief="raised", bd=2, cursor="hand2",
                                 activebackground=BORDER, activeforeground=ACCENT_DIM,
                                 highlightbackground=BORDER_DARK,
                                 highlightthickness=2,
                                 padx=20, pady=12,
                                 command=self._launch_visualization)
        self.viz_btn.place(relx=0.5, y=156, anchor="center")

        container = tk.Frame(page, bg=BG)
        container.place(x=50, y=210, width=620, height=480)

        sb = tk.Scrollbar(container, orient="vertical")
        sb.pack(side="right", fill="y")

        self.results_canvas = tk.Canvas(container, bg=BG,
                                        highlightthickness=0,
                                        yscrollcommand=sb.set)
        self.results_canvas.pack(side="left", fill="both", expand=True)
        sb.configure(command=self.results_canvas.yview)

        self.results_inner = tk.Frame(self.results_canvas, bg=BG)
        self.results_canvas.create_window((0, 0), window=self.results_inner,
                                          anchor="nw")
        self.results_inner.bind("<Configure>",
                                lambda _: self.results_canvas.configure(
                                    scrollregion=self.results_canvas.bbox("all")))

    def _populate_results(self, songs: list[tuple[float, str, str]]) -> None:
        """Populate the results page with the given list of recommended songs.

        Clears any previously rendered rows, then creates one row per song showing
        a zero-padded index, the track name, genre, and a percentage match badge
        derived from the cosine similarity weight. If songs is empty, a fallback
        message prompts the user to broaden their preferences.

        Preconditions:
            - Each tuple in songs is (weight, track_name, genre) with 0.0 <= weight <= 1.0.
        """
        for w in self.results_inner.winfo_children():
            w.destroy()

        if not songs:
            tk.Label(self.results_inner,
                     text="No songs found. Try adjusting your preferences —\n"
                          "lower the energy threshold or choose a broader genre.",
                     font=self.font_label, bg=BG, fg=TEXT_DIM,
                     wraplength=500, justify="center"
                     ).pack(pady=60)
            return

        for i, (weight, name, genre) in enumerate(songs):
            row = tk.Frame(self.results_inner, bg=BG)
            row.pack(fill="x", padx=8, pady=6)

            tk.Label(row,
                     text=f"{i + 1:02d}",
                     font=tkfont.Font(family="Courier New", size=13, weight="bold"),
                     bg=BG, fg=BORDER_DARK, width=4, anchor="e"
                     ).pack(side="left", padx=(0, 14))

            info = tk.Frame(row, bg=BG)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=name, font=self.font_result,
                     bg=BG, fg=TEXT, anchor="w").pack(fill="x")
            tk.Label(info, text=genre, font=self.font_small,
                     bg=BG, fg=TEXT_DIM, anchor="w").pack(fill="x")

            pct = int(weight * 100)
            badge = tk.Frame(row, bg=TAG_BG,
                             highlightbackground=TAG_BORDER, highlightthickness=1)
            badge.pack(side="right", padx=8)
            tk.Label(badge, text=f"{pct}% match",
                     font=self.font_small, bg=TAG_BG, fg=ACCENT_DIM,
                     padx=8, pady=5).pack()

            tk.Frame(self.results_inner, bg=BORDER, height=1).pack(
                fill="x", padx=8)

        self.results_subtitle.configure(
            text=f"{len(songs)} songs  ·  genres: {', '.join(self.preferred_genres)}")

    # Generation pipeline
    def _launch_visualization(self) -> None:
        """Launch the 3D interactive graph visualization in the user's browser.

        Maps the final recommended song names back to Song objects using the
        loaded song graph, then delegates to graph_visualization.run_visualization
        with the seed songs, full graph, and final recommendation set.

        This mirrors the _launch_viz function in console_version.py exactly.
        The visualization opens as a Plotly figure in the default web browser
        and supports zoom and 360-degree rotation.

        Does nothing if the graph has not been loaded yet (i.e. _generate has
        not been run successfully at least once).
        """
        if self._graph_song is None:
            return

        seed_objs = [s for _, s in self._seed_songs]
        song_map = {s.track_name: s for s in self._graph_song.get_all_songs()}
        final_objs = {song_map[name]
                      for _, name, _ in self._final_songs
                      if name in song_map}

        # Run visualization in a background thread so the Tkinter event loop
        # is not blocked — Plotly's fig.show() opens a browser window and waits,
        # which would freeze the GUI if called on the main thread.
        thread = threading.Thread(
            target=graph_visualization.run_visualization,
            args=(seed_objs, self._graph_song, final_objs),
            daemon=True   # thread dies automatically when the app closes
        )
        thread.start()

    def _generate(self) -> None:
        """Run the full playlist recommendation pipeline and navigate to the results page.

        Logic:
            1. Validate the playlist size input (must be a positive integer).
            2. Ensure at least one genre has been selected.
            3. Load the genre tree and song graph from CSV on first run (cached thereafter).
            4. Filter all songs to those whose genre exactly matches a selected genre,
               whose energy meets or exceeds preferred_energy, and (if preferred_viral
               is True) whose popularity is at least VIRAL_THRESHOLD.
            5. Sort the filtered candidates by popularity (descending) and take the top 5
               as seed songs. Store them in _seed_songs for use by _launch_visualization.
            6. Collect all graph neighbours of each seed song along with their edge weights
               (cosine similarity scores).
            7. Sort the neighbour set by similarity weight (descending) and take the top N.
               Store the result in _final_songs for use by _launch_visualization.
            8. Pass the final list to _populate_results and navigate to page 5.
        """
        # validate count
        try:
            n = int(self.count_var.get())
            if n <= 0:
                raise ValueError
            self.recommend_n_songs = n
        except ValueError:
            self.gen_status.configure(
                text="Please enter a valid number greater than 0.", fg="#D32F2F")
            return

        if not self.preferred_genres:
            self.gen_status.configure(
                text="Please select at least one genre first.", fg="#D32F2F")
            return

        # loading feedback
        self.gen_btn.configure(state="disabled", text="Loading…")
        self.gen_status.configure(
            text="Building song graph — this may take ~30 seconds on first run…",
            fg=TEXT_DIM)
        self.update()

        # load data (cached after first run)
        if self._tree_genre is None:
            self._tree_genre = load_genre_tree('data/spotify_data.csv')
        if self._graph_song is None:
            self._graph_song = sg.load_song_graph('data/spotify_data.csv')

        self.gen_status.configure(text="Filtering songs…")
        self.update()

        # filter candidates — exact genre match, same logic as main.py
        candidate_songs: set[tuple[int, sg.Song]] = set()
        for genre in self.preferred_genres:
            genre_node = self._tree_genre.find(genre)
            if genre_node is None:
                continue
            for song in self._graph_song.get_all_songs():
                if song.genre != genre:
                    continue
                meets_energy = song.features.energy >= self.preferred_energy
                meets_popularity = (song.popularity >= VIRAL_THRESHOLD
                                    if self.preferred_viral else True)
                if meets_energy and meets_popularity:
                    candidate_songs.add((song.popularity, song))

        # seed songs (top 5 by popularity)
        seed_songs = sorted(list(candidate_songs),
                            key=lambda x: x[0], reverse=True)[:5]
        self._seed_songs = seed_songs

        # collect neighbours from graph
        recommendation_set: set[tuple[float, str, str]] = set()
        for _, song in seed_songs:
            for neighbour in self._graph_song.get_neighbours(song):
                weight = self._graph_song.get_weight(song, neighbour)
                recommendation_set.add(
                    (weight, neighbour.track_name, neighbour.genre))

        # sort by similarity, take top N
        final = sorted(list(recommendation_set),
                       reverse=True)[:self.recommend_n_songs]
        self._final_songs = final

        self._populate_results(final)
        self.gen_btn.configure(state="normal", text="Generate Playlist  →")
        self.gen_status.configure(text="")
        self._show_page(5)


def run_gui() -> None:
    """Initialize and run the Playlistify Graphical User Interface."""
    app = PlaylistifyApp()
    app.mainloop()


if __name__ == "__main__":
    import python_ta

    python_ta.check_all(config={
        'max-line-length': 120,
        'extra-imports': ['math', 'threading', 'tkinter', 'song_graph', 'genre_tree', 'graph_visualization'],
        'allowed-io': ['load_song_graph'],
        # 'disable': ['C9103', 'E9972', 'R0902']
    })

    run_gui()

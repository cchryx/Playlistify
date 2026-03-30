"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

GUI module — white-themed multi-page survey with genre tree explorer,
user preference collection, and playlist results display.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

import math
import tkinter as tk
from tkinter import font as tkfont

from genre_tree import GENRE_HIERARCHY, load_genre_tree
import song_graph as sg

# ── Palette (white theme) ──────────────────────────────────────────────────────
BG          = "#FFFFFF"
SURFACE     = "#F5F5F5"
BORDER      = "#E0E0E0"
BORDER_DARK = "#BDBDBD"
ACCENT      = "#1DB954"
ACCENT_DIM  = "#158a3e"
TEXT        = "#212121"
TEXT_DIM    = "#757575"
TAG_BG      = "#E8F5E9"
TAG_BORDER  = "#1DB954"
DROP_BG     = "#FFFFFF"

BUBBLE_COLORS = {
    0: ("#1DB954", "#FFFFFF"),
    1: ("#E8F5E9", "#1B5E20"),
    2: ("#F1F8E9", "#33691E"),
}

ALL_GENRES      = sorted(GENRE_HIERARCHY.keys())
MAX_DROP        = 6
VIRAL_THRESHOLD = 10


# ── Build children map ────────────────────────────────────────────────────────
def _build_children() -> dict[str, list[str]]:
    children: dict[str, list[str]] = {"root": []}
    for genre in GENRE_HIERARCHY:
        children[genre] = []
    for genre, parent in GENRE_HIERARCHY.items():
        children[parent].append(genre)
    return children


CHILDREN = _build_children()


# ══════════════════════════════════════════════════════════════════════════════
class PlaylistifyApp(tk.Tk):
    """Root window — hosts all pages in a simple stack."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Playlistify")
        self.geometry("720x820")
        self.resizable(False, False)
        self.configure(bg=BG)

        self.preferred_genres:  list[str] = []
        self.preferred_viral:   bool      = False
        self.preferred_energy:  float     = 0.5
        self.recommend_n_songs: int       = 10

        self._tree_genre = None
        self._graph_song = None

        self._build_fonts()

        self.pages:        list[tk.Frame] = []
        self.current_page: int            = 0

        self._build_page_genre()    # 0
        self._build_page_tree()     # 1
        self._build_page_viral()    # 2
        self._build_page_energy()   # 3
        self._build_page_count()    # 4
        self._build_page_results()  # 5
        self._build_nav()

        self._show_page(0)

    # ── Fonts ──────────────────────────────────────────────────────────────────
    def _build_fonts(self) -> None:
        self.font_title   = tkfont.Font(family="Georgia",     size=20, weight="bold")
        self.font_label   = tkfont.Font(family="Georgia",     size=12)
        self.font_small   = tkfont.Font(family="Georgia",     size=9)
        self.font_input   = tkfont.Font(family="Courier New", size=12)
        self.font_nav     = tkfont.Font(family="Georgia",     size=16, weight="bold")
        self.font_tag     = tkfont.Font(family="Courier New", size=10)
        self.font_bubble  = tkfont.Font(family="Georgia",     size=9,  weight="bold")
        self.font_result  = tkfont.Font(family="Georgia",     size=11)
        self.font_big_num = tkfont.Font(family="Georgia",     size=36, weight="bold")

    # ── Navigation ─────────────────────────────────────────────────────────────
    def _build_nav(self) -> None:
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
        self.dots: list[tk.Label] = []
        for _ in range(4):
            d = tk.Label(self.dot_frame, text="●", bg=SURFACE,
                         font=tkfont.Font(size=8))
            d.pack(side="left", padx=4)
            self.dots.append(d)
        self._update_dots()

    def _dot_index(self) -> int:
        return {0: 0, 1: 0, 2: 1, 3: 2, 4: 3, 5: 3}.get(self.current_page, 0)

    def _update_dots(self) -> None:
        di = self._dot_index()
        for i, d in enumerate(self.dots):
            d.configure(fg=ACCENT if i == di else BORDER_DARK)

    def _show_page(self, index: int) -> None:
        for p in self.pages:
            p.place_forget()
        self.pages[index].place(x=0, y=0, width=720, height=756)
        self.current_page = index
        self._update_dots()

    def _prev_page(self) -> None:
        # Page 1 (tree explorer) is only reachable via the Browse button, not arrow nav
        if self.current_page == 2:
            self._show_page(0)
        elif self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _next_page(self) -> None:
        # Skip page 1 (tree explorer) when using arrow nav
        if self.current_page == 0:
            self._show_page(2)
        elif self.current_page < len(self.pages) - 1:
            self._show_page(self.current_page + 1)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 0 — Genre selection
    # ══════════════════════════════════════════════════════════════════════════
    def _build_page_genre(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Playlistify", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")
        tk.Label(page, text="What genres are you in the mood for?",
                 font=self.font_label, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=82, anchor="center")

        # search bar
        sf = tk.Frame(page, bg=BORDER_DARK, padx=1, pady=1)
        sf.place(relx=0.5, y=130, anchor="center", width=500, height=46)
        inner = tk.Frame(sf, bg=BG)
        inner.pack(fill="both", expand=True)

        self.genre_var = tk.StringVar()
        self.genre_var.trace_add("write", self._on_genre_type)

        self.search_entry = tk.Entry(inner, textvariable=self.genre_var,
                                     font=self.font_input, bg=BG, fg=TEXT_DIM,
                                     insertbackground=ACCENT, relief="flat", bd=8)
        self.search_entry.pack(fill="both", expand=True)
        self.search_entry.insert(0, "Search genres…")
        self.search_entry.bind("<Return>",  self._on_genre_enter)
        self.search_entry.bind("<Down>",    self._drop_focus_first)
        self.search_entry.bind("<Escape>",  lambda e: self._hide_dropdown())
        self.search_entry.bind("<FocusIn>",  self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)

        # dropdown
        self.drop_frame = tk.Frame(page, bg=BORDER_DARK, padx=1, pady=1)
        self.drop_lb = tk.Listbox(self.drop_frame, font=self.font_input,
                                   bg=DROP_BG, fg=TEXT,
                                   selectbackground=ACCENT, selectforeground=BG,
                                   relief="flat", bd=0, activestyle="none",
                                   highlightthickness=0, exportselection=False)
        self.drop_lb.pack(fill="both", expand=True, padx=1, pady=1)
        self.drop_lb.bind("<Return>",           self._on_drop_select)
        self.drop_lb.bind("<Double-Button-1>",  self._on_drop_select)
        self.drop_lb.bind("<Escape>",           lambda e: self._hide_dropdown())
        self.drop_lb.bind("<Up>",               self._drop_up)

        # browse button
        tk.Button(page, text="🎵  Browse genre tree  →",
                  font=self.font_small, bg=SURFACE, fg=ACCENT,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=BORDER, activeforeground=ACCENT_DIM,
                  padx=12, pady=6,
                  command=lambda: self._show_page(1)
                  ).place(relx=0.5, y=192, anchor="center")

        # divider
        tk.Frame(page, bg=BORDER, height=1).place(
            relx=0.5, y=220, anchor="center", width=500)

        tk.Label(page, text="Selected genres", font=self.font_small,
                 bg=BG, fg=TEXT_DIM).place(x=110, y=232)

        self.tag_frame = tk.Frame(page, bg=BG)
        self.tag_frame.place(x=110, y=255, width=500, height=240)

        tk.Label(page, text="Press Enter to add  ·  Click × to remove",
                 font=self.font_small, bg=BG, fg=BORDER_DARK
                 ).place(relx=0.5, y=510, anchor="center")

    def _clear_placeholder(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        if self.search_entry.get() == "Search genres…":
            self.search_entry.delete(0, "end")
            self.search_entry.configure(fg=TEXT)

    def _restore_placeholder(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search genres…")
            self.search_entry.configure(fg=TEXT_DIM)

    def _on_genre_type(self, *_: object) -> None:
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
        h = min(len(matches), MAX_DROP) * 28 + 2
        self.drop_frame.place(relx=0.5, y=177, anchor="n", width=500, height=h)
        self.drop_frame.lift()

    def _hide_dropdown(self) -> None:
        self.drop_frame.place_forget()

    def _on_genre_enter(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        typed = self.genre_var.get().strip().lower()
        sel   = self.drop_lb.curselection()
        genre = self.drop_lb.get(sel[0]) if sel else typed
        self._try_add_genre(genre)

    def _on_drop_select(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self.drop_lb.curselection()
        if sel:
            self._try_add_genre(self.drop_lb.get(sel[0]))

    def _drop_focus_first(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        if self.drop_lb.size() > 0:
            self.drop_lb.focus_set()
            self.drop_lb.selection_set(0)

    def _drop_up(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self.drop_lb.curselection()
        if sel and sel[0] == 0:
            self.search_entry.focus_set()

    def _try_add_genre(self, genre: str) -> None:
        if genre in GENRE_HIERARCHY and genre not in self.preferred_genres:
            self.preferred_genres.append(genre)
            self._render_tags()
        self.genre_var.set("")
        self._hide_dropdown()
        self.search_entry.configure(fg=TEXT)
        self.search_entry.focus_set()

    def _render_tags(self) -> None:
        for w in self.tag_frame.winfo_children():
            w.destroy()
        x, y = 0, 0
        for genre in self.preferred_genres:
            chip = tk.Frame(self.tag_frame, bg=TAG_BG,
                            highlightbackground=TAG_BORDER, highlightthickness=1)
            chip.place(x=x, y=y)
            tk.Label(chip, text=genre, font=self.font_tag,
                     bg=TAG_BG, fg=ACCENT_DIM, padx=8, pady=5).pack(side="left")
            tk.Button(chip, text="×", font=self.font_tag,
                      bg=TAG_BG, fg=TEXT_DIM, relief="flat", bd=0,
                      activebackground=TAG_BG, activeforeground="#D32F2F",
                      cursor="hand2", padx=4,
                      command=lambda g=genre: self._remove_genre(g)
                      ).pack(side="left")
            chip.update_idletasks()
            cw = chip.winfo_reqwidth()
            if x + cw > 490 and x > 0:
                x = 0
                y += 36
                chip.place(x=x, y=y)
            x += cw + 8

    def _remove_genre(self, genre: str) -> None:
        self.preferred_genres.remove(genre)
        self._render_tags()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — Genre tree explorer
    # ══════════════════════════════════════════════════════════════════════════
    def _build_page_tree(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Explore Genres", font=self.font_title,
                 bg=BG, fg=TEXT).place(relx=0.5, y=40, anchor="center")

        # "← Back to Search" always returns to the genre search page (page 0)
        tk.Button(page, text="← Back to Search",
                  font=self.font_small, bg=SURFACE, fg=ACCENT,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=BORDER,
                  command=lambda: self._show_page(0)
                  ).place(x=30, y=60)

        # Separate "↑ Up" button to navigate up within the tree hierarchy
        self.tree_back_btn = tk.Button(page, text="↑ Up",
                                        font=self.font_small, bg=SURFACE, fg=TEXT_DIM,
                                        relief="flat", bd=0, cursor="hand2",
                                        activebackground=BORDER,
                                        command=self._tree_drill_up)
        self.tree_back_btn.place(x=160, y=60)

        self.tree_breadcrumb = tk.Label(page, text="root",
                                         font=self.font_small, bg=BG, fg=TEXT_DIM)
        self.tree_breadcrumb.place(relx=0.5, y=68, anchor="center")

        tk.Label(page,
                 text="Click a bubble to explore sub-genres  ·  Click  +  to add to your selection",
                 font=self.font_small, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=90, anchor="center")

        self.tree_canvas = tk.Canvas(page, bg=BG, highlightthickness=0,
                                      width=720, height=616)
        self.tree_canvas.place(x=0, y=106)

        self._tree_path:    list[str] = []
        self._tree_current: str       = "root"

        self._tree_render()

    def _tree_render(self) -> None:
        self.tree_canvas.delete("all")
        children = CHILDREN.get(self._tree_current, [])

        if not children:
            self.tree_canvas.create_text(
                360, 300, text="No sub-genres available.",
                font=self.font_label, fill=TEXT_DIM)
        else:
            depth                = len(self._tree_path)
            fill_col, text_col  = BUBBLE_COLORS.get(depth, ("#E0E0E0", "#212121"))
            n                   = len(children)
            W, H                = 720, 616
            r                   = max(36, min(68, int(230 / max(n, 1) ** 0.5)))
            cols                = max(1, math.ceil(math.sqrt(n * 1.6)))
            rows                = math.ceil(n / cols)
            pad_x               = W / (cols + 1)
            pad_y               = H / (rows + 1)

            for idx, genre in enumerate(children):
                col = idx % cols
                row = idx // cols
                cx  = pad_x * (col + 1)
                cy  = pad_y * (row + 1)

                has_ch  = bool(CHILDREN.get(genre))
                outline = ACCENT if has_ch else BORDER_DARK
                lw      = 2    if has_ch else 1

                # shadow
                self.tree_canvas.create_oval(
                    cx - r + 3, cy - r + 3, cx + r + 3, cy + r + 3,
                    fill=BORDER, outline="")

                # bubble
                oid = self.tree_canvas.create_oval(
                    cx - r, cy - r, cx + r, cy + r,
                    fill=fill_col, outline=outline, width=lw)

                # label
                lbl = genre if len(genre) <= 12 else genre[:11] + "…"
                tid = self.tree_canvas.create_text(
                    cx, cy, text=lbl, font=self.font_bubble, fill=text_col)

                # + badge
                bx, by  = cx + r - 10, cy - r + 10
                bid     = self.tree_canvas.create_oval(
                    bx - 9, by - 9, bx + 9, by + 9,
                    fill=ACCENT, outline="")
                pid     = self.tree_canvas.create_text(
                    bx, by, text="+",
                    font=tkfont.Font(size=10, weight="bold"), fill="white")

                # drill-down on bubble/label
                for item in (oid, tid):
                    self.tree_canvas.tag_bind(
                        item, "<Button-1>",
                        lambda e, g=genre: self._tree_drill_down(g))
                    self.tree_canvas.tag_bind(
                        item, "<Enter>",
                        lambda e, o=oid: self.tree_canvas.itemconfigure(
                            o, outline=ACCENT, width=2))
                    self.tree_canvas.tag_bind(
                        item, "<Leave>",
                        lambda e, o=oid, ol=outline, lw2=lw:
                            self.tree_canvas.itemconfigure(o, outline=ol, width=lw2))

                # add on badge/plus
                for item in (bid, pid):
                    self.tree_canvas.tag_bind(
                        item, "<Button-1>",
                        lambda e, g=genre: self._tree_add_genre(g))

        # update breadcrumb & back button
        crumb = " › ".join(["root"] + self._tree_path) if self._tree_path else "root"
        self.tree_breadcrumb.configure(text=crumb)
        self.tree_back_btn.configure(
            state="normal" if self._tree_path else "disabled",
            fg=ACCENT if self._tree_path else BORDER_DARK)

    def _tree_drill_down(self, genre: str) -> None:
        if not CHILDREN.get(genre):
            self._tree_add_genre(genre)
            return
        self._tree_path.append(genre)
        self._tree_current = genre
        self._tree_render()

    def _tree_drill_up(self) -> None:
        if self._tree_path:
            self._tree_path.pop()
            self._tree_current = self._tree_path[-1] if self._tree_path else "root"
            self._tree_render()

    def _tree_add_genre(self, genre: str) -> None:
        if genre in GENRE_HIERARCHY and genre not in self.preferred_genres:
            self.preferred_genres.append(genre)
            self._render_tags()
        msg = self.tree_canvas.create_text(
            360, 590, text=f"✓  '{genre}' added to your selection",
            font=self.font_small, fill=ACCENT)
        self.tree_canvas.after(1800, lambda: self.tree_canvas.delete(msg))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — Viral preference
    # ══════════════════════════════════════════════════════════════════════════
    def _build_page_viral(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Playlistify", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")
        tk.Label(page, text="Do you want popular songs?",
                 font=self.font_label, bg=BG, fg=TEXT
                 ).place(relx=0.5, y=200, anchor="center")
        tk.Label(page,
                 text=f"Popular songs have a Spotify popularity score of {VIRAL_THRESHOLD}+  (out of 100)",
                 font=self.font_small, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=226, anchor="center")

        btn_frame = tk.Frame(page, bg=BG)
        btn_frame.place(relx=0.5, y=310, anchor="center")

        self._viral_yes = self._pill_btn(btn_frame, "Yes — give me hits",
                                          lambda: self._set_viral(True))
        self._viral_yes.pack(side="left", padx=16)

        self._viral_no = self._pill_btn(btn_frame, "No — surprise me",
                                         lambda: self._set_viral(False))
        self._viral_no.pack(side="left", padx=16)

        self._set_viral(False)

    def _pill_btn(self, parent: tk.Frame, text: str, cmd: object) -> tk.Button:
        return tk.Button(parent, text=text, font=self.font_label,
                         relief="flat", bd=0, cursor="hand2",
                         activebackground=ACCENT, activeforeground=BG,
                         padx=20, pady=10, command=cmd)  # type: ignore[arg-type]

    def _set_viral(self, value: bool) -> None:
        self.preferred_viral = value
        active   = {"bg": ACCENT,   "fg": BG,
                    "highlightbackground": ACCENT,      "highlightthickness": 0}
        inactive = {"bg": SURFACE,  "fg": TEXT_DIM,
                    "highlightbackground": BORDER_DARK, "highlightthickness": 1}
        self._viral_yes.configure(**(active   if value else inactive))  # type: ignore[arg-type]
        self._viral_no.configure(**(inactive  if value else active))    # type: ignore[arg-type]

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — Energy level
    # ══════════════════════════════════════════════════════════════════════════
    def _build_page_energy(self) -> None:
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

        self.energy_var   = tk.IntVar(value=5)
        self.energy_label = tk.Label(page, text="5", font=self.font_big_num,
                                      bg=BG, fg=ACCENT)
        self.energy_label.place(relx=0.5, y=290, anchor="center")

        tk.Label(page, text="CALM",    font=self.font_small, bg=BG,
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
        self.preferred_energy = int(val) / 10
        self.energy_label.configure(text=val)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 — Playlist size + Generate button
    # ══════════════════════════════════════════════════════════════════════════
    def _build_page_count(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Playlistify", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")
        tk.Label(page, text="How many songs in your playlist?",
                 font=self.font_label, bg=BG, fg=TEXT
                 ).place(relx=0.5, y=190, anchor="center")

        self.count_var = tk.StringVar(value="10")
        cf = tk.Frame(page, bg=BORDER_DARK, padx=1, pady=1)
        cf.place(relx=0.5, y=270, anchor="center", width=180, height=60)
        tk.Entry(cf, textvariable=self.count_var, font=self.font_big_num,
                 bg=BG, fg=ACCENT, insertbackground=ACCENT,
                 justify="center", relief="flat", bd=8
                 ).pack(fill="both", expand=True)

        tk.Label(page, text="Enter a number greater than 0",
                 font=self.font_small, bg=BG, fg=TEXT_DIM
                 ).place(relx=0.5, y=322, anchor="center")

        self.gen_btn = tk.Button(page, text="Generate Playlist  →",
                                  font=self.font_label, bg=ACCENT, fg=BG,
                                  relief="flat", bd=0, cursor="hand2",
                                  activebackground=ACCENT_DIM, activeforeground=BG,
                                  padx=28, pady=12, command=self._generate)
        self.gen_btn.place(relx=0.5, y=420, anchor="center")

        self.gen_status = tk.Label(page, text="", font=self.font_small,
                                    bg=BG, fg=TEXT_DIM, wraplength=500)
        self.gen_status.place(relx=0.5, y=472, anchor="center")

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5 — Results
    # ══════════════════════════════════════════════════════════════════════════
    def _build_page_results(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="Your Playlist", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=40, anchor="center")

        self.results_subtitle = tk.Label(page, text="",
                                          font=self.font_small, bg=BG, fg=TEXT_DIM)
        self.results_subtitle.place(relx=0.5, y=70, anchor="center")

        tk.Frame(page, bg=BORDER, height=1).place(
            relx=0.5, y=88, anchor="center", width=620)

        # scrollable list
        container = tk.Frame(page, bg=BG)
        container.place(x=50, y=100, width=620, height=590)

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
                                 lambda e: self.results_canvas.configure(
                                     scrollregion=self.results_canvas.bbox("all")))

    def _populate_results(self, songs: list[tuple[float, str, str]]) -> None:
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
            row.pack(fill="x", padx=8, pady=4)

            tk.Label(row,
                     text=f"{i + 1:02d}",
                     font=tkfont.Font(family="Courier New", size=11, weight="bold"),
                     bg=BG, fg=BORDER_DARK, width=4, anchor="e"
                     ).pack(side="left", padx=(0, 14))

            info = tk.Frame(row, bg=BG)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=name, font=self.font_result,
                     bg=BG, fg=TEXT, anchor="w").pack(fill="x")
            tk.Label(info, text=genre, font=self.font_small,
                     bg=BG, fg=TEXT_DIM, anchor="w").pack(fill="x")

            pct   = int(weight * 100)
            badge = tk.Frame(row, bg=TAG_BG,
                              highlightbackground=TAG_BORDER, highlightthickness=1)
            badge.pack(side="right", padx=8)
            tk.Label(badge, text=f"{pct}% match",
                     font=self.font_small, bg=TAG_BG, fg=ACCENT_DIM,
                     padx=6, pady=3).pack()

            tk.Frame(self.results_inner, bg=BORDER, height=1).pack(
                fill="x", padx=8)

        self.results_subtitle.configure(
            text=f"{len(songs)} songs  ·  genres: {', '.join(self.preferred_genres)}")

    # ══════════════════════════════════════════════════════════════════════════
    # Generation pipeline
    # ══════════════════════════════════════════════════════════════════════════
    def _generate(self) -> None:
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
        candidate_songs: set[tuple[int, object]] = set()
        for genre in self.preferred_genres:
            genre_node = self._tree_genre.find(genre)
            if genre_node is None:
                continue
            for song in self._graph_song.get_all_songs():
                if song.genre != genre:
                    continue
                meets_energy     = song.features.energy >= self.preferred_energy
                meets_popularity = (song.popularity >= VIRAL_THRESHOLD
                                    if self.preferred_viral else True)
                if meets_energy and meets_popularity:
                    candidate_songs.add((song.popularity, song))

        # seed songs (top 5 by popularity)
        seed_songs = sorted(list(candidate_songs),
                            key=lambda x: x[0], reverse=True)[:5]

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

        self._populate_results(final)
        self.gen_btn.configure(state="normal", text="Generate Playlist  →")
        self.gen_status.configure(text="")
        self._show_page(5)


if __name__ == "__main__":
    app = PlaylistifyApp()
    app.mainloop()

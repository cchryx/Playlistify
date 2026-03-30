"""
CSC111 Project: Playlistify (Mood-Aware Music Recommendation Engine)

This module contains the Tkinter GUI for collecting user preferences.

Copyright (c) 2026 Xing Xu Chen, Tianqi Pan, Norah Liu, Denise Ma
"""

import tkinter as tk
from tkinter import font as tkfont
from genre_tree import GENRE_HIERARCHY

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#0F0F0F"
SURFACE     = "#1A1A1A"
BORDER      = "#2E2E2E"
ACCENT      = "#1DB954"          # Spotify green
ACCENT_DIM  = "#158a3e"
TEXT        = "#FFFFFF"
TEXT_DIM    = "#A0A0A0"
TAG_BG      = "#1E3A28"
TAG_BORDER  = "#1DB954"
DROP_BG     = "#1A1A1A"
DROP_HOVER  = "#252525"

ALL_GENRES  = sorted(GENRE_HIERARCHY.keys())
MAX_DROP    = 6                   # max dropdown rows to show


class PlaylistifyApp(tk.Tk):
    """Main application window for Playlistify."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Playlistify")
        self.geometry("680x780")
        self.resizable(False, False)
        self.configure(bg=BG)

        # ── User preference state ──────────────────────────────────────────
        self.preferred_genres: list[str] = []
        self.preferred_viral: bool = False
        self.preferred_energy: float = 0.5
        self.recommend_n_songs: int = 10

        # ── Pages ──────────────────────────────────────────────────────────
        self.pages: list[tk.Frame] = []
        self.current_page: int = 0

        self._build_fonts()
        self._build_page_genre()
        self._build_page_viral()
        self._build_page_energy()
        self._build_page_count()
        self._build_nav()

        self._show_page(0)

    # ── Fonts ──────────────────────────────────────────────────────────────
    def _build_fonts(self) -> None:
        self.font_title  = tkfont.Font(family="Courier New", size=18, weight="bold")
        self.font_label  = tkfont.Font(family="Courier New", size=11)
        self.font_small  = tkfont.Font(family="Courier New", size=9)
        self.font_input  = tkfont.Font(family="Courier New", size=12)
        self.font_nav    = tkfont.Font(family="Courier New", size=16, weight="bold")
        self.font_tag    = tkfont.Font(family="Courier New", size=10)

    # ── Navigation ─────────────────────────────────────────────────────────
    def _build_nav(self) -> None:
        nav = tk.Frame(self, bg=BG)
        nav.place(relx=0, rely=1.0, anchor="sw", x=0, y=0, relwidth=1.0, height=70)

        tk.Button(nav, text="←", font=self.font_nav, bg=SURFACE, fg=TEXT,
                  relief="flat", bd=0, activebackground=BORDER, activeforeground=ACCENT,
                  cursor="hand2", command=self._prev_page, width=4, height=1
                  ).place(x=20, y=10)

        tk.Button(nav, text="→", font=self.font_nav, bg=SURFACE, fg=TEXT,
                  relief="flat", bd=0, activebackground=BORDER, activeforeground=ACCENT,
                  cursor="hand2", command=self._next_page, width=4, height=1
                  ).place(relx=1.0, x=-80, y=10)

        # Page indicator dots
        self.dot_frame = tk.Frame(nav, bg=BG)
        self.dot_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.dots: list[tk.Label] = []
        for i in range(4):
            d = tk.Label(self.dot_frame, text="●", bg=BG,
                         font=tkfont.Font(size=8))
            d.pack(side="left", padx=4)
            self.dots.append(d)

    def _update_dots(self) -> None:
        for i, d in enumerate(self.dots):
            d.configure(fg=ACCENT if i == self.current_page else BORDER)

    def _show_page(self, index: int) -> None:
        for p in self.pages:
            p.place_forget()
        self.pages[index].place(x=0, y=0, width=680, height=710)
        self.current_page = index
        self._update_dots()

    def _prev_page(self) -> None:
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _next_page(self) -> None:
        if self.current_page < len(self.pages) - 1:
            self._show_page(self.current_page + 1)
        else:
            self._finish()

    # ── Page 1 — Genre selection ───────────────────────────────────────────
    def _build_page_genre(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        # Title
        tk.Label(page, text="PLAYLISTIFY", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")

        tk.Label(page, text="Select your genres", font=self.font_label,
                 bg=BG, fg=TEXT_DIM).place(relx=0.5, y=84, anchor="center")

        # ── Search bar frame ───────────────────────────────────────────────
        search_frame = tk.Frame(page, bg=BORDER, padx=1, pady=1)
        search_frame.place(relx=0.5, y=130, anchor="center", width=480, height=44)

        inner = tk.Frame(search_frame, bg=SURFACE)
        inner.pack(fill="both", expand=True)

        self.genre_var = tk.StringVar()
        self.genre_var.trace_add("write", self._on_genre_type)

        self.search_entry = tk.Entry(inner, textvariable=self.genre_var,
                                     font=self.font_input, bg=SURFACE, fg=TEXT,
                                     insertbackground=ACCENT, relief="flat",
                                     bd=8)
        self.search_entry.pack(fill="both", expand=True)
        self.search_entry.bind("<Return>",      self._on_genre_enter)
        self.search_entry.bind("<Down>",         self._drop_focus_first)
        self.search_entry.bind("<Escape>",       lambda e: self._hide_dropdown())

        # ── Dropdown ───────────────────────────────────────────────────────
        self.drop_frame = tk.Frame(page, bg=BORDER, padx=1, pady=1)
        self.drop_listbox = tk.Listbox(self.drop_frame, font=self.font_input,
                                        bg=DROP_BG, fg=TEXT, selectbackground=ACCENT,
                                        selectforeground=BG, relief="flat", bd=0,
                                        activestyle="none", highlightthickness=0,
                                        exportselection=False)
        self.drop_listbox.pack(fill="both", expand=True, padx=1, pady=1)
        self.drop_listbox.bind("<Return>",       self._on_drop_select)
        self.drop_listbox.bind("<Double-Button-1>", self._on_drop_select)
        self.drop_listbox.bind("<Escape>",       lambda e: self._hide_dropdown())
        self.drop_listbox.bind("<Up>",           self._drop_up)

        # ── Tag chip area ──────────────────────────────────────────────────
        tk.Label(page, text="Added genres:", font=self.font_small,
                 bg=BG, fg=TEXT_DIM).place(x=100, y=200)

        self.tag_frame = tk.Frame(page, bg=BG)
        self.tag_frame.place(x=100, y=222, width=480, height=200)

        # hint
        self.genre_hint = tk.Label(page,
            text="Type a genre and press Enter  ·  Click × to remove",
            font=self.font_small, bg=BG, fg=BORDER)
        self.genre_hint.place(relx=0.5, y=440, anchor="center")

    def _on_genre_type(self, *_: object) -> None:
        """Filter dropdown suggestions as the user types."""
        query = self.genre_var.get().strip().lower()
        if not query:
            self._hide_dropdown()
            return

        matches = [g for g in ALL_GENRES if query in g][:MAX_DROP]
        if not matches:
            self._hide_dropdown()
            return

        self.drop_listbox.delete(0, "end")
        for m in matches:
            self.drop_listbox.insert("end", m)

        row_h = 28
        h = min(len(matches), MAX_DROP) * row_h + 2
        self.drop_frame.place(relx=0.5, y=175, anchor="n", width=480, height=h)
        self.drop_frame.lift()

    def _hide_dropdown(self) -> None:
        self.drop_frame.place_forget()

    def _on_genre_enter(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        """Add genre from entry or top dropdown match."""
        typed = self.genre_var.get().strip().lower()
        # prefer highlighted dropdown item
        sel = self.drop_listbox.curselection()
        genre = self.drop_listbox.get(sel[0]) if sel else typed
        self._try_add_genre(genre)

    def _on_drop_select(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        sel = self.drop_listbox.curselection()
        if sel:
            self._try_add_genre(self.drop_listbox.get(sel[0]))

    def _drop_focus_first(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        if self.drop_listbox.size() > 0:
            self.drop_listbox.focus_set()
            self.drop_listbox.selection_set(0)

    def _drop_up(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        """Return focus to entry when pressing Up on first item."""
        sel = self.drop_listbox.curselection()
        if sel and sel[0] == 0:
            self.search_entry.focus_set()

    def _try_add_genre(self, genre: str) -> None:
        """Add genre tag if valid and not already added."""
        if genre in GENRE_HIERARCHY and genre not in self.preferred_genres:
            self.preferred_genres.append(genre)
            self._render_tags()
        self.genre_var.set("")
        self._hide_dropdown()
        self.search_entry.focus_set()

    def _render_tags(self) -> None:
        """Re-render all genre tag chips."""
        for w in self.tag_frame.winfo_children():
            w.destroy()

        x, y = 0, 0
        for genre in self.preferred_genres:
            chip = tk.Frame(self.tag_frame, bg=TAG_BG,
                            highlightbackground=TAG_BORDER, highlightthickness=1)
            chip.place(x=x, y=y)

            tk.Label(chip, text=genre, font=self.font_tag,
                     bg=TAG_BG, fg=ACCENT, padx=8, pady=4).pack(side="left")

            btn = tk.Button(chip, text="×", font=self.font_tag,
                            bg=TAG_BG, fg=TEXT_DIM, relief="flat", bd=0,
                            activebackground=TAG_BG, activeforeground="#FF5555",
                            cursor="hand2", padx=4,
                            command=lambda g=genre: self._remove_genre(g))
            btn.pack(side="left")

            chip.update_idletasks()
            w = chip.winfo_reqwidth()

            # Wrap to next row if needed
            if x + w > 480 and x > 0:
                x = 0
                y += 36
                chip.place(x=x, y=y)

            x += w + 8

    def _remove_genre(self, genre: str) -> None:
        self.preferred_genres.remove(genre)
        self._render_tags()

    # ── Page 2 — Viral preference ──────────────────────────────────────────
    def _build_page_viral(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="PLAYLISTIFY", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")

        tk.Label(page, text="Do you want viral songs?", font=self.font_label,
                 bg=BG, fg=TEXT).place(relx=0.5, y=180, anchor="center")

        tk.Label(page, text="Viral songs have a popularity score of 75 or above.",
                 font=self.font_small, bg=BG, fg=TEXT_DIM).place(relx=0.5, y=208, anchor="center")

        self.viral_var = tk.BooleanVar(value=False)

        btn_frame = tk.Frame(page, bg=BG)
        btn_frame.place(relx=0.5, y=290, anchor="center")

        self._viral_yes = self._toggle_btn(btn_frame, "YES", lambda: self._set_viral(True))
        self._viral_yes.pack(side="left", padx=16)

        self._viral_no = self._toggle_btn(btn_frame, "NO", lambda: self._set_viral(False))
        self._viral_no.pack(side="left", padx=16)

        self._set_viral(False)  # default

    def _toggle_btn(self, parent: tk.Frame, text: str, cmd: object) -> tk.Button:
        return tk.Button(parent, text=text, font=self.font_input,
                         width=8, relief="flat", bd=0, cursor="hand2",
                         activebackground=ACCENT, activeforeground=BG,
                         command=cmd)  # type: ignore[arg-type]

    def _set_viral(self, value: bool) -> None:
        self.preferred_viral = value
        active   = {"bg": ACCENT,   "fg": BG}
        inactive = {"bg": SURFACE,  "fg": TEXT_DIM,
                    "highlightbackground": BORDER, "highlightthickness": 1}
        if value:
            self._viral_yes.configure(**active)      # type: ignore[arg-type]
            self._viral_no.configure(**inactive)     # type: ignore[arg-type]
        else:
            self._viral_no.configure(**active)       # type: ignore[arg-type]
            self._viral_yes.configure(**inactive)    # type: ignore[arg-type]

    # ── Page 3 — Energy level ──────────────────────────────────────────────
    def _build_page_energy(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="PLAYLISTIFY", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")

        tk.Label(page, text="Energy level", font=self.font_label,
                 bg=BG, fg=TEXT).place(relx=0.5, y=180, anchor="center")

        tk.Label(page, text="1 = calm & relaxed    10 = high energy & intense",
                 font=self.font_small, bg=BG, fg=TEXT_DIM).place(relx=0.5, y=208, anchor="center")

        self.energy_var = tk.IntVar(value=5)
        self.energy_label = tk.Label(page, text="5", font=tkfont.Font(family="Courier New", size=32, weight="bold"),
                                     bg=BG, fg=ACCENT)
        self.energy_label.place(relx=0.5, y=280, anchor="center")

        slider = tk.Scale(page, from_=1, to=10, orient="horizontal",
                          variable=self.energy_var, command=self._on_energy_change,
                          bg=BG, fg=TEXT, troughcolor=BORDER, activebackground=ACCENT,
                          highlightthickness=0, bd=0, sliderlength=24,
                          length=420, showvalue=False)
        slider.place(relx=0.5, y=340, anchor="center")

        # Low / High labels
        tk.Label(page, text="CALM", font=self.font_small, bg=BG, fg=TEXT_DIM).place(relx=0.5, y=370, anchor="center", x=-210)
        tk.Label(page, text="INTENSE", font=self.font_small, bg=BG, fg=TEXT_DIM).place(relx=0.5, y=370, anchor="center", x=210)

    def _on_energy_change(self, val: str) -> None:
        self.preferred_energy = int(val) / 10
        self.energy_label.configure(text=val)

    # ── Page 4 — Playlist size ─────────────────────────────────────────────
    def _build_page_count(self) -> None:
        page = tk.Frame(self, bg=BG)
        self.pages.append(page)

        tk.Label(page, text="PLAYLISTIFY", font=self.font_title,
                 bg=BG, fg=ACCENT).place(relx=0.5, y=48, anchor="center")

        tk.Label(page, text="How many songs?", font=self.font_label,
                 bg=BG, fg=TEXT).place(relx=0.5, y=180, anchor="center")

        self.count_var = tk.StringVar(value="10")

        count_frame = tk.Frame(page, bg=BORDER, padx=1, pady=1)
        count_frame.place(relx=0.5, y=260, anchor="center", width=200, height=56)

        tk.Entry(count_frame, textvariable=self.count_var,
                 font=tkfont.Font(family="Courier New", size=22, weight="bold"),
                 bg=SURFACE, fg=ACCENT, insertbackground=ACCENT,
                 justify="center", relief="flat", bd=8).pack(fill="both", expand=True)

        tk.Label(page, text="Enter a number greater than 0",
                 font=self.font_small, bg=BG, fg=TEXT_DIM).place(relx=0.5, y=310, anchor="center")

        tk.Button(page, text="Generate Playlist →",
                  font=self.font_input, bg=ACCENT, fg=BG,
                  relief="flat", bd=0, cursor="hand2",
                  activebackground=ACCENT_DIM, activeforeground=BG,
                  padx=24, pady=10, command=self._finish
                  ).place(relx=0.5, y=400, anchor="center")

    # ── Finish ─────────────────────────────────────────────────────────────
    def _finish(self) -> None:
        """Validate and print collected preferences, ready to pass to main logic."""
        try:
            n = int(self.count_var.get())
            if n <= 0:
                raise ValueError
            self.recommend_n_songs = n
        except ValueError:
            self.count_var.set("10")
            self.recommend_n_songs = 10

        print("\nPreferences collected:")
        print(f"  Genres:        {self.preferred_genres}")
        print(f"  Viral songs:   {self.preferred_viral}")
        print(f"  Min energy:    {self.preferred_energy}")
        print(f"  Playlist size: {self.recommend_n_songs}")

        # TODO: pass these values into the recommendation pipeline


if __name__ == "__main__":
    app = PlaylistifyApp()
    app.mainloop()

import json
import os
import random
import shutil
import tkinter as tk
from tkinter import messagebox, ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DECKS_DIR = os.path.join(BASE_DIR, "decks")
ARCHIVE_DIR = os.path.join(DECKS_DIR, "mastered_archive")
MASTERED_FILE = os.path.join(BASE_DIR, "mastered_cards.json")

# Dark-Mode Palette
BG_MAIN = "#12151C"
BG_PANEL = "#1A1F2B"
BG_CARD = "#212736"
BG_CODE = "#0D1017"
FG_PRIMARY = "#E6EDF3"
FG_MUTED = "#8B949E"
ACCENT_BLUE = "#3B82F6"
ACCENT_GREEN = "#10B981"
ACCENT_AMBER = "#F59E0B"
ACCENT_RED = "#EF4444"
BORDER_COLOR = "#30363D"


class FlashcardTrainerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BS-CS-CPSE Flashcard & Code-Output Drill Trainer")
        self.root.geometry("1040x780")
        self.root.minsize(880, 640)
        self.root.configure(bg=BG_MAIN)

        os.makedirs(DECKS_DIR, exist_ok=True)
        os.makedirs(ARCHIVE_DIR, exist_ok=True)

        self.mastered_ids = self._load_mastered()
        self.decks = {}
        self.session_queue = []
        self.current_card = None
        self.answer_revealed = False
        self.session_correct = 0
        self.session_missed = 0

        self._build_ui()
        self._bind_shortcuts()
        self.reload_decks()

    # ------------------------------------------------------------------
    # Data & Persistence
    # ------------------------------------------------------------------
    def _load_mastered(self) -> set:
        if os.path.exists(MASTERED_FILE):
            try:
                with open(MASTERED_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return set(data.get("mastered_ids", []))
            except Exception:
                return set()
        return set()

    def _save_mastered(self):
        with open(MASTERED_FILE, "w", encoding="utf-8") as f:
            json.dump({"mastered_ids": sorted(self.mastered_ids)}, f, indent=2)

    def reload_decks(self):
        self.decks.clear()
        os.makedirs(DECKS_DIR, exist_ok=True)

        json_files = sorted(
            f for f in os.listdir(DECKS_DIR)
            if f.lower().endswith(".json") and os.path.isfile(os.path.join(DECKS_DIR, f))
        )

        for fname in json_files:
            fpath = os.path.join(DECKS_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                deck_title = raw.get("deck_name", fname.replace(".json", ""))
                cards = raw.get("cards", [])
                normalized_cards = []
                for idx, c in enumerate(cards):
                    cid = c.get("id") or f"{fname}::{idx}"
                    ans = c.get("answer", "")
                    accepted = c.get("accepted_answers", [])
                    if isinstance(accepted, str):
                        accepted = [accepted]
                    if ans and ans not in accepted:
                        accepted = [ans] + list(accepted)

                    normalized_cards.append({
                        "id": cid,
                        "deck_file": fname,
                        "deck_name": deck_title,
                        "category": c.get("category", "General"),
                        "type": c.get("type", "flashcard"),
                        "prompt": c.get("prompt", ""),
                        "code": c.get("code", ""),
                        "answer": ans,
                        "accepted_answers": accepted,
                        "explanation": c.get("explanation", "")
                    })
                self.decks[fname] = {
                    "file": fname,
                    "deck_name": deck_title,
                    "cards": normalized_cards
                }
            except Exception as e:
                messagebox.showerror("Deck Load Error", f"Failed to load {fname}:\n{e}")

        deck_options = ["All Active Decks"] + [
            f"{d['deck_name']} ({fname})" for fname, d in self.decks.items()
        ]
        self.deck_combo["values"] = deck_options
        if deck_options:
            self.deck_var.set(deck_options[0])

        self._update_category_filter()
        self.start_new_session()

    def _get_selected_deck_files(self) -> list:
        sel = self.deck_var.get()
        if not sel or sel == "All Active Decks":
            return list(self.decks.keys())
        for fname in self.decks:
            if sel.endswith(f"({fname})"):
                return [fname]
        return list(self.decks.keys())

    def _update_category_filter(self):
        files = self._get_selected_deck_files()
        cats = set()
        for f in files:
            for c in self.decks[f]["cards"]:
                cats.add(c["category"])
        cat_list = ["All Categories"] + sorted(cats)
        self.cat_combo["values"] = cat_list
        if self.cat_var.get() not in cat_list:
            self.cat_var.set("All Categories")

    # ------------------------------------------------------------------
    # UI Layout (Input Box Permanently Visible Inside GUI Card Stage)
    # ------------------------------------------------------------------
    def _build_ui(self):
        # Top Control Bar
        top_bar = tk.Frame(
            self.root, bg=BG_PANEL, padx=14, pady=10,
            highlightbackground=BORDER_COLOR, highlightthickness=1
        )
        top_bar.pack(fill=tk.X, padx=12, pady=(12, 6))

        tk.Label(top_bar, text="Deck:", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.deck_var = tk.StringVar(value="All Active Decks")
        self.deck_combo = ttk.Combobox(top_bar, textvariable=self.deck_var, state="readonly", width=34)
        self.deck_combo.pack(side=tk.LEFT, padx=(6, 14))
        self.deck_combo.bind("<<ComboboxSelected>>", lambda e: (self._update_category_filter(), self.start_new_session()))

        tk.Label(top_bar, text="Topic:", bg=BG_PANEL, fg=FG_MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.cat_var = tk.StringVar(value="All Categories")
        self.cat_combo = ttk.Combobox(top_bar, textvariable=self.cat_var, state="readonly", width=22)
        self.cat_combo.pack(side=tk.LEFT, padx=(6, 14))
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self.start_new_session())

        self.hide_mastered_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            top_bar, text="Hide Mastered", variable=self.hide_mastered_var,
            command=self.start_new_session, bg=BG_PANEL, fg=FG_PRIMARY,
            selectcolor=BG_CODE, activebackground=BG_PANEL, activeforeground=FG_PRIMARY,
            font=("Segoe UI", 9)
        ).pack(side=tk.LEFT, padx=(0, 12))

        tk.Button(
            top_bar, text="Reload Decks", command=self.reload_decks,
            bg=BG_CARD, fg=FG_PRIMARY, relief=tk.FLAT, padx=10, pady=4, font=("Segoe UI", 9)
        ).pack(side=tk.RIGHT, padx=(6, 0))

        tk.Button(
            top_bar, text="Archive Selected Deck", command=self.archive_selected_deck,
            bg="#2D2024", fg="#FCA5A5", relief=tk.FLAT, padx=10, pady=4, font=("Segoe UI", 9)
        ).pack(side=tk.RIGHT)

        # Stats Strip
        stats_bar = tk.Frame(self.root, bg=BG_MAIN, padx=14)
        stats_bar.pack(fill=tk.X, pady=(2, 6))

        self.stats_label = tk.Label(
            stats_bar, text="Remaining: 0 | Session Mastered: 0 | Re-Queued: 0 | All-Time Mastered: 0",
            bg=BG_MAIN, fg=FG_MUTED, font=("Segoe UI", 9, "bold")
        )
        self.stats_label.pack(side=tk.LEFT)

        tk.Button(
            stats_bar, text="Reset Mastered Progress", command=self.reset_mastered,
            bg=BG_MAIN, fg=FG_MUTED, relief=tk.FLAT, font=("Segoe UI", 8, "underline")
        ).pack(side=tk.RIGHT)

        # Main Card Stage
        self.card_frame = tk.Frame(
            self.root, bg=BG_CARD, padx=22, pady=16,
            highlightbackground=BORDER_COLOR, highlightthickness=1
        )
        self.card_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        header_row = tk.Frame(self.card_frame, bg=BG_CARD)
        header_row.pack(fill=tk.X, pady=(0, 8))

        self.badge_label = tk.Label(
            header_row, text="CATEGORY • TYPE", bg=BG_CODE, fg=ACCENT_BLUE,
            padx=10, pady=3, font=("Consolas", 9, "bold")
        )
        self.badge_label.pack(side=tk.LEFT)

        self.deck_tag_label = tk.Label(
            header_row, text="", bg=BG_CARD, fg=FG_MUTED, font=("Segoe UI", 9)
        )
        self.deck_tag_label.pack(side=tk.RIGHT)

        # Prompt Display
        self.prompt_text = tk.Text(
            self.card_frame, height=3, wrap=tk.WORD, bg=BG_CARD, fg=FG_PRIMARY,
            relief=tk.FLAT, font=("Segoe UI", 12, "bold"), padx=4, pady=2
        )
        self.prompt_text.pack(fill=tk.X)
        self.prompt_text.configure(state=tk.DISABLED)

        # Optional Code Snippet Box
        self.code_frame = tk.Frame(self.card_frame, bg=BG_CODE, highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.code_text = tk.Text(
            self.code_frame, height=8, wrap=tk.NONE, bg=BG_CODE, fg="#A5D6FF",
            relief=tk.FLAT, font=("Consolas", 11), padx=12, pady=8
        )
        self.code_text.pack(fill=tk.BOTH, expand=True)
        self.code_text.configure(state=tk.DISABLED)

        # ALWAYS-VISIBLE GUI INPUT BOX FOR USER'S ANSWER
        self.input_frame = tk.Frame(self.card_frame, bg=BG_CARD, pady=8)
        self.input_frame.pack(fill=tk.X)

        input_header = tk.Frame(self.input_frame, bg=BG_CARD)
        input_header.pack(fill=tk.X, pady=(0, 4))

        self.input_label = tk.Label(
            input_header,
            text="Type Your Answer Below (Press Enter for single-line check, or Ctrl+Enter for multi-line):",
            bg=BG_CARD, fg=ACCENT_AMBER, font=("Segoe UI", 9, "bold")
        )
        self.input_label.pack(side=tk.LEFT)

        self.user_answer_box = tk.Text(
            self.input_frame, height=3, bg=BG_CODE, fg=FG_PRIMARY, insertbackground=FG_PRIMARY,
            relief=tk.FLAT, font=("Consolas", 11), padx=10, pady=8,
            highlightbackground=ACCENT_BLUE, highlightthickness=2
        )
        self.user_answer_box.pack(fill=tk.X)

        # Validation Result & Expected Answer Panel (Revealed after checking)
        self.answer_frame = tk.Frame(
            self.card_frame, bg="#16202A", padx=14, pady=10,
            highlightbackground=ACCENT_GREEN, highlightthickness=1
        )
        self.grade_banner = tk.Label(
            self.answer_frame, text="", bg="#16202A", fg=ACCENT_GREEN,
            font=("Segoe UI", 10, "bold"), anchor="w"
        )
        self.grade_banner.pack(fill=tk.X)

        self.answer_text = tk.Text(
            self.answer_frame, height=6, wrap=tk.WORD, bg="#16202A", fg=FG_PRIMARY,
            relief=tk.FLAT, font=("Consolas", 11), padx=2, pady=4
        )
        self.answer_text.pack(fill=tk.BOTH, expand=True)
        self.answer_text.configure(state=tk.DISABLED)

        # Bottom Action Controls
        bottom_bar = tk.Frame(self.root, bg=BG_MAIN, padx=12, pady=12)
        bottom_bar.pack(fill=tk.X)

        self.check_btn = tk.Button(
            bottom_bar, text="Check My Answer  [Ctrl+Enter]", command=self.validate_and_reveal,
            bg=ACCENT_BLUE, fg="#FFFFFF", relief=tk.FLAT, padx=18, pady=9,
            font=("Segoe UI", 10, "bold")
        )
        self.check_btn.pack(side=tk.LEFT)

        self.again_btn = tk.Button(
            bottom_bar, text="Again (Re-Queue)  [1]", command=self.mark_again,
            bg=ACCENT_RED, fg="#FFFFFF", relief=tk.FLAT, padx=16, pady=9,
            font=("Segoe UI", 10, "bold"), state=tk.DISABLED
        )
        self.again_btn.pack(side=tk.LEFT, padx=(12, 8))

        self.got_it_btn = tk.Button(
            bottom_bar, text="Got It (Mark Mastered)  [2]", command=self.mark_got_it,
            bg=ACCENT_GREEN, fg="#FFFFFF", relief=tk.FLAT, padx=16, pady=9,
            font=("Segoe UI", 10, "bold"), state=tk.DISABLED
        )
        self.got_it_btn.pack(side=tk.LEFT)

        self.skip_btn = tk.Button(
            bottom_bar, text="Skip  [Right]", command=self.skip_card,
            bg=BG_PANEL, fg=FG_MUTED, relief=tk.FLAT, padx=14, pady=9,
            font=("Segoe UI", 9)
        )
        self.skip_btn.pack(side=tk.RIGHT)

    def _bind_shortcuts(self):
        self.user_answer_box.bind("<Return>", self._on_enter_in_box)
        self.user_answer_box.bind("<Control-Return>", self._on_ctrl_enter)
        self.root.bind("<Control-Return>", self._on_ctrl_enter)
        self.root.bind("1", lambda e: self._if_not_typing(self.mark_again))
        self.root.bind("2", lambda e: self._if_not_typing(self.mark_got_it))
        self.root.bind("<Right>", lambda e: self._if_not_typing(self.skip_card))

    def _if_not_typing(self, fn):
        if self.root.focus_get() != self.user_answer_box:
            fn()

    def _on_enter_in_box(self, event):
        if not self.current_card:
            return "break"
        # If the expected answer is single-line, pressing Enter immediately checks it!
        # If the expected answer is multi-line, Enter inserts a newline and Ctrl+Enter checks it.
        expected = self.current_card["answer"].strip().replace("\r\n", "\n")
        if "\n" not in expected and not self.answer_revealed:
            self.validate_and_reveal()
            return "break"
        return None

    def _on_ctrl_enter(self, event):
        if not self.answer_revealed:
            self.validate_and_reveal()
        return "break"

    # ------------------------------------------------------------------
    # Session & Validation Logic
    # ------------------------------------------------------------------
    def start_new_session(self):
        files = self._get_selected_deck_files()
        selected_cat = self.cat_var.get()
        hide_mastered = self.hide_mastered_var.get()

        pool = []
        for f in files:
            for c in self.decks[f]["cards"]:
                if selected_cat != "All Categories" and c["category"] != selected_cat:
                    continue
                if hide_mastered and c["id"] in self.mastered_ids:
                    continue
                pool.append(c)

        random.shuffle(pool)
        self.session_queue = pool
        self.session_correct = 0
        self.session_missed = 0
        self.next_card()

    def next_card(self):
        self.answer_revealed = False
        self.answer_frame.pack_forget()
        self.again_btn.configure(state=tk.DISABLED)
        self.got_it_btn.configure(state=tk.DISABLED)
        self.check_btn.configure(state=tk.NORMAL)

        if not self.session_queue:
            self.current_card = None
            self.badge_label.configure(text="SESSION COMPLETE", fg=ACCENT_GREEN)
            self.deck_tag_label.configure(text="")
            self._set_text(
                self.prompt_text,
                "No remaining unmastered cards in this filter!\n\n"
                "Drop more .json deck files into the 'decks/' folder and click 'Reload Decks', "
                "or uncheck 'Hide Mastered' to review everything."
            )
            self.code_frame.pack_forget()
            self.input_frame.pack_forget()
            self.check_btn.configure(state=tk.DISABLED)
            self._update_stats()
            return

        self.current_card = self.session_queue.pop(0)
        c = self.current_card

        is_code = c["type"] == "code_output"
        mode_tag = "CODE OUTPUT DRILL" if is_code else "TYPED FLASHCARD"
        self.badge_label.configure(
            text=f"{c['category'].upper()}  •  {mode_tag}",
            fg=ACCENT_AMBER if is_code else ACCENT_BLUE
        )
        self.deck_tag_label.configure(text=f"Deck: {c['deck_name']}")
        self._set_text(self.prompt_text, c["prompt"])

        if c["code"].strip():
            lines = c["code"].count("\n") + 1
            self.code_text.configure(height=min(max(lines + 1, 4), 12))
            self._set_text(self.code_text, c["code"])
            self.code_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 6))
        else:
            self.code_frame.pack_forget()

        # Always show and focus the GUI input box
        expected = c["answer"].strip().replace("\r\n", "\n")
        if is_code:
            self.input_label.configure(
                text="Type Exact Console Output Below (Enter = submit single-line | Ctrl+Enter = submit multi-line):"
            )
        else:
            hint = "Enter = submit" if "\n" not in expected else "Multi-line answer: Ctrl+Enter = submit"
            self.input_label.configure(text=f"Type Your Command / Answer Below ({hint}):")

        self.user_answer_box.configure(state=tk.NORMAL, highlightbackground=ACCENT_BLUE)
        self.user_answer_box.delete("1.0", tk.END)
        self.input_frame.pack(fill=tk.X, pady=(4, 6))
        self.user_answer_box.focus_set()

        self._update_stats()

    @staticmethod
    def _normalize_text(text: str, strict_whitespace: bool) -> str:
        text = text.strip().replace("\r\n", "\n")
        if strict_whitespace:
            return text
        lines = [" ".join(line.strip().split()) for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def validate_and_reveal(self):
        if not self.current_card or self.answer_revealed:
            return
        self.answer_revealed = True
        c = self.current_card

        raw_user = self.user_answer_box.get("1.0", tk.END)
        strict = (c["type"] == "code_output")
        norm_user = self._normalize_text(raw_user, strict_whitespace=strict)

        valid_targets = [
            self._normalize_text(ans, strict_whitespace=strict)
            for ans in c["accepted_answers"]
            if ans.strip()
        ]

        is_match = (norm_user in valid_targets) and (norm_user != "")

        if is_match:
            self.grade_banner.configure(text="CORRECT MATCH!", fg=ACCENT_GREEN)
            self.answer_frame.configure(highlightbackground=ACCENT_GREEN)
            self.user_answer_box.configure(highlightbackground=ACCENT_GREEN)
        elif norm_user == "":
            self.grade_banner.configure(text="NO ANSWER ENTERED — REVIEW EXPECTED ANSWER", fg=ACCENT_AMBER)
            self.answer_frame.configure(highlightbackground=ACCENT_AMBER)
            self.user_answer_box.configure(highlightbackground=ACCENT_AMBER)
        else:
            self.grade_banner.configure(
                text=f"NOT A MATCH — You typed: {repr(raw_user.strip())}", fg=ACCENT_RED
            )
            self.answer_frame.configure(highlightbackground=ACCENT_RED)
            self.user_answer_box.configure(highlightbackground=ACCENT_RED)

        self.user_answer_box.configure(state=tk.DISABLED)

        body = f"Expected Answer:\n{c['answer']}"
        if len(c["accepted_answers"]) > 1:
            alts = [a for a in c["accepted_answers"] if a != c["answer"]]
            if alts:
                body += "\n\nAlso Accepted:\n" + "\n".join(alts)
        if c["explanation"].strip():
            body += f"\n\nWhy:\n{c['explanation']}"

        self._set_text(self.answer_text, body)
        self.answer_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 4))

        self.check_btn.configure(state=tk.DISABLED)
        self.again_btn.configure(state=tk.NORMAL)
        self.got_it_btn.configure(state=tk.NORMAL)
        self.root.focus_set()

    def mark_again(self):
        if not self.current_card or not self.answer_revealed:
            return
        self.session_missed += 1
        insert_pos = min(2, len(self.session_queue))
        self.session_queue.insert(insert_pos, self.current_card)
        self.next_card()

    def mark_got_it(self):
        if not self.current_card or not self.answer_revealed:
            return
        self.session_correct += 1
        self.mastered_ids.add(self.current_card["id"])
        self._save_mastered()
        self.next_card()

    def skip_card(self):
        if not self.current_card:
            return
        self.session_queue.append(self.current_card)
        self.next_card()

    def archive_selected_deck(self):
        files = self._get_selected_deck_files()
        if len(files) != 1:
            messagebox.showinfo(
                "Select Single Deck",
                "Choose a specific deck in the 'Deck' dropdown before archiving."
            )
            return
        fname = files[0]
        if messagebox.askyesno(
            "Archive Deck",
            f"Move '{fname}' to decks/mastered_archive/?\n(You can move it back anytime.)"
        ):
            shutil.move(os.path.join(DECKS_DIR, fname), os.path.join(ARCHIVE_DIR, fname))
            self.reload_decks()

    def reset_mastered(self):
        if messagebox.askyesno("Reset Progress", "Clear all mastered card history?"):
            self.mastered_ids.clear()
            self._save_mastered()
            self.start_new_session()

    def _update_stats(self):
        rem = len(self.session_queue) + (1 if self.current_card else 0)
        self.stats_label.configure(
            text=(
                f"Remaining in Queue: {rem}   |   "
                f"Session Mastered: {self.session_correct}   |   "
                f"Re-Queued: {self.session_missed}   |   "
                f"All-Time Mastered: {len(self.mastered_ids)}"
            )
        )

    @staticmethod
    def _set_text(widget: tk.Text, content: str):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardTrainerApp(root)
    root.mainloop()

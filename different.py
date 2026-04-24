# main_quiz_app.py
"""
Main GUI app for Umer's Quiz Pro+ — Multi-language final
Run this file. It imports QUESTIONS from questions_data.py
"""

import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import random, os, json, hashlib, threading
from datetime import datetime

# optionally matplotlib for graphs
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except Exception:
    MATPLOTLIB_AVAILABLE = False

# try winsound/playsound for optional sound feedback
SOUND_AVAILABLE = False
try:
    import winsound
    SOUND_AVAILABLE = True
except Exception:
    try:
        from playsound import playsound
        SOUND_AVAILABLE = True
    except Exception:
        SOUND_AVAILABLE = False

# import QUESTIONS
from questions_data import QUESTIONS

# ---------------- Config & theme ----------------
USERS_FILE = "users.json"
LEADERBOARD_FILE = "leaderboard.json"
RESULTS_FILE = "quiz_results.txt"
LOGO_FILE = "quiz_logo.png"
CORRECT_WAV = "correct.wav"
WRONG_WAV = "wrong.wav"

QUESTION_TIME = 15
MAX_LEADERBOARD = 5

LIGHT_THEME = {
    "bg": "#ffffff",
    "panel": "#f0f6ff",
    "fg": "#0b3b66",
    "btn_bg": "#4a90e2",
    "btn_fg": "#ffffff",
    "accent": "#4a90e2",
    "hover": "#d9d9d9"
}
DARK_THEME = {
    "bg": "#111827",
    "panel": "#1f2937",
    "fg": "#e6eef8",
    "btn_bg": "#2563eb",
    "btn_fg": "#ffffff",
    "accent": "#60a5fa",
    "hover": "#374151"
}
# questions_data.py
# Question bank: languages -> topics -> list of question dicts (20 per topic)
# Each question dict: {"question": str, "options": [..4..], "answer": str}



# ---------------- utilities ----------------
def hash_password(password: str):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def ensure_files():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": {}, "last_email": ""}, f)
    if not os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    if not os.path.exists(RESULTS_FILE):
        open(RESULTS_FILE, "w", encoding="utf-8").close()

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}, "last_email": ""}

def save_users(data):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def load_leaderboard():
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_leaderboard(lb):
    try:
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(lb, f, indent=2)
    except Exception:
        pass

def add_to_leaderboard(name, topic, score, total, percent):
    lb = load_leaderboard()
    entry = {"name": name, "topic": topic, "score": score, "total": total, "percent": percent, "time": datetime.now().isoformat()}
    lb.append(entry)
    lb = sorted(lb, key=lambda e: (-e["percent"], -e["score"], e["time"]))[:MAX_LEADERBOARD]
    save_leaderboard(lb)

def save_result_text(name, topic, score, total, percent):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{now} | {name} | Topic: {topic} | Score: {score}/{total} | {percent}%\n"
    try:
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

def play_correct_sound():
    if not SOUND_AVAILABLE: return
    try:
        if 'winsound' in globals():
            winsound.MessageBeep(winsound.MB_OK)
        else:
            if os.path.exists(CORRECT_WAV):
                threading.Thread(target=playsound, args=(CORRECT_WAV,), daemon=True).start()
    except Exception:
        pass

def play_wrong_sound():
    if not SOUND_AVAILABLE: return
    try:
        if 'winsound' in globals():
            winsound.MessageBeep(winsound.MB_ICONHAND)
        else:
            if os.path.exists(WRONG_WAV):
                threading.Thread(target=playsound, args=(WRONG_WAV,), daemon=True).start()
    except Exception:
        pass

# ---------------- Styled big buttons ----------------
class StyledButton(tk.Button):
    def __init__(self, master=None, theme=None, big=False, **kwargs):
        self.theme = theme or LIGHT_THEME
        self.big = big
        super().__init__(master, **kwargs)
        self.default_bg = self.theme["btn_bg"]
        self.default_fg = self.theme["btn_fg"]
        self.hover_bg = self.theme["hover"]
        if self.big:
            font = ("Arial", 16, "bold")
            padx, pady = 24, 18
        else:
            font = ("Arial", 11, "bold")
            padx, pady = 12, 8
        self.configure(bg=self.default_bg, fg=self.default_fg, bd=0, relief="flat", activebackground=self.hover_bg,
                       font=font, cursor="hand2", padx=padx, pady=pady)
        self.configure(highlightthickness=0)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        try:
            self.configure(bg=self.hover_bg, fg="#000000")
        except Exception:
            pass

    def on_leave(self, e):
        try:
            self.configure(bg=self.default_bg, fg=self.default_fg)
        except Exception:
            pass

    def update_theme(self, theme):
        self.theme = theme
        self.default_bg = theme["btn_bg"]
        self.default_fg = theme["btn_fg"]
        self.hover_bg = theme["hover"]
        self.configure(bg=self.default_bg, fg=self.default_fg, activebackground=self.hover_bg)

# ---------------- Main App ----------------
class MultiLangQuizApp:
    def __init__(self, root):
        ensure_files()
        self.root = root
        self.root.title("Umer's Quiz Pro+ — Multi-language")
        self.root.geometry("1040x760")
        self.root.resizable(False, False)

        self.theme = LIGHT_THEME
        self.username = None
        self.user_email = None

        # quiz state
        self.current_language = None
        self.current_topic = None
        self.question_list = []
        self.question_index = 0
        self.user_answers = []
        self.score = 0
        self.timer_after_id = None
        self.time_left = QUESTION_TIME

        # top frame
        self.top_frame = tk.Frame(root, bg=self.theme["accent"])
        self.top_frame.pack(fill="x")
        self._build_topbar()

        # main container
        self.container = tk.Frame(root, bg=self.theme["bg"])
        self.container.pack(fill="both", expand=True)

        users = load_users()
        last_email = users.get("last_email", "")
        if last_email:
            self.show_quick_login(last_email)
        else:
            self.show_signup_screen()

    def _build_topbar(self):
        for w in self.top_frame.winfo_children():
            w.destroy()
        try:
            img = Image.open(LOGO_FILE)
            img = img.resize((56,56))
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(self.top_frame, image=self.logo_img, bg=self.theme["accent"]).pack(side="left", padx=10, pady=6)
        except Exception:
            tk.Label(self.top_frame, text="🧠", font=("Arial",28), bg=self.theme["accent"], fg="white").pack(side="left", padx=12, pady=6)
        tk.Label(self.top_frame, text="Umer's Quiz Pro+ (Multi-language)", bg=self.theme["accent"], fg="white", font=("Helvetica",20,"bold")).pack(side="left", padx=6)
        self.user_label = tk.Label(self.top_frame, text="Not signed in", bg=self.theme["accent"], fg="white", font=("Arial",10))
        self.user_label.pack(side="right", padx=10)
        self.theme_btn = tk.Button(self.top_frame, text="Toggle Dark Mode", command=self.toggle_theme, bg="#ffffff")
        self.theme_btn.pack(side="right", padx=8, pady=8)
        tk.Button(self.top_frame, text="Leaderboard", command=self.show_leaderboard_window, bg="#ffffff").pack(side="right", padx=8, pady=8)

    # ------------- Signup / Quick login -------------
    def show_signup_screen(self):
        for w in self.container.winfo_children():
            w.destroy()
        f = tk.Frame(self.container, bg=self.theme["bg"])
        f.pack(expand=True)
        tk.Label(f, text="Welcome to Umer's Quiz Pro+", font=("Helvetica",24,"bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=8)
        tk.Label(f, text="Create account: Name, Email, Password", bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=6)
        self.entry_name = tk.Entry(f, font=("Arial",14), width=36)
        self.entry_name.pack(pady=6)
        self.entry_name.insert(0, "Your name")
        self.entry_email = tk.Entry(f, font=("Arial",14), width=36)
        self.entry_email.pack(pady=6)
        self.entry_email.insert(0, "you@example.com")
        self.entry_password = tk.Entry(f, font=("Arial",14), width=36, show="*")
        self.entry_password.pack(pady=6)
        btn = StyledButton(f, theme=self.theme, text="Create Account", big=False, command=self.do_signup)
        btn.pack(pady=10)
        self.apply_theme(f)

    def do_signup(self):
        name = self.entry_name.get().strip()
        email = self.entry_email.get().strip().lower()
        password = self.entry_password.get().strip()
        if not (name and email and password):
            messagebox.showwarning("Incomplete", "Please fill name, email and password.")
            return
        users = load_users()
        if email in users["users"]:
            messagebox.showinfo("Exists", "Email already registered — switching to quick login.")
            users["last_email"] = email
            save_users(users)
            self.show_quick_login(email)
            return
        users["users"][email] = {"name": name, "password_hash": hash_password(password)}
        users["last_email"] = email
        save_users(users)
        self.username = name
        self.user_email = email
        self.user_label.configure(text=f"Signed in: {self.username}")
        messagebox.showinfo("Account Created", "Account created and signed in.")
        self.show_language_selection()

    def show_quick_login(self, email):
        for w in self.container.winfo_children():
            w.destroy()
        f = tk.Frame(self.container, bg=self.theme["bg"])
        f.pack(expand=True)
        tk.Label(f, text="Quick Login", font=("Helvetica",20,"bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=8)
        tk.Label(f, text=f"Email: {email}", bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=4)
        self.pw_entry = tk.Entry(f, font=("Arial",14), width=36, show="*")
        self.pw_entry.pack(pady=6)
        btn = StyledButton(f, theme=self.theme, text="Login", big=False, command=lambda: self.do_quick_login(email))
        btn.pack(pady=8)
        btn2 = StyledButton(f, theme=self.theme, text="Use different account", big=False, command=self.show_signup_screen)
        btn2.pack(pady=6)
        self.apply_theme(f)

    def do_quick_login(self, email):
        pw = self.pw_entry.get().strip()
        if not pw:
            messagebox.showwarning("Enter password", "Please enter your password.")
            return
        users = load_users()
        stored = users["users"].get(email)
        if not stored:
            messagebox.showerror("Not found", "Account not found — please sign up.")
            users["last_email"] = ""
            save_users(users)
            return self.show_signup_screen()
        if hash_password(pw) == stored["password_hash"]:
            self.username = stored["name"]
            self.user_email = email
            users["last_email"] = email
            save_users(users)
            self.user_label.configure(text=f"Signed in: {self.username}")
            messagebox.showinfo("Welcome back", f"Welcome, {self.username}!")
            self.show_language_selection()
        else:
            messagebox.showerror("Wrong", "Password incorrect.")

    # ------------- Theme -------------
    def toggle_theme(self):
        self.theme = DARK_THEME if self.theme == LIGHT_THEME else LIGHT_THEME
        self.top_frame.configure(bg=self.theme["accent"])
        self._build_topbar()
        self.apply_theme(self.container)

    def apply_theme(self, widget):
        try:
            widget.configure(bg=self.theme["bg"])
        except Exception:
            pass
        for child in widget.winfo_children():
            try:
                if isinstance(child, tk.Label):
                    child.configure(bg=self.theme["bg"], fg=self.theme["fg"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=self.theme["bg"])
                elif isinstance(child, tk.Button) and not isinstance(child, StyledButton):
                    child.configure(bg=self.theme["panel"], fg=self.theme["fg"], activebackground=self.theme["accent"])
                elif isinstance(child, tk.Entry):
                    child.configure(bg="#ffffff" if self.theme==LIGHT_THEME else "#111827", fg=self.theme["fg"])
                elif isinstance(child, ttk.Progressbar):
                    pass
            except Exception:
                pass
            self.apply_theme(child)

    # ------------- Language selection -------------
    def show_language_selection(self):
        for w in self.container.winfo_children():
            w.destroy()
        f = tk.Frame(self.container, bg=self.theme["bg"])
        f.pack(expand=True, pady=20)
        tk.Label(f, text=f"Hello, {self.username} — Which quiz would you like?", bg=self.theme["bg"], fg=self.theme["fg"], font=("Helvetica", 20, "bold")).pack(pady=8)
        grid = tk.Frame(f, bg=self.theme["bg"])
        grid.pack(pady=12)
        languages = list(QUESTIONS.keys())
        for i, lang in enumerate(languages):
            btn = StyledButton(grid, theme=self.theme, big=True, text=lang, command=lambda l=lang: self.select_language(l))
            btn.grid(row=i//2, column=i%2, padx=18, pady=18)
        tk.Button(f, text="Logout", command=self.logout, bg="#d9534f", fg="white").pack(pady=12)
        self.apply_theme(f)

    def logout(self):
        users = load_users()
        users["last_email"] = users.get("last_email","")
        save_users(users)
        self.username = None
        self.user_email = None
        self.user_label.configure(text="Not signed in")
        last = load_users().get("last_email","")
        if last:
            self.show_quick_login(last)
        else:
            self.show_signup_screen()

    def select_language(self, language):
        self.current_language = language
        # go to topics screen for chosen language
        self.show_topics_screen(language)

    # ------------- Topics screen (language-specific) -------------
    def show_topics_screen(self, language=None):
        if language is None:
            language = self.current_language
        for w in self.container.winfo_children():
            w.destroy()
        self.current_language = language
        f = tk.Frame(self.container, bg=self.theme["bg"])
        f.pack(expand=True, pady=10)
        tk.Label(f, text=f"{self.username} — {language} topics", font=("Helvetica", 20, "bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=8)
        grid = tk.Frame(f, bg=self.theme["bg"])
        grid.pack(pady=8)
        topics_for_lang = list(QUESTIONS.get(language, {}).keys())
        for i, topic in enumerate(topics_for_lang):
            btn = StyledButton(grid, theme=self.theme, big=False, text=topic, command=lambda t=topic: self.start_topic(t))
            btn.grid(row=i//2, column=i%2, padx=12, pady=12)
        tk.Button(f, text="Back to Languages", command=self.show_language_selection, bg=self.theme["panel"]).pack(pady=12)
        self.apply_theme(f)

    # ------------- Start topic -------------
    def start_topic(self, topic_name):
        self.current_topic = topic_name
        pool = QUESTIONS[self.current_language][self.current_topic].copy()
        random.shuffle(pool)
        # ensure exactly 20 questions (pools provided have 20)
        self.question_list = pool[:20]
        self.user_answers = []
        self.question_index = 0
        self.score = 0
        self.show_question_screen()

    # ------------- Question screen -------------
    def show_question_screen(self):
        self.cancel_timer()
        for w in self.container.winfo_children():
            w.destroy()
        q = self.question_list[self.question_index]
        topbar = tk.Frame(self.container, bg=self.theme["bg"])
        topbar.pack(fill="x", pady=(6,0))
        tk.Label(topbar, text=f"{self.current_language} — {self.current_topic}", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",12,"bold")).pack(side="left", padx=8)
        tk.Label(topbar, text=f"Q {self.question_index+1}/{len(self.question_list)}", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",12)).pack(side="left")
        pb_frame = tk.Frame(self.container, bg=self.theme["bg"])
        pb_frame.pack(fill="x", padx=12, pady=(6,0))
        self.progress = ttk.Progressbar(pb_frame, maximum=len(self.question_list), value=len(self.user_answers))
        self.progress.pack(fill="x", pady=6)
        self.time_left = QUESTION_TIME
        self.timer_label = tk.Label(pb_frame, text=f"Time left: {self.time_left}s", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",11,"bold"))
        self.timer_label.pack(side="right", padx=8)
        tk.Label(self.container, text=f"Q{self.question_index+1}. {q['question']}", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",15,"bold"), wraplength=1000, justify="left").pack(pady=12, padx=8)
        opts = q["options"].copy()
        random.shuffle(opts)
        self.var = tk.StringVar(value="")
        opts_frame = tk.Frame(self.container, bg=self.theme["bg"])
        opts_frame.pack(pady=6)
        for opt in opts:
            rb = tk.Radiobutton(opts_frame, text=opt, variable=self.var, value=opt, font=("Arial",13),
                                bg=self.theme["panel"], fg=self.theme["fg"], anchor="w", width=110, padx=6, pady=6,
                                indicatoron=0, relief="raised", cursor="hand2")
            rb.pack(pady=6)
        if self.question_index < len(self.user_answers):
            prev = self.user_answers[self.question_index]["chosen"]
            if prev:
                self.var.set(prev)
        nav = tk.Frame(self.container, bg=self.theme["bg"])
        nav.pack(pady=14)
        tk.Button(nav, text="Topics", command=lambda: self.show_topics_screen(self.current_language), bg=self.theme["panel"]).grid(row=0, column=0, padx=8)
        prev_btn = tk.Button(nav, text="Previous", command=self.go_previous, bg=self.theme["panel"])
        prev_btn.grid(row=0, column=1, padx=8)
        submit_btn = StyledButton(nav, theme=self.theme, text="Submit", big=False, command=self.submit_answer)
        submit_btn.grid(row=0, column=2, padx=8)
        if self.question_index == 0:
            prev_btn.config(state="disabled")
        self.apply_theme(self.container)
        self.update_timer()

    def go_previous(self):
        if self.question_index > 0:
            self.question_index -= 1
            self.show_question_screen()

    # ------------- Timer -------------
    def update_timer(self):
        self.timer_label.config(text=f"Time left: {self.time_left}s")
        if self.time_left <= 0:
            self.submit_answer(auto=True)
            return
        self.time_left -= 1
        self.timer_after_id = self.root.after(1000, self.update_timer)

    def cancel_timer(self):
        try:
            if self.timer_after_id:
                self.root.after_cancel(self.timer_after_id)
        except Exception:
            pass
        self.timer_after_id = None

    # ------------- Submit answer -------------
    def submit_answer(self, auto=False):
        choice = self.var.get()
        if choice == "":
            if auto:
                choice = "No Answer"
            else:
                messagebox.showwarning("Select answer", "Please select an answer before submitting.")
                return
        q = self.question_list[self.question_index]
        correct = q["answer"]
        correct_flag = (choice == correct)
        if self.question_index < len(self.user_answers):
            self.user_answers[self.question_index].update({"chosen": choice, "correct": correct_flag})
        else:
            self.user_answers.append({
                "question": q["question"],
                "options": q["options"],
                "correct_answer": correct,
                "chosen": choice,
                "correct": correct_flag
            })
        if correct_flag:
            play_correct_sound()
        else:
            play_wrong_sound()
        self.score = sum(1 for a in self.user_answers if a["correct"])
        try:
            self.progress['value'] = len(self.user_answers)
        except Exception:
            pass
        self.question_index += 1
        if self.question_index < len(self.question_list):
            self.show_question_screen()
        else:
            self.cancel_timer()
            self.show_results()
            total = len(self.question_list)
            percent = int((self.score/total)*100) if total else 0
            add_to_leaderboard(self.username, f"{self.current_language} - {self.current_topic}", self.score, total, percent)
            save_result_text(self.username, f"{self.current_language} - {self.current_topic}", self.score, total, percent)

    # ------------- Results & Review (graph + leaderboard together) -------------
    def show_results(self):
        for w in self.container.winfo_children():
            w.destroy()
        total = len(self.question_list)
        percent = int((self.score/total)*100) if total else 0
        remark = "🌟 Outstanding!" if percent >= 80 else "👍 Good Job!" if percent >= 50 else "😅 Keep Practicing!"
        tk.Label(self.container, text="Quiz Completed", font=("Helvetica",22,"bold"), bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=8)
        tk.Label(self.container, text=f"{self.username} | {self.current_language} - {self.current_topic}", bg=self.theme["bg"], fg=self.theme["fg"]).pack()
        tk.Label(self.container, text=f"Score: {self.score}/{total}    Percentage: {percent}%", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",14,"bold")).pack(pady=6)
        tk.Label(self.container, text=remark, bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",12)).pack(pady=6)
        # Graph + Leaderboard area
        frame = tk.Frame(self.container, bg=self.theme["bg"])
        frame.pack(fill="both", expand=True, padx=12, pady=12)
        left = tk.Frame(frame, bg=self.theme["bg"])
        left.pack(side="left", fill="both", expand=True, padx=6)
        right = tk.Frame(frame, bg=self.theme["bg"], width=320)
        right.pack(side="right", fill="y", padx=6)
        correct_count = sum(1 for a in self.user_answers if a["correct"])
        wrong_count = len(self.user_answers) - correct_count
        if MATPLOTLIB_AVAILABLE:
            fig = Figure(figsize=(6,3), dpi=100)
            ax = fig.add_subplot(111)
            ax.bar(['Correct','Wrong'], [correct_count, wrong_count], color=[self.theme["accent"], "#e76f51"])
            ax.set_title("Correct vs Wrong")
            ax.set_ylabel("Count")
            canvas = FigureCanvasTkAgg(fig, master=left)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            tk.Label(left, text=f"Correct: {correct_count}\nWrong: {wrong_count}", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",14)).pack(pady=40)
        tk.Label(right, text="Leaderboard (Top)", bg=self.theme["bg"], fg=self.theme["fg"], font=("Arial",13,"bold")).pack(pady=6)
        lb = load_leaderboard()
        if not lb:
            tk.Label(right, text="No leaderboard data yet.", bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=10)
        else:
            for i, e in enumerate(lb, start=1):
                text = f"{i}. {e['name']} — {e['percent']}% ({e['score']}/{e['total']})\n{e['topic']} | {e['time'].split('T')[0]}"
                tk.Label(right, text=text, bg=self.theme["panel"], fg=self.theme["fg"], justify="left", wraplength=280, anchor="w").pack(fill="x", pady=6, padx=6)
        btns = tk.Frame(self.container, bg=self.theme["bg"])
        btns.pack(pady=10)
        StyledButton(btns, theme=self.theme, text="Restart Topic", big=False, command=lambda: self.start_topic(self.current_topic)).grid(row=0, column=0, padx=8)
        tk.Button(btns, text="Topics", command=lambda: self.show_topics_screen(self.current_language), bg=self.theme["panel"]).grid(row=0, column=1, padx=8)
        tk.Button(btns, text="Review Answers", command=self.open_review_window, bg=self.theme["panel"]).grid(row=0, column=2, padx=8)
        tk.Button(btns, text="Languages", command=self.show_language_selection, bg=self.theme["panel"]).grid(row=0, column=3, padx=8)
        self.apply_theme(self.container)

    def open_review_window(self):
        win = tk.Toplevel(self.root)
        win.title("Review Answers")
        win.geometry("980x600")
        header = tk.Label(win, text=f"Review — {self.current_language} - {self.current_topic}", bg="#0b4f8c", fg="white", font=("Helvetica",14,"bold"))
        header.pack(fill="x")
        canvas = tk.Canvas(win, bg="#f8fbff")
        scr = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg="#f8fbff")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scr.set)
        canvas.pack(side="left", fill="both", expand=True)
        scr.pack(side="right", fill="y")
        for i, a in enumerate(self.user_answers, start=1):
            ql = tk.Label(frame, text=f"{i}. {a['question']}", bg="#f8fbff", font=("Arial",11,"bold"), wraplength=920, justify="left")
            ql.pack(anchor="w", pady=(8,0), padx=8)
            chosen = a["chosen"]
            correct = a["correct_answer"]
            if a["correct"]:
                lbl = tk.Label(frame, text=f"Your answer: {chosen}  ✅", bg="#f8fbff", font=("Arial",11))
                lbl.pack(anchor="w", padx=20)
            else:
                lbl = tk.Label(frame, text=f"Your answer: {chosen}  ❌", bg="#f8fbff", font=("Arial",11))
                lbl.pack(anchor="w", padx=20)
                cl = tk.Label(frame, text=f"Correct answer: {correct}", bg="#f8fbff", font=("Arial",11,"bold"))
                cl.pack(anchor="w", padx=20)
        tk.Button(win, text="Close", command=win.destroy, bg="#0b5bd7", fg="white").pack(pady=8)

    def show_leaderboard_window(self):
        win = tk.Toplevel(self.root)
        win.title("Leaderboard")
        win.geometry("480x480")
        win.config(bg=self.theme["bg"])
        tk.Label(win, text="Leaderboard (Top Scores)", bg=self.theme["bg"], fg=self.theme["fg"], font=("Helvetica",14,"bold")).pack(pady=8)
        lb = load_leaderboard()
        if not lb:
            tk.Label(win, text="No entries yet.", bg=self.theme["bg"], fg=self.theme["fg"]).pack(pady=20)
        else:
            for i, e in enumerate(lb, start=1):
                tk.Label(win, text=f"{i}. {e['name']} — {e['percent']}% ({e['score']}/{e['total']})\n{e['topic']}", bg=self.theme["panel"], fg=self.theme["fg"], anchor="w", width=58).pack(pady=6, padx=8)
        tk.Button(win, text="Close", command=win.destroy, bg=self.theme["btn_bg"], fg=self.theme["btn_fg"]).pack(pady=10)

# ---------------- Run app ----------------
if __name__ == "__main__":
    ensure_files()
    root = tk.Tk()
    app = MultiLangQuizApp(root)
    root.mainloop()

import tkinter as tk
from tkinter import messagebox
import pandas as pd
import random
import sys

# ==========================
# LOAD DATA
# ==========================
import os
import sys

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Try to load from CSV first (recommended format), then Excel
CSV_FILE = get_resource_path("all_5000_characters.csv")
EXCEL_FILE = get_resource_path("5000-common-characters.xls")

vocab = []

# Try CSV format first (character, pinyin, definition)
try:
    if pd.io.common.file_exists(CSV_FILE):
        print(f"Loading vocabulary from {CSV_FILE}...")
        df = pd.read_csv(CSV_FILE, encoding='utf-8')
        
        # Expect columns: character, pinyin, definition
        for index, row in df.iterrows():
            if pd.notna(row['character']) and pd.notna(row['pinyin']) and pd.notna(row['definition']):
                char = str(row['character']).strip()
                pinyin = str(row['pinyin']).strip()
                definition = str(row['definition']).strip().strip('"')  # Remove quotes
                
                if char and pinyin and definition:
                    vocab.append({
                        "char": char,
                        "pinyin": pinyin,
                        "definition": definition
                    })
        
        print(f"Successfully loaded {len(vocab)} vocabulary entries from CSV")
        
except FileNotFoundError:
    print(f"{CSV_FILE} not found, trying Excel format...")
except Exception as e:
    print(f"Error loading CSV: {e}, trying Excel format...")

# If CSV didn't work or wasn't found, try Excel format
if len(vocab) == 0:
    try:
        print(f"Loading vocabulary from {EXCEL_FILE}...")
        # Read Excel file - assume 3 columns: Character, Pinyin, Definition
        raw = pd.read_excel(EXCEL_FILE, header=None)
        
        # Look for characters in column 1, starting from row 2 (skip headers)
        for index in range(2, len(raw)):
            row = raw.iloc[index]
            
            # Skip rows that don't have a character in first column
            if pd.notna(row.iloc[1]):  # Characters are in column 1 (0-indexed)
                char = str(row.iloc[1]).strip()
                
                # For now, just create placeholder pinyin and definitions
                # You would need to provide the actual pinyin and definitions
                if len(char) == 1 and char:  # Single Chinese character
                    vocab.append({
                        "char": char,
                        "pinyin": f"placeholder_pinyin_{len(vocab)+1}",
                        "definition": f"definition for {char}"
                    })
                    
                    # Limit to prevent too many entries
                    if len(vocab) >= 50:
                        break
        
        print(f"Loaded {len(vocab)} characters from Excel (with placeholder pinyin/definitions)")
        print("Note: For a proper quiz, please create a CSV file with character, pinyin, and definition columns")
        
    except FileNotFoundError:
        print(f"Error: Could not find {EXCEL_FILE}")
    except Exception as e:
        print(f"Error loading Excel data: {e}")

# Validate we have enough data
if len(vocab) < 4:
    print(f"Error: Need at least 4 vocabulary entries for the quiz, but only found {len(vocab)}")
    print("Please check your data file format.")
    print("Expected CSV format: character,pinyin,definition")
    sys.exit(1)

# =====================
# QUIZ STATE
# =====================
score = 0
total = 0
correct_answer = None
feedback_after_id = None  # For scheduling feedback removal
selected_button = None  # Track which button was clicked
next_button = None  # Next button for manual progression
current_mode = "multiple_choice"  # "multiple_choice" or "typing"
current_difficulty = "level1"  # "level1" through "level10"
mode_frame = None
quiz_frame = None
typing_frame = None
entry_widget = None
dont_know_button = None
current_character_data = None
typed_correctly = False

# =====================
# QUIZ FUNCTIONS
# =====================
def get_vocab_for_difficulty(difficulty):
    """Get vocabulary subset based on difficulty level"""
    if difficulty == "level1":
        return vocab[:500]  # Characters 1-500
    elif difficulty == "level2":
        return vocab[500:1000]  # Characters 501-1000
    elif difficulty == "level3":
        return vocab[1000:1500]  # Characters 1001-1500
    elif difficulty == "level4":
        return vocab[1500:2000]  # Characters 1501-2000
    elif difficulty == "level5":
        return vocab[2000:2500]  # Characters 2001-2500
    elif difficulty == "level6":
        return vocab[2500:3000]  # Characters 2501-3000
    elif difficulty == "level7":
        return vocab[3000:3500]  # Characters 3001-3500
    elif difficulty == "level8":
        return vocab[3500:4000]  # Characters 3501-4000
    elif difficulty == "level9":
        return vocab[4000:4500]  # Characters 4001-4500
    else:  # level10
        return vocab[4500:]  # Characters 4501+

def check_typing_input(event=None):
    """Check typing input in real-time"""
    global score, current_character_data, typed_correctly
    
    if not current_character_data:
        return
        
    user_input = entry_widget.get().strip().lower()
    correct_pinyin = remove_tone_marks(current_character_data['pinyin']).lower()
    
    if user_input == correct_pinyin and not typed_correctly:
        typed_correctly = True
        score += 1
        feedback_label_typing.config(text="✅ Correct!", fg="#4CAF50", font=("Arial", 16, "bold"))
        entry_widget.config(bg="#4CAF50", fg="white", state="disabled")
        dont_know_button.config(state="disabled")
        
        # Show the answer and next button
        show_typing_answer()
    elif user_input and not user_input.startswith(correct_pinyin[:len(user_input)]):
        # Wrong input - show red background
        entry_widget.config(bg="#ffeeee")
    else:
        # Correct partial input - show normal background
        entry_widget.config(bg="white")

def check_typing_answer():
    """Check the typed pinyin answer (for submit button if kept)"""
    global score, current_character_data, typed_correctly
    
    if typed_correctly:
        return  # Already answered correctly
    
    user_input = entry_widget.get().strip().lower()
    correct_pinyin = remove_tone_marks(current_character_data['pinyin']).lower()
    
    entry_widget.config(state="disabled")
    dont_know_button.config(state="disabled")
    
    if user_input == correct_pinyin:
        score += 1
        feedback_label.config(text="✅ Correct!", fg="#4CAF50", font=("Arial", 16, "bold"))
        entry_widget.config(bg="#4CAF50", fg="white")
    else:
        feedback_label.config(text="❌ Incorrect", fg="#f44336", font=("Arial", 16, "bold"))
        entry_widget.config(bg="#f44336", fg="white")
    
    # Show the correct answer and meaning
    show_typing_answer()

def show_typing_answer():
    """Show the correct pinyin and meaning"""
    global current_character_data
    
    if not current_character_data:
        return
        
    answer_text = f"Pinyin: {current_character_data['pinyin']}\nMeaning: {current_character_data['definition']}"
    
    # Create or update answer display
    if not hasattr(show_typing_answer, 'answer_label'):
        show_typing_answer.answer_label = tk.Label(
            typing_frame,
            text="",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#2c3e50",
            justify="center",
            wraplength=600
        )
        show_typing_answer.answer_label.grid(row=6, column=0, pady=10, sticky="ew")
    
    show_typing_answer.answer_label.config(text=answer_text)
    show_typing_answer.answer_label.grid(row=6, column=0, pady=10, sticky="ew")
    
    # Update score and show next button
    score_label_typing.config(text=f"Score: {score} / {total}")
    next_button.config(state="normal")
    # Place next button in typing frame
    next_button.place(in_=typing_frame, relx=0.5, rely=0.9, anchor="center")

def dont_know_clicked():
    """Handle 'I don't know' button click"""
    global current_character_data, typed_correctly
    
    typed_correctly = False  # Don't count as correct
    entry_widget.config(state="disabled", bg="#f0f0f0")
    dont_know_button.config(state="disabled")
    feedback_label_typing.config(text="No worries! Here's the answer:", fg="#666666", font=("Arial", 14, "bold"))
    
    show_typing_answer()

def go_back_to_mode_selection():
    """Return to mode selection screen"""
    global score, total
    
    # Reset scores
    score = 0
    total = 0
    
    # Hide current frames
    quiz_frame.pack_forget()
    typing_frame.pack_forget()
    difficulty_frame.pack_forget()
    next_button.place_forget()
    
    # Show mode selection
    mode_frame.pack(fill="both", expand=True)

def remove_tone_marks(pinyin_text):
    """Remove tone marks from pinyin"""
    tone_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v', 'ü': 'v'
    }
    
    result = pinyin_text
    for toned, plain in tone_map.items():
        result = result.replace(toned, plain)
    return result

def switch_mode(mode):
    """Switch between multiple choice and typing modes"""
    global current_mode
    current_mode = mode
    
    # Hide mode selection and show difficulty selection
    mode_frame.pack_forget()
    difficulty_frame.pack(fill="both", expand=True)

def select_difficulty(difficulty):
    """Select difficulty and start quiz"""
    global current_difficulty
    current_difficulty = difficulty
    
    # Hide difficulty selection
    difficulty_frame.pack_forget()
    
    # Show appropriate quiz interface
    if current_mode == "multiple_choice":
        quiz_frame.pack(fill="both", expand=True)
        feedback_label.config(text="Choose the correct pinyin and definition:", fg="#666666", font=("Arial", 12))
    else:
        typing_frame.pack(fill="both", expand=True)
        feedback_label.config(text="Type the pinyin (without tone marks):", fg="#666666", font=("Arial", 12))
    
    # Start first question
    new_question()

def new_typing_question():
    """Start a new typing question"""
    global current_character_data, total, typed_correctly
    
    total += 1
    typed_correctly = False
    available_vocab = get_vocab_for_difficulty(current_difficulty)
    current_character_data = random.choice(available_vocab)
    
    # Update character display
    if current_mode == "typing":
        char_label_typing.config(text=current_character_data["char"])
        score_label_typing.config(text=f"Score: {score} / {total - 1}")
        feedback_label_typing.config(text="Type the pinyin (without tone marks):", fg="#666666", font=("Arial", 12))
    else:
        char_label.config(text=current_character_data["char"])
        score_label.config(text=f"Score: {score} / {total - 1}")
        feedback_label.config(text="Type the pinyin (without tone marks):", fg="#666666", font=("Arial", 12))
    
    # Reset entry and buttons
    entry_widget.config(state="normal", bg="white", fg="black")
    entry_widget.delete(0, tk.END)
    dont_know_button.config(state="normal")
    
    # Hide answer if it exists
    if hasattr(show_typing_answer, 'answer_label'):
        show_typing_answer.answer_label.grid_remove()
    
    # Hide next button
    next_button.place_forget()
    
    # Focus on entry
    entry_widget.focus_set()
def next_question_after_feedback():
    """Called when Next button is clicked"""
    global feedback_after_id
    feedback_after_id = None
    
    # Hide Next button
    next_button.place_forget()
    
    if current_mode == "multiple_choice":
        # Reset button colors and feedback
        for button in buttons:
            button.config(bg="#f0f0f0", fg="black", font=("Arial", 11, "bold"))
        feedback_label.config(text="", fg="black")
        new_question()
    else:
        new_typing_question()

def new_question():
    global correct_answer, total, feedback_after_id
    
    # Cancel any pending feedback removal
    if feedback_after_id:
        root.after_cancel(feedback_after_id)
        feedback_after_id = None
    
    if current_mode == "typing":
        new_typing_question()
        return
    
    total += 1

    # Pick a random character for the question from current difficulty
    available_vocab = get_vocab_for_difficulty(current_difficulty)
    correct = random.choice(available_vocab)
    correct_answer = f"{correct['pinyin']} — {correct['definition']}"

    # Get 3 different wrong answers from same difficulty level
    available_wrong = [v for v in available_vocab if v != correct]
    if len(available_wrong) < 3:
        print("Error: Not enough vocabulary entries for multiple choice in this difficulty")
        return
        
    wrong_choices = random.sample(available_wrong, 3)

    # Create all 4 options
    options = [correct_answer] + [
        f"{w['pinyin']} — {w['definition']}"
        for w in wrong_choices
    ]

    # Randomize order
    random.shuffle(options)

    # Update UI
    char_label.config(text=correct["char"])
    score_label.config(text=f"Score: {score} / {total - 1}")
    feedback_label.config(text="Choose the correct pinyin and definition:", fg="#666666", font=("Arial", 12))

    # Set up buttons with proper command binding, reset colors, and bold font
    for i in range(4):
        buttons[i].config(
            text=options[i],
            command=lambda choice=options[i], btn=buttons[i]: check_answer(choice, btn),
            state="normal",
            bg="#f0f0f0",
            fg="black",
            font=("Arial", 11, "bold"),
            relief="raised"
        )
    
    # Hide Next button during question
    next_button.place_forget()

def check_answer(choice, button_clicked):
    global score, feedback_after_id, selected_button
    selected_button = button_clicked

    # Disable all buttons and make text bold
    for button in buttons:
        button.config(state="disabled", font=("Arial", 11, "bold"))

    if choice == correct_answer:
        score += 1
        # Show correct feedback
        button_clicked.config(bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))  # Bold text
        feedback_label.config(text="✅ Correct! Well done!", fg="#4CAF50", font=("Arial", 16, "bold"))
    else:
        # Show incorrect feedback
        button_clicked.config(bg="#f44336", fg="white", font=("Arial", 11, "bold"))  # Bold text
        feedback_label.config(text="❌ Incorrect", fg="#f44336", font=("Arial", 16, "bold"))
        
        # Highlight the correct answer in green with bold text
        for button in buttons:
            if button.cget("text") == correct_answer:
                button.config(bg="#4CAF50", fg="white", font=("Arial", 11, "bold"))

    # Update score display
    score_label.config(text=f"Score: {score} / {total}")
    
    # Show Next button for manual progression
    next_button.config(state="normal")
    # Place next button in top right of quiz frame
    next_button.place(in_=quiz_frame, relx=0.95, rely=0.05, anchor="ne")

# =====================
# UI SETUP - Dynamic and Responsive with Mode Selection
# =====================
root = tk.Tk()
root.title("Chinese Character Quiz")
root.geometry("800x700")
root.minsize(600, 500)

# Configure root grid to be responsive
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Trigger initial resize to set proper font sizes
root.update_idletasks()

# Mode Selection Frame
mode_frame = tk.Frame(root, bg="white", padx=40, pady=40)
mode_frame.pack(fill="both", expand=True)

tk.Label(
    mode_frame,
    text="Chinese Character Quiz",
    font=("Arial", 28, "bold"),
    bg="white",
    fg="#2c3e50"
).pack(pady=(0, 30))

tk.Label(
    mode_frame,
    text="Choose your quiz mode:",
    font=("Arial", 16),
    bg="white",
    fg="#666666"
).pack(pady=(0, 20))

# Mode selection buttons
mc_button = tk.Button(
    mode_frame,
    text="📝 Multiple Choice\n\nSee the character and choose from 4 options",
    font=("Arial", 14, "bold"),
    bg="#3498db",
    fg="white",
    relief="raised",
    bd=3,
    padx=20,
    pady=20,
    command=lambda: switch_mode("multiple_choice")
)
mc_button.pack(pady=10, fill="x", ipady=10)

typing_button = tk.Button(
    mode_frame,
    text="⌨️ Typing Mode\n\nType the pinyin pronunciation (no tone marks)",
    font=("Arial", 14, "bold"),
    bg="#27ae60",
    fg="white",
    relief="raised",
    bd=3,
    padx=20,
    pady=20,
    command=lambda: switch_mode("typing")
)
typing_button.pack(pady=10, fill="x", ipady=10)

# Difficulty Selection Frame
difficulty_frame = tk.Frame(root, bg="white", padx=40, pady=40)

tk.Label(
    difficulty_frame,
    text="Choose Difficulty Level",
    font=("Arial", 28, "bold"),
    bg="white",
    fg="#2c3e50"
).pack(pady=(0, 20))

tk.Label(
    difficulty_frame,
    text="Choose your level (most common → least common, 500 characters per level):",
    font=("Arial", 14),
    bg="white",
    fg="#666666"
).pack(pady=(0, 20))

# Create a frame for two columns of difficulty buttons
difficulty_buttons_frame = tk.Frame(difficulty_frame, bg="white")
difficulty_buttons_frame.pack(fill="x", pady=10)
difficulty_buttons_frame.columnconfigure(0, weight=1)
difficulty_buttons_frame.columnconfigure(1, weight=1)

# Define difficulty levels with colors and emojis
levels = [
    ("level1", "🟢 Level 1", "Characters 1-500", "#27ae60"),
    ("level2", "🟡 Level 2", "Characters 501-1000", "#f1c40f"), 
    ("level3", "🟠 Level 3", "Characters 1001-1500", "#f39c12"),
    ("level4", "🔴 Level 4", "Characters 1501-2000", "#e74c3c"),
    ("level5", "🟣 Level 5", "Characters 2001-2500", "#9b59b6"),
    ("level6", "⚫ Level 6", "Characters 2501-3000", "#34495e"),
    ("level7", "🟤 Level 7", "Characters 3001-3500", "#8d4925"),
    ("level8", "🔵 Level 8", "Characters 3501-4000", "#3498db"),
    ("level9", "🔶 Level 9", "Characters 4001-4500", "#e67e22"),
    ("level10", "💎 Level 10", "Characters 4501-4771", "#2c3e50")
]

# Create buttons for each level
for i, (level_id, title, subtitle, color) in enumerate(levels):
    row = i // 2
    col = i % 2
    
    button = tk.Button(
        difficulty_buttons_frame,
        text=f"{title}\n{subtitle}",
        font=("Arial", 10, "bold"),
        bg=color,
        fg="white",
        relief="raised",
        bd=3,
        padx=15,
        pady=8,
        command=lambda l=level_id: select_difficulty(l)
    )
    button.grid(row=row, column=col, pady=3, padx=5, sticky="ew")

# Back button for difficulty selection
back_button_difficulty = tk.Button(
    difficulty_frame,
    text="← Back to Mode Selection",
    font=("Arial", 10, "bold"),
    bg="#95a5a6",
    fg="white",
    relief="raised",
    bd=2,
    padx=15,
    pady=5,
    command=go_back_to_mode_selection
)
back_button_difficulty.pack(pady=20)

# Multiple Choice Quiz Frame
quiz_frame = tk.Frame(root, bg="white", padx=20, pady=20)
quiz_frame.columnconfigure(0, weight=1)

# Common elements (character, score, feedback)
char_label = tk.Label(
    quiz_frame, 
    text="字", 
    font=("Arial", 80), 
    bg="white",
    fg="#34495e"
)

score_label = tk.Label(
    quiz_frame, 
    text="Score: 0 / 0", 
    font=("Arial", 16),
    bg="white",
    fg="#7f8c8d"
)

feedback_label = tk.Label(
    quiz_frame,
    text="",
    font=("Arial", 12),
    bg="white",
    fg="#666666",
    wraplength=600
)

# Buttons frame for multiple choice
buttons_frame = tk.Frame(quiz_frame, bg="white")
buttons_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
buttons_frame.columnconfigure(0, weight=1)

# Create answer buttons with better styling and bold fonts
buttons = []
for i in range(4):
    btn = tk.Button(
        buttons_frame,
        text="",
        font=("Arial", 11, "bold"),  # Bold font for better readability
        wraplength=700,
        height=3,
        bg="#f0f0f0",
        fg="black",
        relief="raised",
        bd=2,
        padx=15,
        pady=10,
        activebackground="#e0e0e0"
    )
    btn.grid(row=i, column=0, pady=5, padx=10, sticky="ew")
    buttons.append(btn)

# Typing Mode Frame
typing_frame = tk.Frame(root, bg="white", padx=20, pady=20)
typing_frame.columnconfigure(0, weight=1)

# Character label for typing mode (reuse)
char_label_typing = tk.Label(
    typing_frame, 
    text="字", 
    font=("Arial", 80), 
    bg="white",
    fg="#34495e"
)
char_label_typing.grid(row=0, column=0, pady=20, sticky="ew")

# Score label for typing mode (reuse)
score_label_typing = tk.Label(
    typing_frame, 
    text="Score: 0 / 0", 
    font=("Arial", 16),
    bg="white",
    fg="#7f8c8d"
)
score_label_typing.grid(row=1, column=0, pady=(0, 10), sticky="ew")

# Feedback label for typing mode
feedback_label_typing = tk.Label(
    typing_frame,
    text="",
    font=("Arial", 12),
    bg="white",
    fg="#666666",
    wraplength=600
)
feedback_label_typing.grid(row=2, column=0, pady=(0, 20), sticky="ew")

# Entry widget for typing pinyin
entry_widget = tk.Entry(
    typing_frame,
    font=("Arial", 18, "bold"),
    justify="center",
    relief="solid",
    bd=2,
    width=20
)
entry_widget.grid(row=3, column=0, pady=20, ipady=10)

# I don't know button frame
typing_buttons_frame = tk.Frame(typing_frame, bg="white")
typing_buttons_frame.grid(row=4, column=0, pady=10)

dont_know_button = tk.Button(
    typing_buttons_frame,
    text="❓ I don't know",
    font=("Arial", 12, "bold"),
    bg="#e74c3c",
    fg="white",
    relief="raised",
    bd=2,
    padx=20,
    pady=5,
    command=dont_know_clicked
)
dont_know_button.pack()

# Back button for typing mode
back_button_typing = tk.Button(
    typing_frame,
    text="← Back to Menu",
    font=("Arial", 10, "bold"),
    bg="#95a5a6",
    fg="white",
    relief="raised",
    bd=2,
    padx=15,
    pady=5,
    command=go_back_to_mode_selection
)
back_button_typing.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

# Bind real-time input checking
def on_typing_input(event):
    check_typing_input()

entry_widget.bind("<KeyRelease>", on_typing_input)

# Next button (shared between modes)
next_button = tk.Button(
    root,  # Will be reparented as needed
    text="Next Question →",
    font=("Arial", 14, "bold"),
    bg="#3498db",
    fg="white",
    relief="raised",
    bd=2,
    padx=20,
    pady=10,
    command=next_question_after_feedback,
    state="disabled"
)

# Configure frames to be responsive
for i in range(4):
    buttons_frame.rowconfigure(i, weight=1)

# Back button for multiple choice mode
back_button_quiz = tk.Button(
    quiz_frame,
    text="← Back to Menu",
    font=("Arial", 10, "bold"),
    bg="#95a5a6",
    fg="white",
    relief="raised",
    bd=2,
    padx=15,
    pady=5,
    command=go_back_to_mode_selection
)
back_button_quiz.grid(row=0, column=0, sticky="nw", padx=10, pady=10)

# Adjust other elements to accommodate back button
char_label.grid(row=1, column=0, pady=20, sticky="ew")
score_label.grid(row=2, column=0, pady=(0, 10), sticky="ew")
feedback_label.grid(row=3, column=0, pady=(0, 20), sticky="ew")
buttons_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))

# Bind window resize event to adjust font sizes
def on_window_resize(event):
    # Only resize for the root window, not child widgets
    if event.widget == root:
        width = root.winfo_width()
        height = root.winfo_height()
        
        # Adjust character font size based on window size
        char_size = max(40, min(120, width // 10))
        char_label.config(font=("Arial", char_size))
        char_label_typing.config(font=("Arial", char_size))
        
        # Adjust button font size (bold)
        button_font_size = max(9, min(14, width // 60))
        for button in buttons:
            button.config(font=("Arial", button_font_size, "bold"))
            
        # Adjust Next button font size
        next_font_size = max(12, min(16, width // 50))
        next_button.config(font=("Arial", next_font_size, "bold"))
        
        # Adjust entry widget font
        entry_font_size = max(14, min(20, width // 45))
        entry_widget.config(font=("Arial", entry_font_size, "bold"))

root.bind("<Configure>", on_window_resize)

# Trigger initial resize after UI is built
def setup_dynamic_sizing():
    """Set up proper font sizes on startup"""
    root.update_idletasks()
    width = root.winfo_width()
    
    # Set initial font sizes
    char_size = max(40, min(120, width // 10))
    button_font_size = max(9, min(14, width // 60))
    next_font_size = max(12, min(16, width // 50))
    entry_font_size = max(14, min(20, width // 45))
    
    char_label.config(font=("Arial", char_size))
    
    for button in buttons:
        button.config(font=("Arial", button_font_size, "bold"))
    
    next_button.config(font=("Arial", next_font_size, "bold"))
    entry_widget.config(font=("Arial", entry_font_size, "bold"))

# Set up dynamic sizing after UI is built
root.after(100, setup_dynamic_sizing)

# Start with mode selection - quiz will start after mode is chosen
if len(vocab) >= 4:
    root.mainloop()
else:
    print("Cannot start quiz - insufficient vocabulary data")

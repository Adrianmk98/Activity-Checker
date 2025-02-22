import praw
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime
import time
import threading

# Set up Reddit API connection
reddit = praw.Reddit(
    client_id='X',
    client_secret='X',
    user_agent='X'
)

# List of specific flairs to check in cmhocpress
TARGET_FLAIRS = [
    "⚔️ Question Period",
    "2nd Reading",
    "Committee of the Whole",
    "Motion Debate",
    "Report Stage",
    "3rd Reading",
    "Take-Note Debate",
    "Motion Amendments"
]

# Global dictionary to hold user comment details
user_comment_details = {}


# Function to read usernames from names.txt and filter out "Vacant"
def load_usernames():
    try:
        with open('names.txt', 'r') as file:
            usernames = [line.strip() for line in file if line.strip().lower() != "vacant"]
        print(f"Usernames loaded: {usernames}")
        return usernames
    except FileNotFoundError:
        result_textbox.insert(tk.END, "Error: 'names.txt' file not found.\n", 'red')
        return []


# Function to check if a user has commented in the specific subreddits during the time period
# and if the post the comment was made on has one of the specified flairs for cmhocpress
def check_comments():
    subreddit1 = "cmhoc"
    subreddit2 = "cmhochouse"

    result_textbox.delete(0, tk.END)  # Clear previous results
    details_textbox.delete(1.0, tk.END)  # Clear previous details
    result_textbox.insert(tk.END, "Checking comments, please wait...\n")

    try:
        start_time = time.mktime(calendar_start.get_date().timetuple())
        end_time = time.mktime(calendar_end.get_date().timetuple())

        usernames = load_usernames()
        if not usernames:
            return  # Exit if no usernames loaded

        for username in usernames:
            try:
                user = reddit.redditor(username)
                comments = user.comments.new(limit=None)

                found_in_subreddits = {
                    subreddit1: False,
                    subreddit2: False
                }

                # Collect details for display in second textbox
                user_comment_details[username] = []

                for comment in comments:
                    if comment.subreddit.display_name in [subreddit1, subreddit2]:
                        if start_time <= comment.created_utc <= end_time:
                            # Build comment detail string
                            comment_time = datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S')
                            comment_link = f"https://www.reddit.com{comment.permalink}"
                            comment_detail = f"Subreddit: {comment.subreddit.display_name}, Time: {comment_time}\nLink: {comment_link}\n"

                            if comment.subreddit.display_name == subreddit1:
                                # Check flair only for cmhocpress
                                flair = comment.submission.link_flair_text
                                if flair in TARGET_FLAIRS:
                                    found_in_subreddits[subreddit1] = True
                                    comment_detail += f"Flair: {flair}\n"
                                    user_comment_details[username].append(comment_detail)
                            elif comment.subreddit.display_name == subreddit2:
                                # Accept all comments from cmhochouse
                                found_in_subreddits[subreddit2] = True
                                user_comment_details[username].append(comment_detail)

                # Color-coding based on whether comments were found
                if found_in_subreddits[subreddit1] or found_in_subreddits[subreddit2]:
                    result_textbox.insert(tk.END, f"{username} - Comments found\n")
                    result_textbox.itemconfig(tk.END, {'fg': 'green'})
                else:
                    result_textbox.insert(tk.END, f"{username} - No comments\n")
                    result_textbox.itemconfig(tk.END, {'fg': 'red'})

            except Exception as e:
                result_textbox.insert(tk.END, f"{username} - Error: {e}\n")
                result_textbox.itemconfig(tk.END, {'fg': 'red'})

    except Exception as e:
        result_textbox.insert(tk.END, f"Error during comment checking: {e}\n")
        result_textbox.itemconfig(tk.END, {'fg': 'red'})

    result_textbox.insert(tk.END, "Check complete.\n")


# Function to run the check_comments in a separate thread
def run_check_comments():
    thread = threading.Thread(target=check_comments)
    thread.start()


# Function to display details of the selected user in the second text box
def display_user_details(event):
    selected_index = result_textbox.curselection()
    if selected_index:
        selected_username = result_textbox.get(selected_index[0]).split(" - ")[0]
        details_textbox.delete(1.0, tk.END)  # Clear previous details

        if selected_username in user_comment_details:
            details_textbox.insert(tk.END, f"Details for {selected_username}:\n\n")
            for detail in user_comment_details[selected_username]:
                details_textbox.insert(tk.END, detail + "\n")


# GUI setup
root = tk.Tk()
root.title("")

# Date input
tk.Label(root, text="Start Date:").grid(row=0, column=0, padx=10, pady=5)
calendar_start = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
calendar_start.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="End Date:").grid(row=1, column=0, padx=10, pady=5)
calendar_end = DateEntry(root, width=12, background='darkblue', foreground='white', borderwidth=2)
calendar_end.grid(row=1, column=1, padx=10, pady=5)

# Check button
check_button = ttk.Button(root, text="Check Comments", command=run_check_comments)
check_button.grid(row=2, column=0, columnspan=2, pady=10)

# Result display using Listbox for clickable usernames
result_textbox = tk.Listbox(root, width=50, height=15)
result_textbox.grid(row=3, column=0, columnspan=2, pady=10)
result_textbox.bind('<<ListboxSelect>>', display_user_details)  # Bind click event

# Detailed comment display in second Text widget
details_textbox = tk.Text(root, width=60, height=15)
details_textbox.grid(row=4, column=0, columnspan=2, pady=10)

# Start the GUI loop
root.mainloop()

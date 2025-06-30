import os
import pickle
import sys
import time
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
CLIENT_SECRETS_FILE = "client_secret.json"
CREDENTIALS_PICKLE_FILE = "token.pickle"

SPINNER = ['-', '\\', '|', '/']

def spinner_loading():
    percent = 0
    spinner_index = 0
    while percent <= 100:
        spinner_char = SPINNER[spinner_index % len(SPINNER)]
        sys.stdout.write(f"\rLoading {spinner_char} {percent}%")
        sys.stdout.flush()
        time.sleep(0.08)  # frame every 0.08s for smooth spinner
        spinner_index += 1
        if spinner_index % 10 == 0:  # every 0.8 seconds (10*0.08)
            percent += 6
    sys.stdout.write("\rLoading complete!     \n")
    sys.stdout.flush()

def show_title():
    print("\nLGM's YT Replier")
    time.sleep(1.6)  # changed per your edit
    print("\nWelcome!\n")

def get_authenticated_service():
    creds = None
    if os.path.exists(CREDENTIALS_PICKLE_FILE):
        with open(CREDENTIALS_PICKLE_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(CREDENTIALS_PICKLE_FILE, "wb") as token:
            pickle.dump(creds, token)
    return build("youtube", "v3", credentials=creds)

def get_my_channel_id(youtube):
    response = youtube.channels().list(
        part="id",
        mine=True
    ).execute()
    items = response.get("items", [])
    if not items:
        raise Exception("Could not retrieve your channel ID.")
    return items[0]["id"]

def get_all_comments(youtube, video_id):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )
    while request:
        response = request.execute()
        for item in response["items"]:
            comment = item["snippet"]["topLevelComment"]
            published_at = comment["snippet"]["publishedAt"]
            published_dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            published_str = published_dt.strftime("%Y-%m-%d %H:%M:%S UTC")

            comments.append({
                "id": comment["id"],
                "text": comment["snippet"]["textDisplay"],
                "published_at": published_str
            })
        request = youtube.commentThreads().list_next(request, response)
    return comments

def get_replies_for_comment(youtube, parent_comment_id):
    replies = []
    request = youtube.comments().list(
        part="snippet",
        parentId=parent_comment_id,
        maxResults=100,
        textFormat="plainText"
    )
    while request:
        response = request.execute()
        for item in response.get("items", []):
            replies.append(item)
        request = youtube.comments().list_next(request, response)
    return replies

def has_replied(youtube, your_channel_id, comment_id):
    replies = get_replies_for_comment(youtube, comment_id)
    for reply in replies:
        author_channel_id = reply["snippet"]["authorChannelId"]["value"]
        if author_channel_id == your_channel_id:
            return True
    return False

def reply_to_comment(youtube, comment_id, text):
    response = youtube.comments().insert(
        part="snippet",
        body={
            "snippet": {
                "parentId": comment_id,
                "textOriginal": text
            }
        }
    ).execute()
    return response

def add_phrases(phrases):
    print("\nAdd up to 5 reply phrases.")
    for i in range(5):
        current = phrases.get(i+1, None)
        if current:
            print(f"Phrase {i+1}: {current}")
        else:
            print(f"Phrase {i+1}: [None]")
    print("Enter the phrase number (1-5) to add/change, or 0 to return to menu.")
    while True:
        choice = input("Choose phrase number to edit (0 to exit): ").strip()
        if choice == '0':
            break
        if choice not in ['1','2','3','4','5']:
            print("Invalid choice, enter a number 1-5 or 0 to exit.")
            continue
        idx = int(choice)
        new_phrase = input(f"Enter new phrase for phrase {idx}: ").strip()
        if new_phrase == '':
            print("Empty phrase ignored.")
        else:
            phrases[idx] = new_phrase
            print(f"Phrase {idx} updated.")
    return phrases

def choose_phrase(phrases):
    print("Which phrase? (1-5)")
    for i in range(1,6):
        phrase = phrases.get(i)
        if phrase:
            print(f"{i}: {phrase}")
        else:
            print(f"{i}: No phrase added (will use default)")
    while True:
        choice = input("Enter phrase number (1-5): ").strip()
        if choice in ['1','2','3','4','5']:
            idx = int(choice)
            phrase = phrases.get(idx)
            if phrase:
                return phrase
            else:
                return "Thanks for your comment!"
        else:
            print("Invalid choice. Enter a number 1-5.")

def start_replier(phrases, your_channel_id):
    video_id = input("Enter the YouTube video ID: ").strip()
    youtube = get_authenticated_service()

    comments = get_all_comments(youtube, video_id)
    if not comments:
        print("No comments found.")
        return

    for comment in comments:
        print(f"\nComment posted on: {comment['published_at']}")
        print("Comment text:\n" + comment["text"])
        if has_replied(youtube, your_channel_id, comment["id"]):
            print("Already replied by the bot or manually! Skipping to next comment..")
            continue

        while True:
            reply = input("Reply to comment? Y/N (or 0 to exit): ").strip().lower()
            if reply == "0":
                print("Exiting reply loop and returning to main menu.")
                return
            elif reply in ["y", "n"]:
                break
            else:
                print("Invalid input. Please enter Y, N, or 0.")

        if reply == "y":
            reply_text = choose_phrase(phrases)
            reply_to_comment(youtube, comment["id"], reply_text)
            print(f"Replied to comment ID {comment['id']} on video https://youtu.be/{video_id}")
        else:
            print("Skipped replying.")

def main():
    spinner_loading()
    show_title()

    phrases = {}

    youtube = get_authenticated_service()
    your_channel_id = get_my_channel_id(youtube)
    print(f"Authenticated as channel ID: {your_channel_id}")

    while True:
        print("\nMain Menu:")
        print("1 - Start Replier")
        print("2 - Add Phrases")
        print("0 - Exit")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            start_replier(phrases, your_channel_id)
        elif choice == "2":
            phrases = add_phrases(phrases)
        elif choice == "0":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option. Please select 0, 1, or 2.")

if __name__ == "__main__":
    main()


import os
from datetime import datetime
import pandas as pd
import requests

# ==========================================
# 1. YOUTUBE API CONFIGURATION
# ==========================================

API_KEY = os.getenv("YOUTUBE_API_KEY")

if not API_KEY:
    raise ValueError(
        "YouTube API key not found! "
        "Set YOUTUBE_API_KEY environment variable."
    )

CHANNEL_IDS = [
    "UCq-Fj5jknLsUf-MWSy4_brA",
    "UC6-F5tO8uklgE9Zy8IvbdFw",
    "UCmqfX0S3x0I3uwLkPdpX03w",
    "UCqwUrj10mAEsqezcItqvwEw",
    "UC7eHZXheF8nVOfwB2PEslMw",
    "UCyoXW-Dse7fURq30EWl_CUA",
    "UCOhHO2ICt0ti9KAh-QHvttQ",
    "UCaayLD9i5x4MmIoVZxXSv_g",
    "UCpEhnqL0y41EpW2TvWAHD7Q",
    "UCFFbwnve3yF62-tVXkTyHqg"
]

# ==========================================
# 2. FILE PATHS
# ==========================================

folder = os.path.dirname(os.path.abspath(__file__))

current_file = os.path.join(
    folder, "Current_Data.csv"
)

latest_file = os.path.join(
    folder, "latest youtube.csv"
)

history_file = os.path.join(
    folder, "History_Data.csv"
)

old_file = os.path.join(
    folder, "youtube_metrics_tracker.csv"
)

# ==========================================
# 3. TIMESTAMP
# ==========================================

now = datetime.now()

timestamp = now.strftime("%d-%m-%Y %H:%M:%S")

data = []

# ==========================================
# 4. FETCH LATEST YOUTUBE DATA
# ==========================================

print("Fetching YouTube channel data...")

url = "https://www.googleapis.com/youtube/v3/channels"

for channel_id in CHANNEL_IDS:

    params = {
        "part": "snippet,statistics",
        "id": channel_id,
        "key": API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        items = response.json().get("items", [])

        if items:

            snippet = items[0]["snippet"]
            stats = items[0]["statistics"]

            data.append({

                "Timestamp": timestamp,

                "ChannelName": snippet.get("title"),

                "ChannelID": channel_id,

                "Subscribers": int(
                    stats.get("subscriberCount", 0)
                ),

                "TotalViews": int(
                    stats.get("viewCount", 0)
                ),

                "TotalVideos": int(
                    stats.get("videoCount", 0)
                )

            })

            print("Fetched:", snippet.get("title"))

        else:

            print("Channel not found:", channel_id)

    except requests.RequestException as e:

        print(
            "Error fetching",
            channel_id,
            ":",
            e
        )

        if getattr(e, "response", None) is not None:
            try:
                print("API details:", e.response.text)
            except Exception:
                pass

# ==========================================
# 5. CREATE DATAFRAME
# ==========================================

df_new = pd.DataFrame(data)

# ==========================================
# 6. SAVE CURRENT DATA AND POWER BI DATA
# ==========================================

if not df_new.empty:

    # Remove duplicate channels in current fetch
    df_new = df_new.drop_duplicates(
        subset=["ChannelID"],
        keep="last"
    )

    # Save current data
    df_new.to_csv(
        current_file,
        index=False
    )

    print("\nCurrent_Data.csv updated!")

    # Save Power BI source data
    df_new.to_csv(
        latest_file,
        index=False
    )

    print("latest youtube.csv updated!")

    # ==========================================
    # 7. LOAD EXISTING HISTORY DATA
    # ==========================================

    if os.path.exists(history_file):

        df_history = pd.read_csv(history_file)

        print("Existing history file loaded.")

    elif os.path.exists(old_file):

        # One-time import of old historical data
        df_history = pd.read_csv(old_file)

        print("Old history file imported.")

    else:

        df_history = pd.DataFrame(
            columns=df_new.columns
        )

        print("New history file created.")

    # ==========================================
    # 8. COMBINE HISTORY AND NEW DATA
    # ==========================================

    df_combined = pd.concat(
        [df_history, df_new],
        ignore_index=True
    )

    # ==========================================
    # 9. REMOVE DUPLICATES
    # ==========================================

    if not df_combined.empty:

        # Convert Timestamp into datetime
        df_combined["ParsedDate"] = pd.to_datetime(
            df_combined["Timestamp"],
            errors="coerce",
            dayfirst=True
        )

        # Remove invalid timestamps
        df_combined = df_combined.dropna(
            subset=["ParsedDate"]
        )

        # Extract date only
        df_combined["DateKey"] = (
            df_combined["ParsedDate"]
            .dt.strftime("%Y-%m-%d")
        )

        # One record per ChannelID per day
        # Keep latest fetched record
        df_combined = df_combined.drop_duplicates(
            subset=["ChannelID", "DateKey"],
            keep="last"
        )

        # Sort history by date
        df_combined = df_combined.sort_values(
            by=["ParsedDate", "ChannelName"]
        )

        # Remove temporary columns
        df_combined = df_combined.drop(
            columns=["ParsedDate", "DateKey"]
        )

    # ==========================================
    # 10. SAVE HISTORY DATA
    # ==========================================

    df_combined.to_csv(
        history_file,
        index=False
    )

    print("\nHistory_Data.csv updated successfully!")

    print("--------------------------------")

    print("Channels fetched:", len(df_new))

    print("History total records:", len(df_combined))

    print("Duplicate records avoided!")

    print("--------------------------------")

    print("Current file:", current_file)

    print("Power BI file:", latest_file)

    print("History file:", history_file)

else:

    print("\nNo data fetched.")

    print("CSV files were not changed.")

# ==========================================
# 11. COMPLETION
# ==========================================

print("\nYouTube data extraction process completed!")

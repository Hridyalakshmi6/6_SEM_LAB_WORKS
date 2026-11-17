
"""
Experiment: Fetching Social Media Data using an API
Platform: YouTube
API: YouTube Data API v3
"""

import os
import requests
import pandas as pd

from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

LIMIT = 10


# Step 1: Fetch videos from YouTube
def fetch_videos(keyword):

    search_params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": LIMIT,
        "order": "relevance",
        "key": API_KEY
    }

    response = requests.get(
        SEARCH_URL,
        params=search_params,
        timeout=30
    )

    response.raise_for_status()

    search_data = response.json()

    video_ids = [
        item["id"]["videoId"]
        for item in search_data.get("items", [])
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return []

    # Step 2: Fetch video statistics
    video_params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }

    response = requests.get(
        VIDEOS_URL,
        params=video_params,
        timeout=30
    )

    response.raise_for_status()

    return response.json().get("items", [])


# Step 3: Structure the retrieved data
def structure_data(videos):

    records = []

    for video in videos:

        snippet = video.get("snippet", {})
        stats = video.get("statistics", {})

        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))

        engagement = likes + comments

        engagement_rate = (
            (engagement / views) * 100 if views > 0 else 0
        )

        records.append({

            "Video ID": video.get("id", ""),
            "Title": snippet.get("title", ""),
            "Description": snippet.get("description", ""),
            "Channel": snippet.get("channelTitle", ""),
            "Published Date": snippet.get("publishedAt", ""),
            "Views": views,
            "Likes": likes,
            "Comments": comments,
            "Total Engagement": engagement,
            "Engagement Rate (%)": round(engagement_rate, 2)

        })

    return pd.DataFrame(records)


# Step 4: Store data in CSV and JSON
def store_data(df):

    os.makedirs("output", exist_ok=True)

    df.to_csv(
        "output/youtube_data.csv",
        index=False,
        encoding="utf-8-sig"
    )

    df.to_json(
        "output/youtube_data.json",
        orient="records",
        indent=4,
        force_ascii=False
    )

    print("\nData successfully stored!")
    print("CSV  : output/youtube_data.csv")
    print("JSON : output/youtube_data.json")


# Step 5: Display retrieved posts
def display_data(df):

    print("\n" + "=" * 75)
    print("             YOUTUBE SOCIAL MEDIA DATA")
    print("=" * 75)

    for index, row in df.iterrows():

        print(f"\nPost {index + 1}")
        print("-" * 65)

        print("Title       :", row["Title"])
        print("Channel     :", row["Channel"])
        print("Published   :", row["Published Date"])

        print("Description :",
              row["Description"][:200].replace("\n", " "))

        print("\nEngagement Metrics:")
        print("Views       :", row["Views"])
        print("Likes       :", row["Likes"])
        print("Comments    :", row["Comments"])

        print("Total Engagement:", row["Total Engagement"])
        print("Engagement Rate  :",
              str(row["Engagement Rate (%)"]) + "%")

    # Engagement summary
    print("\n" + "=" * 75)
    print("                  ENGAGEMENT SUMMARY")
    print("=" * 75)

    print("Videos fetched :", len(df))
    print("Total views    :", df["Views"].sum())
    print("Total likes    :", df["Likes"].sum())
    print("Total comments :", df["Comments"].sum())

    print("Average engagement :",
          round(df["Total Engagement"].mean(), 2))

    top = df.loc[df["Total Engagement"].idxmax()]

    print("\nMost engaging video:")
    print("Title :", top["Title"])
    print("Channel:", top["Channel"])
    print("Interactions:", top["Total Engagement"])

    print("\n" + "=" * 75)


# Main function
def main():

    if not API_KEY:
        print("Error: YouTube API key not found in .env file.")
        return

    keyword = input(
        "Enter a keyword to search on YouTube: "
    ).strip()

    if not keyword:
        print("Please enter a valid keyword.")
        return

    print("\nFetching YouTube data...")

    try:

        videos = fetch_videos(keyword)

        if not videos:
            print("No videos found for this keyword.")
            return

        df = structure_data(videos)

        store_data(df)

        display_data(df)

        print("\nStructured Data (DataFrame):")

        print(
            df[[
                "Title",
                "Views",
                "Likes",
                "Comments",
                "Total Engagement"
            ]].to_string(index=False)
        )

    except requests.exceptions.HTTPError as error:

        print("\nHTTP Error:", error)

        try:
            print(error.response.json())
        except ValueError:
            pass

    except requests.exceptions.RequestException as error:

        print("\nAPI connection error:", error)

    except (ValueError, KeyError) as error:

        print("\nData processing error:", error)


if __name__ == "__main__":
    main()

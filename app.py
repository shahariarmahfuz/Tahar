import os
import json
import hashlib
import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

# ভিডিও সংরক্ষণের ফোল্ডার
VIDEO_FOLDER = "videos"
os.makedirs(VIDEO_FOLDER, exist_ok=True)

# ভিডিও ডাউনলোড চেক করার JSON ফাইল
CHECK_FILE = "check.json"
if not os.path.exists(CHECK_FILE):
    with open(CHECK_FILE, "w") as f:
        json.dump({}, f)

# RapidAPI তথ্য
RAPIDAPI_HOST = "facebook-reel-and-video-downloader.p.rapidapi.com"
RAPIDAPI_KEY = "আপনার-র্যাপিডএপিআই-কী"


def read_json():
    """check.json ফাইল থেকে ডাটা পড়া"""
    with open(CHECK_FILE, "r") as f:
        return json.load(f)


def write_json(data):
    """check.json ফাইলে নতুন ডাটা লেখা"""
    with open(CHECK_FILE, "w") as f:
        json.dump(data, f, indent=4)


def check_video_exists(fb_url):
    """ভিডিও আগেই ডাউনলোড করা হয়েছে কিনা তা চেক করা"""
    data = read_json()
    return data.get(fb_url)


def save_video_info(fb_url, video_path):
    """ভিডিও ডাউনলোড হলে সেটির তথ্য check.json ফাইলে সংরক্ষণ করা"""
    data = read_json()
    data[fb_url] = video_path
    write_json(data)


def fetch_hd_video_url(fb_url):
    """RapidAPI থেকে HD ভিডিও URL বের করা"""
    url = f"https://{RAPIDAPI_HOST}/app/main.php?url={fb_url}"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        hd_url = data.get("links", {}).get("Download High Quality")  # শুধুমাত্র HD URL নেওয়া
        return hd_url
    return None


def download_video(fb_url, hd_url):
    """HD ভিডিও ডাউনলোড করে সংরক্ষণ করা"""
    if not hd_url:
        return None

    file_hash = hashlib.md5(fb_url.encode()).hexdigest()  # লিংক থেকে ইউনিক নাম তৈরি করা
    video_path = os.path.join(VIDEO_FOLDER, f"{file_hash}.mp4")

    video_response = requests.get(hd_url, stream=True)
    with open(video_path, "wb") as f:
        for chunk in video_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    save_video_info(fb_url, video_path)
    return video_path


@app.route("/link", methods=["GET"])
def get_video():
    """ফেসবুক ভিডিও ডাউনলোড করে এবং ইউজারকে ভিডিওতে রিডাইরেক্ট করে।"""
    fb_url = request.args.get("url")
    if not fb_url:
        return jsonify({"error": "URL is required"}), 400

    # আগের ডাউনলোড চেক করা
    video_path = check_video_exists(fb_url)
    if not video_path:
        hd_url = fetch_hd_video_url(fb_url)  # HD URL বের করা
        if hd_url:
            video_path = download_video(fb_url, hd_url)

    if video_path:
        return redirect(f"/{video_path}")  # ইউজারকে ডাউনলোড করা ভিডিওতে পাঠানো হবে
    else:
        return jsonify({"error": "Video download failed"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

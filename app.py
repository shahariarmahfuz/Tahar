import threading
import time
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# RapidAPI তথ্য
RAPIDAPI_HOST = "facebook-reel-and-video-downloader.p.rapidapi.com"
RAPIDAPI_KEY = "d4cc664bddmshad58db8819652d6p19e7adjsn6bcd66d66ef4"

def fetch_video_links(fb_url):
    """RapidAPI থেকে সকল ভিডিও লিংক বের করা"""
    url = f"https://{RAPIDAPI_HOST}/app/main.php?url={fb_url}"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        links = data.get("links", {})
        
        # HD এবং SD লিংক আলাদা করা
        hd_url = links.get("Download High Quality")
        sd_url = links.get("Download Low Quality")
        
        return {
            "hd_url": hd_url,
            "sd_url": sd_url
        }
    return None

@app.route("/fb", methods=["GET"])
def get_video_links():
    """ফেসবুক ভিডিওর HD ও SD লিংক রিটার্ন করা"""
    fb_url = request.args.get("link")
    if not fb_url:
        return jsonify({"error": "লিংক প্রদান করুন"}), 400

    # RapidAPI থেকে লিংক সংগ্রহ
    video_links = fetch_video_links(fb_url)
    
    if video_links:
        return jsonify({
            "status": "success",
            "links": video_links
        })
    else:
        return jsonify({"error": "ভিডিও লিংক পাওয়া যায়নি"}), 404

@app.route('/ping', methods=['GET'])
def ping():
    """সার্ভার একটিভ থাকা চেক করুন"""
    return jsonify({"status": "active"})

def keep_alive():
    """রেন্ডার সার্ভার একটিভ রাখতে পিং পাঠানো"""
    url = "https://video-for-you.onrender.com/ping"
    while True:
        time.sleep(300)
        try:
            requests.get(url)
            print("সার্ভার একটিভ রাখতে পিং পাঠানো হয়েছে!")
        except Exception as e:
            print(f"ত্রুটি: {e}")

if __name__ == "__main__":
    threading.Thread(target=keep_alive, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)

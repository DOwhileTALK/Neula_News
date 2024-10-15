from flask import Flask, render_template, request, jsonify
import feedparser
from bs4 import BeautifulSoup
from transformers import pipeline

app = Flask(__name__)

# List of world news RSS feeds (expanded)
rss_feeds = [
    "https://rss.cnn.com/rss/edition_world.rss",  # CNN World News
    
    
    
    "https://www.bbc.co.uk/news/world/rss.xml",  # BBC World News
    "https://www.theguardian.com/world/rss",  # The Guardian World News
    
    
    
]

# Global variable for the summarizer
summarizer = None

# Function to fetch the news
def fetch_news():
    news_items = []
    
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries:
            soup = BeautifulSoup(entry.summary, "html.parser")
            description = soup.get_text()  # Get plain text summary
            
            # Handle images
            image_url = None
            if 'media_content' in entry:
                image_url = entry.media_content[0].get('url', None)
            if not image_url:  # Check for image tag in the description
                img_tag = soup.find('img')
                if img_tag and 'src' in img_tag.attrs:
                    image_url = img_tag['src']
            if not image_url:
                image_url = '/static/no_image.jpg'  # Fallback image
            
            news = {
                'title': entry.title,
                'link': entry.link,
                'description': description.strip(),
                'image': image_url
            }
            news_items.append(news)

    # Prioritize articles with images
    news_items.sort(key=lambda x: x['image'] != '/static/no_image.jpg', reverse=True)
    return news_items

# Initialize the summarizer globally, but only when first needed
def get_summarizer():
    global summarizer
    if summarizer is None:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return summarizer

# Handle the article page
@app.route('/article/<int:article_id>')
def article(article_id):
    news_feed = fetch_news()
    article = news_feed[article_id]  # Get the article from the list using the article_id
    return render_template('article.html', article=article)

# Generate summary asynchronously
@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    data = request.json
    article_description = data.get('description', '')

    # Get the summarizer
    summarizer = get_summarizer()
    
    # Generate the summary
    summary = summarizer(article_description, max_length=150, min_length=50, do_sample=False)
    
    return jsonify({'summary': summary[0]['summary_text']})

# Homepage with pagination
@app.route('/')
def index():
    news_feed = fetch_news()
    page = request.args.get('page', 1, type=int)
    per_page = 6
    total = len(news_feed)
    total_pages = (total // per_page) + (1 if total % per_page else 0)
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages))

    start = (page - 1) * per_page
    end = start + per_page
    paginated_news = news_feed[start:end]
    
    return render_template('index.html', news=paginated_news, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)


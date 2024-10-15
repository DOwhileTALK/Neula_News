from flask import Flask, render_template, request
import feedparser
from bs4 import BeautifulSoup
from transformers import pipeline

# Initialize the Flask app
app = Flask(__name__)

# Initialize the summarizer
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# List of world news RSS feeds
rss_feeds = [
    "https://rss.cnn.com/rss/edition_world.rss",  # World News
    "https://news.google.com/news/rss",  # Google News
    # Add more sources if needed
]

# Fetch and parse the news
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

    return news_items

# Handle the article page and summarization
@app.route('/article/<int:article_id>')
def article(article_id):
    news_feed = fetch_news()
    article = news_feed[article_id]  # Get the article from the list using the article_id
    
    # Summarize the article content using the AI model
    full_description = article['description']
    summary = summarizer(full_description, max_length=150, min_length=50, do_sample=False)[0]['summary_text']
    
    return render_template('article.html', article=article, summary=summary)

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

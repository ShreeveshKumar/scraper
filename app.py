from flask import Flask, jsonify, request
import master_scraper
import subprocess
import os
import json

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Hackathon Scraper API!"

@app.route('/scrape', methods=['GET'])
def get_scraped_events():
    print("Received request for /api/scrape_events")
    try:
        print("Calling master_scraper_module.runscraper()...")
        scrape_results = master_scraper.runscraper()
        
        if scrape_results.get("error"):
             print(f"Scraping function reported an error: {scrape_results['error']}")
             return jsonify(scrape_results), 500 # Internal server error from scraper

        print(f"Successfully scraped {scrape_results['total_events']} events. Sending JSON response.")
        return jsonify(scrape_results), 200
        
    except Exception as e:
        import traceback
        print(f"Error during API call to scraper: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": "An internal server error occurred while calling the scraper.", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

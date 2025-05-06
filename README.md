
## A lightweight Flask-based API to scrape and serve hackathon event data from various sources using a custom scraper (`master_scraper.py`). This project is useful for developers and communities looking to aggregate hackathon data programmatically.

---

### 🧾 Table of Contents

* [Features](#features)
* [Installation](#installation)
* [API Endpoints](#api-endpoints)
* [File Structure](#file-structure)
* [License](#license)

---

### 📌 Features

* Scrapes hackathon data via a unified endpoint
* JSON API for integration with front-end apps or bots
* Error handling and debugging logs
* Easy to extend with additional data sources

---

### 🛠 Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/ShreeveshKumar/scraper
   cd hackathon-scraper-api
   ```

2. **Install Dependencies**
   Ensure Python 3.7+ and `pip` are installed.

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the API**

   ```bash
   python app.py
   ```

---

### 🌐 API Endpoints

#### `GET /`

**Description**: Basic route to confirm the API is running.
**Response**:

```json
"Welcome to the Hackathon Scraper API!"
```

---

#### `GET /scrape`

**Description**: Triggers the scraper and returns hackathon event data in JSON format.

**Response Example** (Success):

```json
{
  "total_events": 15,
  "events": [
    {
      "title": "Hack the Future",
      "date": "2025-06-15",
      "location": "Online",
      "link": "https://example.com/hack-the-future"
    },
    ...
  ]
}
```

**Response Example** (Failure):

```json
{
  "error": "An internal server error occurred while calling the scraper.",
  "details": "Specific traceback or error message"
}
```

---

### 🗂 File Structure

```
hackathon-scraper-api/
│
├── app.py                # Flask app with routing
├── master_scraper.py     # Custom scraper logic
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

### 📜 License

This project is licensed under the MIT License - feel free to use, modify, and distribute.
---

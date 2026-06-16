# 🌾 CropCast AI

> Weather-informed farming decisions for Tamil Nadu farmers.

CropCast AI analyzes historical weather and cultivation data to predict weather conditions for upcoming months and provide farming recommendations. Users select a month through a simple web interface to view predicted weather trends along with suggested crops and cultivation materials.

---

## Features

- 📅 **Month selector** — pick any month to get predictions
- 🌡️ **Weather forecast** — temperature, rainfall, humidity, wind speed
- ✅ **Crop recommendations** — what to grow and what to avoid
- 🧰 **Cultivation materials** — tools and inputs needed for the season
- 📈 **Annual trend chart** — interactive yearly weather overview

---

## Project Structure

```
cropcast/
├── app.py                  # Flask application
├── requirements.txt
├── .gitignore
├── data/
│   └── crop_data.py        # Historical weather & crop data
├── templates/
│   └── index.html          # Main HTML template
└── static/
    ├── css/style.css
    └── js/app.js
```

---

## Setup & Run

```bash
# 1. Clone the repo
git clone https://github.com/Jayavarshini-Jayakumaran/CropCast-AI.git
cd CropCast-AI

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open your browser at **http://localhost:5000**

---

🙌 **Connect** — [LinkedIn: Jayavarshini Jayakumaran](https://www.linkedin.com/in/jayavarshini-jayakumaran)

📄 **License** — [MIT](LICENSE)

<p align="center"><b>Finish what you started 💻 </b></p>
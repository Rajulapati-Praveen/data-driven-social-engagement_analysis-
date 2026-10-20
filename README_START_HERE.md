# START HERE: Complete Beginner Guide (From Zero to End)

This guide assumes you know **nothing** about Data Science. Read it from top to bottom.

---

## PART 1: What is this project? (in simple words)

Imagine a creator who makes Instagram Reels / YouTube Shorts about everyday struggles like
**Social Anxiety, Loneliness, Overthinking, Dating**. Today they pick topics by *guessing*.

**This project replaces guessing with data.** It answers these questions:

| Question | How we answer it |
|---|---|
| Which topic makes people share and save the most? | Viral Coefficient (a score we calculate) |
| Do people feel "this is so me" when they see a post? | NLP reads the comments and tags them Relatable / Neutral |
| Are Short videos better than Long ones? Visual hook or Text hook? Which posting time? | A/B testing (statistics) |
| What should we post next week? | A machine learning model recommends a plan |
| Which struggles are becoming popular soon? | Trend forecasting |
| How do we show all of this nicely? | A dashboard (a web page with charts) |

---

## PART 2: Words you must know

- **Dataset**: a table of data (like an Excel sheet). Each row is one post.
- **Views / Likes / Comments / Shares / Saves**: the numbers Instagram or YouTube gives for each post.
- **Retention rate**: what % of the video people watched.
- **Viral Coefficient**: our score for "how likely this post spreads".
  Formula: `(5 x shares + 3 x saves + 1.5 x comments + 0.5 x likes) / views x 100`.
  Shares and saves count more than likes, because sharing/saving takes effort, so it shows real connection.
- **Save-to-Share ratio**: saves divided by shares. High = "this is about me, I'll keep it". Low = "my friend should see this".
- **NLP (Natural Language Processing)**: teaching the computer to understand text. Here it reads comments like "omg this is so me" and tags them **Relatable**.
- **A/B test**: compare two versions (A vs B) and check whether the difference is real or just luck.
- **p-value**: if it is **below 0.05**, the difference is probably real (not luck).
- **Machine learning model**: a program that learns patterns from old data to predict new results.
- **Dashboard**: an interactive page of charts and tables.
- **Pipeline**: a series of steps that run one after another automatically.

---

## PART 3: What we built (all steps, in order)

We built one folder called `social_engagement_project`. Inside it, each file does one job.

| Step | What happens | File that does it |
|---|---|---|
| 1. Get data | Creates practice data: 220 posts, about 2,000 comments and keyword trends. (Real accounts can be used later, see Part 7.) | `src/generate_data.py` |
| 2. Clean data | Removes duplicates, fixes wrong or missing values, standardises topic names, adds new columns, saves into a database. | `src/clean_data.py` |
| 3. Virality | Calculates the Viral Coefficient for every post and ranks topics. | `src/virality.py` |
| 4. NLP | Reads comments, tags **Relatable / Neutral**, calculates a Relatability Score per post. | `src/sentiment.py` |
| 5. A/B tests | Statistically compares Short vs Long, Visual vs Text, caption styles, posting times. | `src/ab_testing.py` |
| 6. Recommender | A machine learning model predicts virality and suggests next week's plan. | `src/recommender.py` |
| 7. Trends | Finds rising keywords and forecasts 4 weeks ahead. | `src/trends.py` |
| 8. Report | Writes the Strategy Report automatically. | `src/report.py` |
| 9. Dashboard | Shows everything in charts in your browser. | `app.py` |
| Run all | Runs steps 1 to 8 with one command. | `run_pipeline.py` |
| Real data | Optional: pulls real data from YouTube / Instagram APIs. | `src/collect_real_data.py` |

---

## PART 4: How to run it (step by step, no experience needed)

### Step 1: Install Python
1. Go to **python.org/downloads** and download Python 3.10 or newer.
2. Run the installer. **Tick the box "Add Python to PATH"**, then click Install.

### Step 2: Unzip the project
Right-click `social_engagement_project.zip` and choose **Extract All**. You get a folder named `social_engagement_project`.

### Step 3: Open a terminal inside that folder
- **Windows:** open the folder, click the address bar, type `cmd` and press Enter.
- **Mac:** right-click the folder and choose "New Terminal at Folder".

### Step 4: Install the required libraries (one time, needs internet)
```
use==  pip install -r requirements.txt
``` or 
If this says "pip not found", use: `python -m pip install -r requirements.txt`

### Step 5: Run the whole project
```
use==  python run_pipeline.py
```
You will see 8 sections print on screen. When you see **"Done!"**, it worked.
This creates: cleaned data (`data/processed`), the database (`data/engagement.db`), trained models (`models`) and the report (`reports/strategy_report.md`).

### Step 6: Open the dashboard
```
use==  python -m streamlit run app.py
```
Your browser opens the dashboard. If not, go to **http://localhost:8501**. Press `Ctrl + C` in the terminal to stop it.

---
or read carfully please.

if you want to collect data and do this project we do this process. or if you want run my project do this three steps above.

## 4. How to run

**Setup (once):** install Python 3.10+, open a terminal in the project folder, then run
`pip install -r requirements.txt`

if you want to collect your own data you should this process below.
your_key means you should create one api key by own . you can ask google help and we can create own api key next we go youtube and click on profile share we can see channelID copy it past below 1 point it starts with UC....

**Real-data workflow (use this order):**
1. `python -m src.collect_real_data youtube --api-key YOUR_KEY --channel-id UCxxxx` (collects posts and comments into `data/raw/`)
2. use==  python -m src.auto_label      (guesses labels, backs up the original file, drops videos newer than 7 days, writes `data/raw/labels_to_review.csv`)
3. Open `labels_to_review.csv`, fix wrong labels, save, then run `python -m src.auto_label --apply`
4. `python run_pipeline.py --real` (clean, score, test, recommend, forecast, write report)
5. `python -m streamlit run app.py` (opens the dashboard at http://localhost:8501) 
it will show unlabeled data we need to some modifications
**Warning:** running `python run_pipeline.py` *without* `--real` regenerates simulated data and **overwrites** `data/raw/`. Use it only to try the project with practice data.

**Security:** never share your API key. It is typed on the command line only and is not stored in any file.


## PART 5: What each dashboard tab shows

1. **Overview**: total posts, views, followers gained, follower growth over time.
2. **Virality & Topics**: which topics have the highest Viral Coefficient and bring the most followers, plus the Save-to-Share ratio.
3. **Sentiment**: how many comments are Relatable. At the bottom there is a box where you type any comment and the model tags it live.
4. **A/B Tests**: tables showing which choices (Short vs Long etc.) really matter, with p-values.
5. **Recommendations**: the plan for next week (topic, format, hook, caption style, length, posting hour).
6. **Trends**: keywords that are rising or declining, with a 4-week forecast line.
7. **Report**: the strategy report inside the dashboard.

Use the **sidebar** (left) to filter by topic, format and date.

---

## PART 6: Which file answers which part of project brief

| Requirement in the brief | Where it is |
|---|---|
| Module 1: Content Performance Tracker | `src/generate_data.py`, `src/collect_real_data.py` |
| Module 2: Virality Prediction Engine | `src/virality.py` |
| Module 3: Audience Sentiment Analyzer | `src/sentiment.py` |
| Module 4: A/B Testing Framework | `src/ab_testing.py` |
| Module 5: Engagement Optimization Recommender | `src/recommender.py` |
| Module 6: Growth Visualization Dashboard | `app.py` |
| Module 7: Trend Forecasting | `src/trends.py` |
| Deliverable 1: Analytics Dashboard | `app.py` |
| Deliverable 2: Structured Dataset | `data/processed/*.csv` and `data/engagement.db` |
| Deliverable 3: NLP Sentiment Model | `src/sentiment.py` and `models/relatability_model.joblib` |
| Deliverable 4: Strategy Report | `reports/strategy_report.md` |
| Deliverable 5: The Content Series | **You must create this yourself** (see Part 7) |

---

## PART 7: What need to do for real i should post reel 

1. **Content Series (Deliverable 5):** make 8 to 12 short videos about struggles like Social Anxiety, Loneliness, Overthinking, Dating. Vary the length (about 20 sec vs about 60 sec), hook (visual vs text), caption style (question / story / list) and posting time. After 7 days, note down views, likes, comments, shares and saves.
2. **(Recommended) Use real data:** put your posts' numbers in `data/raw/posts_raw.csv` and comments in `data/raw/comments_raw.csv` (same column names as the practice files), then run `python run_pipeline.py --real`. The file `src/collect_real_data.py` can download data using YouTube or Instagram official APIs if you get API keys.
3. **Take screenshots** of each dashboard tab for your submission.
4. **Copy the report** from `reports/strategy_report.md` into Word or PDF and add your screenshots.
 

---

## PART 8: explaing my project

> "Content creators usually guess what will connect with people. We built a data science system that measures it.
> We collected performance data for each post, cleaned it and stored it in a SQL database.
> We created a Viral Coefficient that gives more weight to shares and saves than likes.
> An NLP model reads comments and tags them Relatable or Neutral.
> We ran statistical A/B tests to see whether format, hook and posting time really change results.
> A machine learning model recommends next week's content, and a forecasting module spots rising trends.
> Everything is shown in an interactive dashboard and summarised in an auto-generated strategy report."

---

## PART 9: If something goes wrong

| Problem | Fix |
|---|---|
| `python` not recognised | Reinstall Python and tick "Add Python to PATH". Try `py` or `python3` instead. |
| `pip` not recognised | Use `python -m pip install -r requirements.txt` |
| Dashboard says "Results not found" | Run `python run_pipeline.py` first |
| Port already in use | Run `streamlit run app.py --server.port 8502` |
| Any other error | Copy the full error message and send it to me |

---

## Folder map

```
social_engagement_project/
|-- app.py                 -> the dashboard
|-- run_pipeline.py        -> runs everything
|-- requirements.txt       -> libraries to install
|-- README.md              -> technical guide
|-- src/                   -> the code modules
|-- data/raw/              -> original data
|-- data/processed/        -> cleaned data and results
|-- data/engagement.db     -> SQL database
|-- models/                -> saved ML models
`-- reports/strategy_report.md -> the strategy report
```

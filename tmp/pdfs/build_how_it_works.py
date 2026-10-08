from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output' / 'pdf' / 'Football_ML_Monitoring_System_How_It_Works.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)

fonts = Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Segoe', str(fonts / 'segoeui.ttf')))
pdfmetrics.registerFont(TTFont('SegoeBold', str(fonts / 'segoeuib.ttf')))

W,H=612,792
NAVY=HexColor('#142E42'); TEAL=HexColor('#087F7B'); INK=HexColor('#203342')
MUTED=HexColor('#596E7C'); PALE=HexColor('#EAF5F3'); RULE=HexColor('#CDDCE1')
c=canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('Football ML Monitoring System - How It Works')
page=0; y=0; left=42; width=528

def new(title, subtitle, sources):
    global page,y
    if page: c.showPage()
    page+=1; y=H-42
    c.setFillColor(TEAL); c.rect(0,H-9,W,9,fill=1,stroke=0)
    c.setFont('SegoeBold',17); c.setFillColor(NAVY); c.drawString(left,y,title); y-=19
    c.setFont('Segoe',8.2); c.setFillColor(MUTED); c.drawString(left,y,subtitle); y-=17
    c.setStrokeColor(RULE); c.line(left,y,W-left,y); y-=14
    c.setFont('Segoe',6.7); c.setFillColor(MUTED)
    c.drawString(left,24,'SOURCE: '+sources[:112])
    c.drawRightString(W-left,24,f'{page} / 12')

def txt(s, size=8.3, lead=10.5, bold=False, color=INK, indent=0, gap=3):
    global y
    size*=1.13; lead*=1.19; gap*=1.15
    f='SegoeBold' if bold else 'Segoe'; c.setFont(f,size); c.setFillColor(color)
    lines=simpleSplit(s,f,size,width-indent)
    for line in lines:
        c.drawString(left+indent,y,line); y-=lead
    y-=gap
    return len(lines)

def head(s):
    global y
    y-=3; txt(s,10,12,True,NAVY,gap=3)

def box(label, body, h=None):
    global y
    lines=simpleSplit(body,'Segoe',8.8,width-20)
    bh=25+len(lines)*11.3 if h is None else h
    c.setFillColor(PALE); c.roundRect(left,y-bh+8,width,bh,5,fill=1,stroke=0)
    c.setFillColor(TEAL); c.setFont('SegoeBold',8.4); c.drawString(left+9,y-2,label.upper())
    yy=y-16;c.setFont('Segoe',8.8);c.setFillColor(INK)
    for line in lines:c.drawString(left+9,yy,line);yy-=11.3
    y-=bh+3

def table(headers, rows, widths=None, fs=7.15, line=8.55, pad=5, gap=6, density=1):
    global y
    fs*=1.18*density; line*=1.25*density; pad*=1.55*density; gap*=1.2
    ws=widths or [width/len(headers)]*len(headers)
    def cells(row,bold=False):
        return [simpleSplit(str(v),'SegoeBold' if bold else 'Segoe',fs,w-2*pad) for v,w in zip(row,ws)]
    allrows=[cells(headers,True)]+[cells(r) for r in rows]
    for i,rr in enumerate(allrows):
        rh=max(len(z) for z in rr)*line+2*pad
        c.setFillColor(NAVY if i==0 else (white if i%2 else HexColor('#F3F7F8')))
        c.rect(left,y-rh+3,width,rh,fill=1,stroke=0)
        xx=left
        for j,ls in enumerate(rr):
            c.setFont('SegoeBold' if i==0 else 'Segoe',fs)
            c.setFillColor(white if i==0 else INK)
            for k,v in enumerate(ls):c.drawString(xx+pad,y-pad-k*line,v)
            xx+=ws[j]
        y-=rh
    y-=gap

def check():
    print(f'page {page}: content bottom {y:.1f}')
    if y<39:raise RuntimeError(f'Page {page} overflow: y={y:.1f}')

# 1 - project crux
new('01  Project crux','Read top to bottom: the exact path from an entered record to a result.',
    'app.py; views/*.py; services/*.py; ml/*.py; database/*.py')
table(['STAGE','WHAT ACTUALLY HAPPENS'],[
 ('User / CSV','Data page accepts mapped CSV columns or manual form values; Players must exist first.'),
 ('Validation','Required columns/cells, dates, types, ranges, relationships and player/date uniqueness are checked.'),
 ('SQLite database','SQLAlchemy stores accepted rows in eight tables. Invalid rows are not stored.'),
 ('Retrieval','Services read table rows into Pandas frames, grouped by player and ordered by date where needed.'),
 ('Feature engineering','Earlier records become calendar-window sums, means, slopes, counts and latest values.'),
 ('ML / analytics','Three supervised pipelines train on labeled outcomes; trends calculate statistics; K-Means groups profiles.'),
 ('Prediction / evaluation','Saved models predict probabilities or a rating. Held-out tests produce metrics; clustering produces profiles.'),
 ('Streamlit UI','Dashboard, Data, Players, ML Predictions, Health and Model Analysis display results.')], [133,395],7.7,9.8)
box('Master path','RAW DATA  >  VALIDATION  >  SQLITE  >  RETRIEVAL  >  FEATURES  >  MODEL OR ANALYTICS  >  OUTPUT  >  UI')
head('Six major capabilities')
table(['MODULE','INPUT TO FINAL OUTPUT'],[
 ('Injury prediction','Training + recovery + injuries + profile  >  7-day onset probability and Low/Medium/High.'),
 ('Performance prediction','Prior matches + training + recovery + profile  >  next-match rating estimate.'),
 ('Health monitoring','Health + medical tests + health_events  >  7-day event probability and risk band.'),
 ('Health trends','Observed health/test series  >  rolling charts, latest change and trend direction.'),
 ('Health clustering','Recent health + available labs  >  K-Means group, profile and PCA chart.'),
 ('Model analysis','Training readiness + validation comparison + held-out test + global feature importance.')],[132,396],7.5,9.3)
check()

# 2 - tech
new('02  Technologies and roles','Only packages and systems present in the current repository.',
    'requirements.txt; Dockerfile; database/database.py; app.py; views/*.py; ml/*.py; tests/*.py')
table(['TECHNOLOGY','PURPOSE','WHERE USED'],[
 ('Python 3.12','Application language, feature calculations and ML orchestration.','Dockerfile; all .py files'),
 ('Streamlit','Page navigation, forms, buttons, tables, metrics and charts.','app.py; views/'),
 ('SQLite','Persistent default database football_ml.db.','database/database.py'),
 ('SQLAlchemy + SQL','ORM models, constraints, select/count queries and transactions.','database/; services/data_service.py'),
 ('Pandas','Read CSV, create frames, filter histories, calculate sums/means.','views/data.py; services/'),
 ('NumPy','Missing values, arrays, slopes, standard deviation, RMSE.','services/; ml/train.py'),
 ('Scikit-learn','Imputation, scaling, one-hot coding, models, split metrics, K-Means, PCA.','ml/; services/health_service.py'),
 ('Plotly','Confusion matrix, feature importance and clustering scatter plots.','views/health.py; views/model_analysis.py'),
 ('joblib','Serialize and reload fitted model pipelines.','ml/train.py; ml/health.py'),
 ('Docker','Builds Python 3.12 image and runs Streamlit on port 8501.','Dockerfile'),
 ('pytest','Project test suite.','tests/; pytest.ini'),
 ('python-dotenv','Declared dependency; no import found in application files.','requirements.txt')], [94,257,177],7.2,8.8)
head('Storage is separate from trained model files')
txt('SQLite holds imported data. A trained pipeline is a joblib file plus JSON metadata under data/model_artifacts; Health uses its health subfolder. A dataset fingerprint and feature version guard artifact reuse. The database URL can be overridden with FOOTBALL_ML_DATABASE_URL.')
box('What is absent','No XGBoost or Matplotlib dependency or import appears in the current application. No XGBoost model is trained.')
check()

# 3 - raw data
new('03  Raw data: exact CSV contract','R = required; O = optional. Types: S text, N numeric, I integer, D ISO date, B Boolean.',
    'services/validation_service.py; services/health_schema.py; database/models.py')
table(['FILE  >  SQLITE TABLE','COLUMNS (type; role)'],[
 ('players.csv > players','R player_id S key, name S display, age I years, position S role; O height N cm, weight N kg.'),
 ('training.csv > training','R player_id S, date D, duration_min N minutes, rpe N, distance N km, sprint_distance N m, high_speed_distance N m.'),
 ('recovery.csv > recovery','R player_id S, date D, sleep_hours N, sleep_quality N, hrv N, resting_hr N, soreness N, stress N.'),
 ('injuries.csv > injuries','R player_id S, injury_date D, injury_occurred B target log; O injury_type S, days_missed I.'),
 ('matches.csv > matches','R player_id S, match_date D, minutes_played I, goals I, assists I, shots I, passes_completed I, key_passes I, rating N target.'),
 ('health.csv > health_records','R player_id S, date D, resting_hr N, hrv N, sleep_hours N, sleep_quality N, soreness N, fatigue N, stress N, energy_level N, hydration_status N; O weight N, body_fat_pct N, blood_pressure_sys N, blood_pressure_dia N, oxygen_saturation N, body_temperature N.'),
 ('medical_tests.csv > medical_tests','R player_id S, test_date D; O hemoglobin, hematocrit, wbc_count, platelet_count, ferritin, serum_iron, vitamin_d, vitamin_b12, glucose, creatinine, crp (all N).'),
 ('health_events.csv > health_events','R player_id S, event_date D, health_event B target log; 1 = documented event, 0 = confirmed event-free day.')],[142,386],7.05,8.3)
head('Four different things')
txt('RAW INPUT = one of the CSV columns above. TARGET = injury_occurred over a future 7-day window, a match rating on its match date, or health_event over a future 7-day window. DERIVED FEATURE = a value computed only from earlier records. PREDICTION = model output on a selected date; it is never imported as an input.')
head('What each field family means and who consumes it')
table(['DATASET','FIELD MEANING / USED BY'],[
 ('players','ID links every record; name is display text. Age and position enter Injury/Performance ML; height and profile weight are stored/displayed, not ML features.'),
 ('training','Date anchors the session; duration and RPE form workload; distance checks sprint/high-speed consistency; sprint and high-speed distances form seven-day loads. Injury/Performance.'),
 ('recovery','Sleep duration/quality, HRV, resting HR, soreness and stress form seven-day means. Injury/Performance.'),
 ('injuries','injury_occurred is the daily outcome log and source of previous injury count. injury_type and days_missed are stored/displayed, not model features.'),
 ('matches','rating is the Performance target and prior-rating feature; minutes/goals/assists form recent sums. shots, passes_completed, key_passes are stored/displayed, not ML features.'),
 ('health + tests','Nine required daily health values form means/slopes/changes; six optional values provide recent latest values; eleven lab values provide latest/change/recency. Health ML and trends.'),
 ('health_events','health_event is the separate daily target log for Health ML; it is not inferred from measured health fields.')],[99,429],6.7,7.8,4,density=.78)
box('Missing / invalid / duplicate','Missing required column blocks validation; missing required cell rejects that row. Missing optional cell becomes NULL. Invalid date, Boolean, range or cross-field rule rejects row. Unknown player_id rejects row. Duplicate player ID or player/date rejects row. Default import is all-or-nothing; "Import valid rows only" can save valid rows while reporting errors.')
check()

# 4 - upload
new('04  Upload to ML-ready row','The same validation and transaction path handles CSV and manual entry.',
    'views/data.py; services/validation_service.py; services/data_service.py; database/models.py')
table(['STEP','ACTUAL BEHAVIOR'],[
 ('1 Input','Choose template; read CSV as strings; auto-detect a dataset when possible; user confirms dataset and column mapping. Unmapped columns are ignored.'),
 ('2 Schema','Each required mapped column must exist. One input column cannot map to two fields. Required empty cells are errors.'),
 ('3 Type/range/date','Dates must be YYYY-MM-DD and not future; numeric values finite and in field bounds; designated integers whole; Booleans 0/1, true/false, yes/no.'),
 ('4 Cross-field','Known player_id; training sprint/high-speed each <= distance*1000; match goals <= shots; health systolic > diastolic if both provided; unique player or player/date.'),
 ('5 Save','Preview valid rows and issues. Confirm import; default blocks all rows when any issue exists. Optional valid-only mode inserts accepted rows in a nested transaction and commits.'),
 ('6 Retrieve','read_dataset executes SQLAlchemy select for the chosen table and builds a Pandas frame; History/HealthHistory group by player.'),
 ('7 Engineer','A snapshot at point t uses dates strictly before t. Training/recovery/health use prior seven calendar days; model-specific features are assembled.'),
 ('8 Model ready','The resulting feature row is passed through the fitted imputer/scaler/encoder and then the selected estimator.')],[72,456],7.55,9.5)
box('Exact data path','RAW CSV  >  mapped fields  >  normalized valid rows  >  SQLite table  >  Pandas retrieval  >  prior-date snapshot  >  ML feature vector')
head('Missing data at prediction time')
txt('Injury and Performance omit a player unless workload_7d and sleep_hours_7d_mean exist; Performance also requires recent_rating_mean. Health omits a player with zero health observations in the prior seven days. Other missing numeric features pass to a median imputer, with missing indicators; optional medical values can remain absent.')
check()

# 5 features
new('05  Feature engineering formulas','t = prediction date; W7 = [t-7 days,t); W28 = [t-28 days,t). All formulas use prior records.',
    'services/feature_service.py; services/health_service.py')
table(['FEATURE / RAW INPUT','EXACT FORMULA; EXAMPLE; USED BY'],[
 ('training_load; duration_min,rpe','duration_min * rpe. Example 60*7=420. Intermediate session load for workload sums.'),
 ('workload_7d / 28d','Sum of training_load in W7 / W28. Example loads 420+300=720 / 4 weeks of 720=2880. Injury + Performance.'),
 ('workload_change_pct','(workload_7d/(workload_28d/4)-1)*100; example 720 vs 2880/4 = 0%. NaN without full 28-day history or positive baseline. Injury + Performance.'),
 ('sprint_load_7d; sprint_distance','Sum sprint_distance in W7; example 100+80=180 m. Injury + Performance.'),
 ('high_speed_load_7d; high_speed_distance','Sum high_speed_distance in W7; example 300+250=550 m. Injury + Performance.'),
 ('six recovery 7d means','Mean of W7 values for sleep_hours, sleep_quality, hrv, resting_hr, soreness, stress; e.g. HRV (50+60)/2=55. Injury + Performance.'),
 ('previous_injuries','Count prior injury_occurred=True where injury_date<t; e.g. 2 previous onsets -> 2. Injury only.'),
 ('recent_rating_mean','Mean ratings in latest five prior matches; e.g. (7+8+6)/3=7. Performance only.'),
 ('rating_trend','Slope of least-squares line through prior rating order x=0..n-1; e.g. 6,7,8 -> +1 per match. Performance.'),
 ('rating_consistency','Population standard deviation of last five prior ratings; e.g. 7,7,7 -> 0. Performance.'),
 ('recent_minutes/goals/assists','Sum each field across latest five earlier matches; e.g. 80+90=170 minutes. Performance.'),
 ('age / position','Profile values copied unchanged; age numeric, position one-hot encoded. Injury + Performance.')],[160,368],6.9,8.0,4)
head('Health feature families - exact expansion')
txt('For each of 9 required health fields f, create f_7d_mean = mean(W7), f_trend = least-squares slope against calendar days in W7, and f_change = last(W7)-first(W7). Example HRV 50,60 over two days -> mean 55, trend +10/day, change +10. All 27 enter Health ML.')
txt('For each of 6 optional health fields, latest_f = last non-null W7 value. For each of 11 medical fields, latest_f = last value before t; change_f = last-previous; days_since_f = t-last test date. Example ferritin 30 then 35 with last test 4 days ago -> latest 35, change +5, days_since 4. Add health_observations_7d = count W7 rows and days_since_health = t-last health date. Total Health ML inputs: 68. Missing history yields NaN and is imputed.')
check()

# 6 injury
new('06  Injury prediction: every step','One training row follows a recorded training day; forecast starts the next midnight.',
    'services/feature_service.py; ml/train.py; ml/predict.py; views/model_analysis.py')
table(['STEP','WHAT HAPPENS'],[
 ('1 Input','players + training + recovery + injuries are retrieved; matches are read for snapshot but not in Injury feature list.'),
 ('2 Validation/storage','Import rules on pages 3-4 apply; tables players, training, recovery, injuries hold the raw values.'),
 ('3 Features','age, position, 5 training values, 6 recovery means, previous_injuries (14 inputs). All dated features precede t.'),
 ('4 Target','t = training date + 1; y=1 if any injury_occurred=True in [t,t+7 days). y=0 only if all seven dates have explicit injury outcome rows and none is True. A same-day onset excludes the example.'),
 ('5 Readiness','At least 40 usable windows, 5 positive windows and 5 recorded onsets; both labels; required feature availability; viable chronological partitions.'),
 ('6 Split/leakage','Distinct dates split at 60% and 80%; purge rows whose label_end crosses next boundary. >=5 rows each. Same-day feature records excluded. Players can appear across periods.'),
 ('7 Preprocess','Numeric median imputation + missing indicators + StandardScaler; position OneHotEncoder(handle_unknown=ignore). Fitted on training partition only during comparison.'),
 ('8 Candidates','Logistic Regression (balanced linear log-odds); Random Forest (100 balanced trees, min leaf 2); Gradient Boosting (sequential trees). Each receives the same preprocessed features and predicts class/probability.'),
 ('9 Select/test/save','Validation score = 0.7*recall + 0.3*F1; highest wins, ties follow listed order. Refit winner on train+validation, evaluate untouched test, save joblib + JSON.'),
 ('10 Predict/UI','predict_proba(X)[:,1] = estimated onset probability. Low p<0.4; Medium 0.4<=p<0.7; High p>=0.7. ML Predictions/Dashboard/Players show p and band.')],[94,434],7.1,8.7)
box('Important interpretation','The displayed percentage is the fitted classifier output, not a rule-based injury score. It is uncalibrated research output. A missing outcome day is unknown, never assumed injury-free.')
check()

# 7 performance
new('07  Performance prediction: every step','The supervised target is an actual match rating; prediction estimates a future rating.',
    'services/feature_service.py; ml/train.py; ml/predict.py')
table(['STEP','WHAT HAPPENS'],[
 ('1-3 Input > features','Read players, prior matches, training and recovery; validate/store first. At match date t, use last 5 earlier matches, W7/W28 training and W7 recovery. Features: age, position, 6 match-history, 5 training, 6 recovery = 19.'),
 ('4 Target','y = actual rating on match at t (0-10 input scale). First match per player is skipped because no earlier match exists.'),
 ('5 Readiness','>=35 usable rows, match history, required feature coverage, >=10 distinct prediction dates, >=5 rows after purge in each partition, at least two training target values.'),
 ('6 Split/preprocess','Same date-based 60/20/20 and boundary purge as Injury; numerical median + missing flags + scaling; one-hot position.'),
 ('7 Candidates','Linear Regression fits linear coefficients. Random Forest Regressor averages 100 tree outputs (min leaf 2). Gradient Boosting Regressor adds trees to correct residuals. All output a continuous rating estimate.'),
 ('8 Select/save','Choose lowest validation MAE (equivalent to max -MAE); ties use candidate order. Refit train+validation, evaluate test once, save joblib + JSON.'),
 ('9 Predict/UI','For eligible players, pipeline.predict produces predicted_next_rating. It is a numerical estimate of the next match rating, not a known result. The code does not clamp it to 0-10.')],[100,428],7.4,9.1)
head('Match-history calculations - a tiny example')
table(['INPUT','FORMULA / OUTPUT','REASON'],[
 ('ratings 6,7,8','mean=7; trend slope=+1; population SD~0.82','level, direction, variability'),
 ('minutes 70,80,90','sum=240','recent playing time'),
 ('goals 0,1,0; assists 1,0,1','sum goals=1; assists=2','recent contributions')],[120,215,193],7.3,9)
head('Regression metrics used to compare and report')
txt('MAE = mean(|y - yhat|); errors 1,2 -> MAE 1.5, lower is better. RMSE = sqrt(mean((y-yhat)^2)); errors 1,2 -> sqrt(2.5)=1.58, lower is better. R2 = 1 - sum squared errors / sum((y-mean y)^2), higher is better; can be negative. Model selection uses MAE only; the other two appear in evaluation.')
check()

# 8 health
new('08  Health monitoring: every step','Health measurements are inputs; health_events is the independent outcome log.',
    'services/health_schema.py; services/health_service.py; ml/health.py; views/health.py')
table(['STEP','ACTUAL HEALTH PIPELINE'],[
 ('1 Input','health.csv: 9 required daily fields + 6 optional vitals/body fields; medical_tests.csv: test_date + 11 optional labs; health_events.csv: daily label observations.'),
 ('2 Validate/store','Same import checks; accepted rows enter health_records, medical_tests, health_events. A medical panel may have no measured values and still be accepted with warning.'),
 ('3 Features','For each required field: W7 mean, calendar-day slope and last-first change (27). Six optional latest W7 values. Eleven lab latest/change/days-since triples (33). Count W7 health rows and days since last = 68 inputs.'),
 ('4 Target','For each health observation day d, t=d+1. y=1 if any health_event=True in [t,t+7). y=0 only if all seven follow-up dates are explicitly logged and none is True; otherwise skip.'),
 ('5 Readiness','>=40 labeled windows, >=5 documented events, both classes, valid 60/20/20 chronological partitions with >=5 rows each and both classes in train/validation.'),
 ('6 Preprocess','Numeric median imputation (keep all-empty fields) + missing indicators, then StandardScaler. Optional or absent lab features are not claimed to be observed.'),
 ('7 Train/select','Logistic Regression, Random Forest Classifier (100 trees, balanced, min leaf 2), Gradient Boosting Classifier. Maximize 0.7*validation recall + 0.3*validation F1; candidate order breaks ties.'),
 ('8 Save/test','Refit selected model on train+validation; evaluate held-out test; save health-specific joblib + JSON and reference medians.'),
 ('9 Predict/UI','At least one health row in W7 required. predict_proba[:,1] -> LOW <0.4, MEDIUM 0.4-<0.7, HIGH >=0.7. Health tab shows band, percent, model metrics and local one-feature substitutions.')],[91,437],7.05,8.65)
head('The 9 required measurements each create 3 features')
table(['RAW FIELD','MEAN / TREND / CHANGE FEATURE NAMES'],[
 ('resting_hr, hrv','resting_hr_*; hrv_*'),
 ('sleep_hours, sleep_quality','sleep_hours_*; sleep_quality_*'),
 ('soreness, fatigue, stress','soreness_*; fatigue_*; stress_*'),
 ('energy_level, hydration_status','energy_level_*; hydration_status_*')],[147,381],6.8,7.9,4)
txt('For every * above, suffixes are 7d_mean, trend, change. W7 mean = arithmetic mean; trend = least-squares slope per calendar day (NaN with <2 dates); change = latest minus earliest W7 reading (NaN with <2). All 27 are inputs to each Health candidate, along with all optional/latest, lab and recency features.',7.7,9.2)
box('Feature example','HRV 50 then 60 across two calendar days -> hrv_7d_mean=55, hrv_trend=+10/day, hrv_change=+10. Ferritin 30 then 35, last tested 4 days before t -> latest=35, change=+5, days_since=4. Each value enters each Health candidate.')
check()

# 9 trends/clustering
new('09  Health trends and clustering','These two Health tabs serve different purposes and have no historical target labels.',
    'services/health_service.py; views/health.py')
head('Health Trends - statistical analysis, no fitted supervised model')
table(['INPUT / ACTION','FORMULA / OUTPUT / PURPOSE'],[
 ('Player + field','Read observed health or medical-test values in date order; absent fields show no chart.'),
 ('Rolling chart','Time-based rolling mean over 7 days for health or 90 days for labs; min 1 value. Smooths observed variation.'),
 ('Recent value','Last observed value; displayed in summary.'),
 ('Change percent','(last/previous - 1)*100, only when >=2 values and previous != 0; displayed as change_pct.'),
 ('Direction','Least-squares slope on last 7 observed values vs calendar days: >1e-8 Rising, <-1e-8 Declining, else Stable; <2 values -> Insufficient history.'),
 ('UI','Heart, Sleep, Recovery, Hydration, Body, Vitals, Medical tests expanders; summary table and line chart.')],[132,396],7.3,9)
head('Health Clustering - unsupervised K-Means, no given answer')
table(['STEP','EXACT BEHAVIOR'],[
 ('Select records','At selected profile date, include players with >=1 health row in W7; require at least k players.'),
 ('Candidate features','Nine 7-day means for required health fields plus latest hemoglobin, ferritin, vitamin_d, crp.'),
 ('Keep / fill / scale','Keep feature when >=50% nonmissing and >1 unique value; median-impute gaps, StandardScaler.'),
 ('K-Means','User chooses k=2,3,4,5 (default 3). Require >=k distinct scaled profiles. Fit KMeans(random_state=42,n_init=10); display cluster numbers 1..k.'),
 ('Interpret','Profile = per-cluster raw-feature mean. Compare to roster mean / roster SD; report three largest absolute differences as higher/lower average.'),
 ('Visualize','PCA projects scaled features to up to 2 components (PC2=0 if one feature); Plotly scatter colors points by cluster. PCA is for display, not K-Means input.')],[112,416],7.2,8.8)
box('No clustering score','The code displays assignments, group sizes implicitly through rows, profiles and a PCA chart. It does not calculate a silhouette score.')
check()

# 10 supervised
new('10  What supervised ML means here','Past inputs and known outcomes train three models. New inputs produce estimates.',
    'services/feature_service.py; services/health_service.py; ml/train.py; ml/health.py')
table(['MODULE','HISTORICAL INPUT','KNOWN TARGET','TYPE','FINAL OUTPUT'],[
 ('Injury','Earlier training/recovery/profile/injury count','New onset within next 7 dates','Supervised classification','Probability + risk band'),
 ('Performance','Earlier matches/training/recovery/profile','Actual rating on match date','Supervised regression','Estimated next rating'),
 ('Health','Earlier health/test measurements','Event within next 7 dates','Supervised classification','Probability + risk band'),
 ('Health Trends','Observed series','None','Statistics + charts','Mean/change/direction'),
 ('Health Clustering','Recent health/lab profile','None','Unsupervised K-Means','Cluster/group profile')],[78,140,106,91,113],6.7,8.0)
box('Training','PAST INPUTS + DOCUMENTED OUTCOME  >  preprocess on training data  >  fit each candidate  >  compare validation results  >  refit winner  >  test')
box('Prediction','NEW PRIOR-DATE INPUTS  >  saved preprocessing + selected model  >  probability or rating estimate  >  risk band when classification  >  UI')
head('What a label does - and does not - mean')
txt('An Injury or Health positive training row means at least one documented new onset occurred in the following seven calendar dates. A negative row requires explicit zero observations on every one of those dates. A missing date provides no answer. Performance uses the actual rating from the match at that date. Health measurements themselves do not create health_event labels.')
head('Why the time split matters')
txt('A model is selected on later validation dates and reported on still later test dates. Feature snapshots exclude same-day and future values. Rows whose outcome window crosses a partition boundary are removed from the earlier partition. This limits temporal leakage; the same players can still occur in all periods, so test results are about later records, not unseen players.')
check()

# 11 evaluation
new('11  Evaluation, cutoffs and validation ranges','Metrics below are computed on model outputs; input bounds are software checks, not clinical limits.',
    'ml/train.py; ml/health.py; ml/predict.py; services/validation_service.py')
table(['METRIC','FORMULA / RANGE / DIRECTION / PROJECT MEANING'],[
 ('Accuracy','(TP+TN)/N; 0..1 higher. Overall correct class share.'),
 ('Precision','TP/(TP+FP); 0..1 higher. Among predicted onsets, share documented.'),
 ('Recall','TP/(TP+FN); 0..1 higher. Share of documented onsets caught.'),
 ('F1','2*precision*recall/(precision+recall); 0..1 higher. Balances precision/recall.'),
 ('ROC-AUC','Area under TPR vs FPR across cutoffs; 0..1 higher. Probability ranking (None if test has one class).'),
 ('Confusion matrix','[[TN,FP],[FN,TP]]; counts >=0. Shows exact class error types.'),
 ('MAE / RMSE','mean |e| / sqrt(mean e^2); >=0 lower. Rating error size; RMSE weights large misses more.'),
 ('R2','1 - SSE/SST; <=1, higher. Fit vs predicting mean rating; may be negative; None for one actual value.'),
 ('Clustering','No silhouette metric in code. Cluster IDs, member rows and observed cluster means are shown.')],[113,415],7.05,8.25)
box('Decision cutoffs','Injury: Low p<0.40, Medium 0.40<=p<0.70, High p>=0.70. Health: LOW / MEDIUM / HIGH at the same values. Selection: classification max(0.7*recall+0.3*F1); Performance min validation MAE.')
head('Actual upload ranges (inclusive)')
txt('RPE, sleep_quality, soreness, stress, fatigue, energy_level, hydration_status, rating: 0-10. sleep_hours: 0-24; HRV: 1-300; resting_hr: 20-220. age: 10-70; height: 100-250; weight: 25-200; duration_min: 1-360; distance km: 0-60; sprint and high-speed distance m: 0-60000.')
txt('Match: minutes 1-130; goals/assists 0-30; shots/key_passes 0-100; passes_completed 0-300. days_missed 0-3650. Body fat and oxygen saturation 0-100; systolic 40-300; diastolic 20-200; temperature 25-45. Medical fields 0-100000, except hematocrit 0-100. Dates cannot be future.')
check()

# 12 UI + master
new('12  Complete UI to backend walkthrough','Each row follows a user action to its query, calculation and visible result.',
    'app.py; views/dashboard.py; views/data.py; views/players.py; views/predictions.py; views/health.py; views/model_analysis.py')
table(['PAGE / ACTION','FUNCTION > QUERY > CALCULATION / MODEL > DISPLAY'],[
 ('Dashboard / open','dataset_counts + readiness read all tables; prediction_tables loads saved Injury/Performance artifacts, rebuilds features and predicts; health summary calls Health artifact. Counts, readiness, predictions, elevated-risk count.'),
 ('Data / Import','upload > pd.read_csv > mapping > validate_input > import_records > INSERT via SQLAlchemy. Preview, errors, saved-row notice; Records tab SELECTs/export CSV.'),
 ('Data / Save record','Manual form > same validation/import transaction. Invalid values shown; successful save reruns page.'),
 ('Players / choose','read_dataset for roster, training, recovery, matches, injuries; calculate training_load; History.snapshot; prediction_tables. History tables, load/rating charts, features and model predictions.'),
 ('ML Predictions / date','load_artifact > History.prediction_frame > predict_proba or predict. Probability/band and estimated rating, plus global feature list; unavailable artifact/history shows message.'),
 ('Model Analysis / Train','readiness > History.training_frame > temporal_split > preprocess + three candidate estimators > validation selection > refit > test > joblib/JSON. Comparisons, metrics, matrix/importance.'),
 ('Health / Train','HealthHistory.training_frame + assess_health > three classifiers > validation selection > held-out test > health artifact. Readiness and evaluation.'),
 ('Health / Predict','Select player/date > HealthHistory.snapshot > saved pipeline.predict_proba > band + explain_prediction reference substitution. Risk, percent, feature differences.'),
 ('Health / Trends','Read selected player field > trend_analysis; no model. Summary and line chart.'),
 ('Health / Cluster','HealthHistory.prediction_frame > feature filter/impute/scale > KMeans + PCA; assignments, profiles, summaries and scatter.')],[119,409],6.75,7.9,4)
box('One master diagram','RAW DATA  >  VALIDATION  >  DATABASE  >  FEATURE FORMULAS  >  ML FEATURES  >  MODEL / ANALYTICS  >  PREDICTION OR GROUP  >  RISK BAND / SCORE  >  EVALUATION  >  STREAMLIT UI')
head('Viva checklist')
txt('1. Name the eight CSVs and three label sources.  2. Explain why absent outcome dates are unknown.  3. Derive training load, workload change, rating trend and one Health feature.  4. State 60/20/20 chronological split and purge.  5. Name all candidate models and selection formulas.  6. Distinguish class probability, rating regression, trends and K-Means.  7. State 0.40/0.70 cutoffs and UI destinations.',7.8,9.6)
check()
c.save()
print(f'{OUT}\nPAGES={page}')

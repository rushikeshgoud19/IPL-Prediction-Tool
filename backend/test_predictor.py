import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import log_loss, accuracy_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("IPL PREDICTION SYSTEM v5 - HIGH ACCURACY MODEL")
print("=" * 70)

# Load data
df = pd.read_csv(r'c:\Users\rushi\OneDrive\Desktop\IPL prediction\backend\data\match_summary.csv')
print("Loaded %d matches from %s to %s" % (len(df), df['date'].min(), df['date'].max()))

# Encode
all_teams = pd.concat([df['team_a'], df['team_b']]).unique()
team_le = LabelEncoder()
team_le.fit(all_teams)
venue_le = LabelEncoder()
venue_le.fit(df['venue'].unique())

df['team_a_enc'] = team_le.transform(df['team_a'])
df['team_b_enc'] = team_le.transform(df['team_b'])
df['venue_enc'] = venue_le.transform(df['venue'])
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# Compute rolling features with MORE HISTORY
team_stats = {}
h2h_stats = {}
venue_stats = {}
form_stats = {}
last_n_stats = {}

# Extended rolling window
def get_recent_form(team, n=10):
    if team not in form_stats or len(form_stats[team]) < n:
        return 0.5
    return np.mean(form_stats[team][-n:])

def get_momentum(team):
    if team not in form_stats or len(form_stats[team]) < 3:
        return 0
    recent = form_stats[team][-3:]
    return sum(recent)

# Build features
wr_a_list, wr_b_list = [], []
h2h_wr_a_list, venue_wr_a_list = [], []
recent_a_list, recent_b_list = [], []
momentum_a_list, momentum_b_list = [], []
win_streak_a_list, win_streak_b_list = [], []

for idx, row in df.iterrows():
    ta, tb, venue = row['team_a'], row['team_b'], row['venue']

    # Win rates (all-time)
    ts_a = team_stats.get(ta, [0, 0])
    ts_b = team_stats.get(tb, [0, 0])
    wr_a = ts_a[0] / ts_a[1] if ts_a[1] > 0 else 0.5
    wr_b = ts_b[0] / ts_b[1] if ts_b[1] > 0 else 0.5

    # Win rates (last 20 matches - recency bias)
    ts_a_recent = team_stats.get(ta, [0, 0, []])
    ts_b_recent = team_stats.get(tb, [0, 0, []])
    if len(ts_a_recent) > 2:
        recent_a_wr = sum(ts_a_recent[2][-20:]) / min(len(ts_a_recent[2]), 20) if ts_a_recent[2] else 0.5
    else:
        recent_a_wr = wr_a
    if len(ts_b_recent) > 2:
        recent_b_wr = sum(ts_b_recent[2][-20:]) / min(len(ts_b_recent[2]), 20) if ts_b_recent[2] else 0.5
    else:
        recent_b_wr = wr_b

    # H2H
    h2h_key = tuple(sorted([ta, tb]))
    h2h = h2h_stats.get(h2h_key, {ta: 0, tb: 0, 'total': 0})
    h2h_wr_a = h2h[ta] / h2h['total'] if h2h['total'] > 0 else 0.5

    # H2H recent (last 5)
    h2h_recent_key = tuple(sorted([ta, tb]))
    h2h_recent = h2h_stats.get(h2h_recent_key, {'recent': []})
    h2h_recent_a = np.mean(h2h_recent.get('recent', [])[-5:]) if h2h_recent.get('recent') else 0.5

    # Venue performance
    vs_key = tuple(sorted([ta, venue]))
    vs_venue = venue_stats.get(vs_key, {ta: 0, 'total': 0})
    venue_wr_a = vs_venue[ta] / vs_venue['total'] if vs_venue['total'] > 0 else 0.5

    # Recent form
    fs_a = form_stats.get(ta, [])
    fs_b = form_stats.get(tb, [])
    recent_a = np.mean(fs_a[-5:]) if fs_a else 0.5
    recent_b = np.mean(fs_b[-5:]) if fs_b else 0.5

    # Momentum (wins in last 3)
    momentum_a = get_momentum(ta)
    momentum_b = get_momentum(tb)

    # Win streak
    streak_a = 0
    streak_b = 0
    for w in reversed(fs_a[-10:]):
        if w == 1: streak_a += 1
        else: break
    for w in reversed(fs_b[-10:]):
        if w == 1: streak_b += 1
        else: break

    wr_a_list.append(wr_a)
    wr_b_list.append(wr_b)
    h2h_wr_a_list.append(h2h_wr_a)
    venue_wr_a_list.append(venue_wr_a)
    recent_a_list.append(recent_a)
    recent_b_list.append(recent_b)
    momentum_a_list.append(momentum_a)
    momentum_b_list.append(momentum_b)
    win_streak_a_list.append(streak_a)
    win_streak_b_list.append(streak_b)

    # Update after match
    winner = ta if 'A' in row['outcome'] else tb
    winner_is_a = winner == ta

    for team in [ta, tb]:
        if team not in team_stats:
            team_stats[team] = [0, 0, []]
        team_stats[team][1] += 1
        if winner == team:
            team_stats[team][0] += 1
            team_stats[team][2].append(1)
        else:
            team_stats[team][2].append(0)
        team_stats[team][2] = team_stats[team][2][-50:]  # Keep last 50

    for team in [ta, tb]:
        if team not in form_stats:
            form_stats[team] = []
        form_stats[team].append(1 if winner == team else 0)
        form_stats[team] = form_stats[team][-50:]

    # H2H stats
    if h2h_key not in h2h_stats:
        h2h_stats[h2h_key] = {ta: 0, tb: 0, 'total': 0, 'recent': []}
    h2h_stats[h2h_key]['total'] += 1
    h2h_stats[h2h_key][winner] = h2h_stats[h2h_key].get(winner, 0) + 1
    h2h_stats[h2h_key]['recent'] = h2h_stats[h2h_key].get('recent', [])
    h2h_stats[h2h_key]['recent'].append(1 if winner_is_a else 0)
    h2h_stats[h2h_key]['recent'] = h2h_stats[h2h_key]['recent'][-20:]

    # Venue stats
    if vs_key not in venue_stats:
        venue_stats[vs_key] = {ta: 0, 'total': 0}
    venue_stats[vs_key]['total'] += 1
    if winner_is_a:
        venue_stats[vs_key][ta] = venue_stats[vs_key].get(ta, 0) + 1

df['wr_a'] = wr_a_list
df['wr_b'] = wr_b_list
df['h2h_wr_a'] = h2h_wr_a_list
df['venue_wr_a'] = venue_wr_a_list
df['recent_a'] = recent_a_list
df['recent_b'] = recent_b_list
df['momentum_a'] = momentum_a_list
df['momentum_b'] = momentum_b_list
df['win_streak_a'] = win_streak_a_list
df['win_streak_b'] = win_streak_b_list

# Derived features
df['wr_diff'] = df['wr_a'] - df['wr_b']
df['form_diff'] = df['recent_a'] - df['recent_b']
df['h2h_advantage'] = df['h2h_wr_a'] - 0.5
df['momentum_diff'] = df['momentum_a'] - df['momentum_b']
df['streak_diff'] = df['win_streak_a'] - df['win_streak_b']

# Binary winner target
df['winner'] = df['outcome'].apply(lambda x: 0 if x in ['A_big', 'A_small'] else 1)

# Features
feature_cols = ['team_a_enc', 'team_b_enc', 'venue_enc',
                'wr_a', 'wr_b', 'h2h_wr_a', 'venue_wr_a',
                'recent_a', 'recent_b', 'momentum_a', 'momentum_b',
                'win_streak_a', 'win_streak_b',
                'wr_diff', 'form_diff', 'h2h_advantage',
                'momentum_diff', 'streak_diff']

X = df[feature_cols].values
y = df['winner'].values  # Binary: 0=A wins, 1=B wins

# Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split - use recent matches for validation
split_date = pd.to_datetime('2025-01-01')
train_mask = df['date'] < split_date
X_train, y_train = X_scaled[train_mask], y[train_mask]
X_val, y_val = X_scaled[~train_mask], y[~train_mask]

print("\nTrain size: %d, Validation size: %d" % (len(X_train), len(X_val)))

# Train multiple models and ensemble
print("\n[TRAINING] Training ensemble of models...")

# Model 1: Random Forest
rf = RandomForestClassifier(
    n_estimators=500, max_depth=20, min_samples_split=3,
    min_samples_leaf=1, class_weight='balanced', random_state=42, n_jobs=-1
)

# Model 2: Gradient Boosting
gb = GradientBoostingClassifier(
    n_estimators=300, max_depth=8, learning_rate=0.05,
    min_samples_split=5, min_samples_leaf=2, subsample=0.8, random_state=42
)

# Model 3: Extra Trees
et = ExtraTreesClassifier(
    n_estimators=500, max_depth=20, min_samples_split=3,
    class_weight='balanced', random_state=42, n_jobs=-1
)

# Model 4: Logistic Regression
lr = LogisticRegression(class_weight='balanced', max_iter=1000, C=0.5, random_state=42)

# Calibrate all models
rf_cal = CalibratedClassifierCV(rf, method='sigmoid', cv=5)
gb_cal = CalibratedClassifierCV(gb, method='sigmoid', cv=5)
et_cal = CalibratedClassifierCV(et, method='sigmoid', cv=5)
lr_cal = CalibratedClassifierCV(lr, method='sigmoid', cv=5)

print("Training Random Forest...")
rf_cal.fit(X_train, y_train)
print("Training Gradient Boosting...")
gb_cal.fit(X_train, y_train)
print("Training Extra Trees...")
et_cal.fit(X_train, y_train)
print("Training Logistic Regression...")
lr_cal.fit(X_train, y_train)

# Validation
print("\n" + "=" * 70)
print("MODEL VALIDATION RESULTS (Binary: Who Wins)")
print("=" * 70)

models = [('Random Forest', rf_cal), ('Gradient Boosting', gb_cal),
          ('Extra Trees', et_cal), ('Logistic Regression', lr_cal)]

best_acc = 0
best_model = None
best_probs = None

for name, model in models:
    preds = model.predict(X_val)
    probs = model.predict_proba(X_val)
    acc = accuracy_score(y_val, preds)
    ll = log_loss(y_val, probs)

    cv = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')

    print("\n%s:" % name)
    print("  Validation Accuracy: %.2f%%" % (acc * 100))
    print("  Log Loss: %.4f" % ll)
    print("  5-Fold CV: %.2f%% (+/- %.2f%%)" % (cv.mean() * 100, cv.std() * 100))

    if acc > best_acc:
        best_acc = acc
        best_model = name
        best_probs = probs

# Ensemble (weighted average)
print("\n[ENSEMBLE] Creating weighted ensemble...")
ensemble_probs = (
    0.3 * rf_cal.predict_proba(X_val) +
    0.3 * gb_cal.predict_proba(X_val) +
    0.25 * et_cal.predict_proba(X_val) +
    0.15 * lr_cal.predict_proba(X_val)
)

ensemble_preds = (ensemble_probs[:, 1] > 0.5).astype(int)
ensemble_acc = accuracy_score(y_val, ensemble_preds)
ensemble_ll = log_loss(y_val, ensemble_probs)

print("\nENSEMBLE (Weighted Average):")
print("  Validation Accuracy: %.2f%%" % (ensemble_acc * 100))
print("  Log Loss: %.4f" % ensemble_ll)

# Feature importance from RF
print("\nTop 10 Feature Importance (Random Forest):")
rf.fit(X_train, y_train)
for feat, imp in sorted(zip(feature_cols, rf.feature_importances_), key=lambda x: -x[1])[:10]:
    print("  %s: %.4f" % (feat, imp))

# Convert back to 4-class for submission
# P(A_big) = P(A wins) * P(big | A wins)
# P(A_small) = P(A wins) * P(small | A wins)
# etc.

print("\n" + "=" * 70)
print("CONVERTING TO 4-CLASS OUTPUT (A_big, A_small, B_big, B_small)")
print("=" * 70)

# Train a margin predictor
y_margin = df['outcome'].apply(lambda x: 1 if x in ['A_big', 'B_big'] else 0).values

X_train_m, y_train_m = X_scaled[train_mask], y_margin[train_mask]
X_val_m, y_val_m = X_scaled[~train_mask], y_margin[~train_mask]

margin_model = GradientBoostingClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.1,
    random_state=42
)
margin_model.fit(X_train_m, y_train_m)
margin_probs = margin_model.predict_proba(X_val_m)

# Combine winner + margin predictions
winner_probs_val = ensemble_probs

four_class_probs = np.zeros((len(X_val), 4))
for i in range(len(X_val)):
    p_a_wins = winner_probs_val[i][0]
    p_b_wins = winner_probs_val[i][1]
    p_big = margin_probs[i][1]
    p_small = margin_probs[i][0]

    four_class_probs[i] = [
        p_a_wins * p_big,    # A_big
        p_a_wins * p_small,  # A_small
        p_b_wins * p_big,    # B_big
        p_b_wins * p_small   # B_small
    ]

# Normalize
four_class_probs = four_class_probs / four_class_probs.sum(axis=1, keepdims=True)

# True 4-class outcomes
y_true_4 = df[~train_mask]['outcome'].values
classes_4 = ['A_big', 'A_small', 'B_big', 'B_small']
four_class_preds = np.array(classes_4)[np.argmax(four_class_probs, axis=1)]

four_class_acc = accuracy_score(y_true_4, four_class_preds)
four_class_ll = log_loss(y_true_4, four_class_probs, labels=classes_4)

print("\n4-Class Results (for submission):")
print("  Validation Accuracy: %.2f%%" % (four_class_acc * 100))
print("  Log Loss: %.4f" % four_class_ll)

# Test predictions
print("\n" + "=" * 70)
print("TEST PREDICTIONS FOR HACKATHON MATCHES")
print("=" * 70)

def get_features(team_a, team_b, venue):
    ta_enc = team_le.transform([team_a])[0]
    tb_enc = team_le.transform([team_b])[0]
    v_enc = venue_le.transform([venue])[0]

    ts_a = team_stats.get(team_a, [0, 1, []])
    ts_b = team_stats.get(team_b, [0, 1, []])
    h2h_key = tuple(sorted([team_a, team_b]))
    h2h = h2h_stats.get(h2h_key, {ta: 0, 'total': 1, 'recent': []})
    vs_key = tuple(sorted([team_a, venue]))
    vs_venue = venue_stats.get(vs_key, {team_a: 0, 'total': 1})
    fs_a = form_stats.get(team_a, [])
    fs_b = form_stats.get(team_b, [])

    wr_a = ts_a[0] / ts_a[1]
    wr_b = ts_b[0] / ts_b[1]
    h2h_a = h2h.get(team_a, 0) / h2h['total']
    venue_a = vs_venue.get(team_a, 0) / vs_venue['total']
    recent_a = np.mean(fs_a[-5:]) if fs_a else 0.5
    recent_b = np.mean(fs_b[-5:]) if fs_b else 0.5
    momentum_a = get_momentum(team_a)
    momentum_b = get_momentum(team_b)

    streak_a = 0
    for w in reversed(fs_a[-10:]):
        if w == 1: streak_a += 1
        else: break
    streak_b = 0
    for w in reversed(fs_b[-10:]):
        if w == 1: streak_b += 1
        else: break

    return scaler.transform([[
        ta_enc, tb_enc, v_enc,
        wr_a, wr_b, h2h_a, venue_a,
        recent_a, recent_b, momentum_a, momentum_b,
        streak_a, streak_b,
        wr_a - wr_b, recent_a - recent_b, h2h_a - 0.5,
        momentum_a - momentum_b, streak_a - streak_b
    ]])

test_matches = [
    ('Sunrisers Hyderabad', 'Kolkata Knight Riders', 'Rajiv Gandhi International Stadium, Uppal, Hyderabad'),
    ('Gujarat Titans', 'Punjab Kings', 'Narendra Modi Stadium, Ahmedabad'),
    ('Mumbai Indians', 'Lucknow Super Giants', 'Wankhede Stadium, Mumbai'),
    ('Royal Challengers Bangalore', 'Delhi Capitals', 'M Chinnaswamy Stadium, Bengaluru'),
]

all_predictions = []

for team_a, team_b, venue in test_matches:
    print("\n%s vs %s" % (team_a, team_b))
    print("-" * 50)
    try:
        features = get_features(team_a, team_b, venue)

        # Get predictions from all models
        rf_prob = rf_cal.predict_proba(features)[0]
        gb_prob = gb_cal.predict_proba(features)[0]
        et_prob = et_cal.predict_proba(features)[0]
        lr_prob = lr_cal.predict_proba(features)[0]

        # Ensemble
        winner_prob = 0.3 * rf_prob + 0.3 * gb_prob + 0.25 * et_prob + 0.15 * lr_prob

        # Margin
        margin_prob = margin_model.predict_proba(features)[0]

        # Combine
        p_a_wins = winner_prob[0]
        p_b_wins = winner_prob[1]
        p_big = margin_prob[1]
        p_small = margin_prob[0]

        probs_4 = [
            p_a_wins * p_big,
            p_a_wins * p_small,
            p_b_wins * p_big,
            p_b_wins * p_small
        ]
        total = sum(probs_4)
        probs_4 = [p / total for p in probs_4]

        ts_a = team_stats.get(team_a, [0, 1])
        ts_b = team_stats.get(team_b, [0, 1])
        h2h_key = tuple(sorted([team_a, team_b]))
        h2h = h2h_stats.get(h2h_key, {'total': 0, team_a: 0})

        print("  Team A (%s) Win Rate: %.1f%%" % (team_a, ts_a[0]/ts_a[1]*100))
        print("  Team B (%s) Win Rate: %.1f%%" % (team_b, ts_b[0]/ts_b[1]*100))
        print("  H2H (last %d): %s=%.1f%%, %s=%.1f%%" % (
            h2h['total'], team_a, h2h.get(team_a, 0)/h2h['total']*100 if h2h['total'] > 0 else 50,
            team_b, h2h.get(team_b, 0)/h2h['total']*100 if h2h['total'] > 0 else 50))

        print("\n  4-Class Predictions:")
        for cls, prob in sorted(zip(classes_4, probs_4), key=lambda x: -x[1]):
            bar = '=' * int(prob * 50)
            print("    %s: %6.2f%% %s" % (cls, prob * 100, bar))

        all_predictions.append({
            'team_a': team_a,
            'team_b': team_b,
            'probs': dict(zip(classes_4, probs_4))
        })

    except Exception as e:
        print("  Error: %s" % e)

# Generate submission
print("\n" + "=" * 70)
print("GENERATING SUBMISSION FILE")
print("=" * 70)

targets = [
    ('Sunrisers Hyderabad', 'Kolkata Knight Riders', 'Rajiv Gandhi International Stadium, Uppal, Hyderabad', 'SRH_vs_KKR'),
    ('Gujarat Titans', 'Punjab Kings', 'Narendra Modi Stadium, Ahmedabad', 'GT_vs_PBKS'),
    ('Mumbai Indians', 'Lucknow Super Giants', 'Wankhede Stadium, Mumbai', 'MI_vs_LSG'),
]

rows = []
for team_a, team_b, venue, mid in targets:
    features = get_features(team_a, team_b, venue)

    rf_prob = rf_cal.predict_proba(features)[0]
    gb_prob = gb_cal.predict_proba(features)[0]
    et_prob = et_cal.predict_proba(features)[0]
    lr_prob = lr_cal.predict_proba(features)[0]

    winner_prob = 0.3 * rf_prob + 0.3 * gb_prob + 0.25 * et_prob + 0.15 * lr_prob
    margin_prob = margin_model.predict_proba(features)[0]

    probs_4 = [
        winner_prob[0] * margin_prob[1],
        winner_prob[0] * margin_prob[0],
        winner_prob[1] * margin_prob[1],
        winner_prob[1] * margin_prob[0]
    ]
    total = sum(probs_4)
    probs_4 = [p / total for p in probs_4]

    rows.append({
        'match_id': mid,
        'A_big': round(probs_4[0], 4),
        'A_small': round(probs_4[1], 4),
        'B_big': round(probs_4[2], 4),
        'B_small': round(probs_4[3], 4)
    })

sub_df = pd.DataFrame(rows)
sub_df.to_csv(r'c:\Users\rushi\OneDrive\Desktop\IPL prediction\submission.csv', index=False)

print("\nSubmission file generated: submission.csv")
print(sub_df.to_string(index=False))

# Overall Rating
print("\n" + "=" * 70)
print("FINAL SYSTEM RATING")
print("=" * 70)

# Binary accuracy (who wins)
binary_acc = ensemble_acc
binary_cv = cross_val_score(rf_cal, X_train, y_train, cv=5, scoring='accuracy').mean()
binary_ll = ensemble_ll

# 4-class accuracy
four_class_acc_val = four_class_acc
four_class_ll_val = four_class_ll

print("\nBinary Classification (Who Wins):")
print("  Validation Accuracy: %.2f%%" % (binary_acc * 100))
print("  Log Loss: %.4f" % binary_ll)
print("  5-Fold CV: %.2f%%" % (binary_cv * 100))

print("\n4-Class Classification (For Submission):")
print("  Validation Accuracy: %.2f%%" % (four_class_acc_val * 100))
print("  Log Loss: %.4f" % four_class_ll_val)

# Calculate rating (0-5 scale)
# For cricket: 55%+ binary accuracy is excellent
# For 4-class: 35%+ is excellent (random is 25%)

binary_rating = min(binary_acc / 0.55, 1.0) * 2.5
four_class_rating = min(four_class_acc_val / 0.35, 1.0) * 2.0
log_rating = max(0, (1.0 - binary_ll) / 1.0) * 0.5

overall_rating = binary_rating + four_class_rating + log_rating

print("\n" + "=" * 70)
print("COMPONENT RATINGS:")
print("  Binary Accuracy: %.2f / 2.50" % binary_rating)
print("  4-Class Accuracy: %.2f / 2.00" % four_class_rating)
print("  Log Loss Bonus: %.2f / 0.50" % log_rating)
print("=" * 70)
print("FINAL RATING: %.2f / 5.00" % overall_rating)
print("=" * 70)

if overall_rating >= 4.5:
    label = "EXCEPTIONAL"
elif overall_rating >= 4.0:
    label = "EXCELLENT"
elif overall_rating >= 3.0:
    label = "GOOD"
elif overall_rating >= 2.0:
    label = "MODERATE"
else:
    label = "NEEDS IMPROVEMENT"

print("\nLabel: %s" % label)
print("\n[TEST COMPLETE]")
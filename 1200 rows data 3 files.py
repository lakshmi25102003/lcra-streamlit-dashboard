import csv
import random
import pandas as pd
from datetime import datetime, timedelta

# ==========================================
# PART 1: CONFIGURATION
# ==========================================
FILE_PROJECTS = "LCRA_Advanced_Project_Budgets.csv"
FILE_TIMESHEETS = "LCRA_Timesheets_1200.csv"
FILE_STATUS = "LCRA_Project_Financial_Status.csv"

# Configuration
NUM_PROJECTS = 115
NUM_CLOSED = 45
NUM_ACTIVE = NUM_PROJECTS - NUM_CLOSED

# Timesheet Config
NUM_CONTRACTORS = 250
NUM_FIRMS = 15
ROW_LIMIT = 1200
# We assume "Today" is roughly Jan 2026 for this demo context
TS_WINDOW_START = datetime(2026, 1, 15) 

# ==========================================
# PART 2: GENERATE PROJECTS (Fixed Date Logic)
# ==========================================
print("--- Generating Projects & Budgets ---")

# 1. Define Durations (Weighted)
active_durations = []
# 60% of Active -> 35, 48, 90 days
for _ in range(int(NUM_ACTIVE * 0.60)): active_durations.append(random.choice([35, 48, 90]))
# 4% -> 120, 180
for _ in range(int(NUM_ACTIVE * 0.04)): active_durations.append(120)
for _ in range(int(NUM_ACTIVE * 0.04)): active_durations.append(180)
# Rest -> Mixed
remaining = NUM_ACTIVE - len(active_durations)
for _ in range(remaining): active_durations.append(random.choice([10, 18, 24, 60]))
random.shuffle(active_durations)

closed_durations = [random.choice([10, 18, 24, 35, 48, 60, 90, 120]) for _ in range(NUM_CLOSED)]

# 2. Assign Attributes
project_pool = []
managers = ["A. Patel", "L. Wang", "M. Garcia", "K. Jones", "J. Smith", "R. Dias", "T. Nguyen"]
sites = ["North", "South", "East", "West", "Central", "Metro", "Rural"]
types = ["Solar", "Wind", "Hydro", "Substation", "Grid", "Maintenance", "Compliance"]

# Helper for Budget
def get_budget(duration):
    if duration == 10: return random.randint(900_000, 1_100_000)
    if duration == 35: return random.randint(3_000_000, 4_500_000)
    if duration == 48: return random.randint(5_000_000, 8_000_000)
    if duration == 90: return random.randint(15_000_000, 22_000_000)
    if duration == 180: return random.randint(65_000_000, 75_000_000)
    return duration * 100000 + random.randint(0, 500000)

# Build Active Projects
for i, duration in enumerate(active_durations):
    # ACTIVE LOGIC: Must end in 2026 or later
    # Start date can be late 2025 or 2026
    start_date = datetime(2025, 9, 1) + timedelta(days=random.randint(0, 200))
    end_date = start_date + timedelta(days=duration)
    
    project_pool.append({
        "status": "Active", "duration": duration, 
        "start": start_date, "end": end_date
    })

# Build Closed Projects
for i, duration in enumerate(closed_durations):
    # CLOSED LOGIC: Must end in 2025 (Strictly)
    # End date between Jan 1, 2025 and Dec 31, 2025
    days_in_2025 = (datetime(2025, 12, 31) - datetime(2025, 1, 1)).days
    random_end_day = random.randint(0, days_in_2025)
    end_date = datetime(2025, 1, 1) + timedelta(days=random_end_day)
    start_date = end_date - timedelta(days=duration)
    
    project_pool.append({
        "status": "Closed", "duration": duration, 
        "start": start_date, "end": end_date
    })

random.shuffle(project_pool)

# Create DataFrame rows
proj_rows = []
# Pick "Intensive" 48-day projects ($55M)
indices_48 = [i for i, p in enumerate(project_pool) if p['duration'] == 48]
intensive_indices = random.sample(indices_48, k=min(len(indices_48), 3))

for i, p in enumerate(project_pool):
    prj_id = f"PRJ-{1000+i}"
    mgr = random.choice(managers)
    name = f"{random.choice(sites)} {random.choice(types)} Phase {random.randint(1,4)}"
    
    if i in intensive_indices:
        budget = random.randint(54_000_000, 56_000_000)
    else:
        budget = get_budget(p['duration'])

    proj_rows.append({
        "PROJECT_ID": prj_id, "PROJECT_NAME": name, "PROJECT_MANAGER": mgr,
        "START_DATE": p['start'].strftime("%d-%m-%Y"), 
        "END_DATE": p['end'].strftime("%d-%m-%Y"),
        "DURATION_DAYS": p['duration'], "TOTAL_BUDGET_USD": budget, "STATUS": p['status']
    })

df_projects = pd.DataFrame(proj_rows)
df_projects.to_csv(FILE_PROJECTS, index=False)
print(f"Created {FILE_PROJECTS} ({len(df_projects)} projects)")

# ==========================================
# PART 3: GENERATE TIMESHEETS (1200 Rows)
# ==========================================
print("--- Generating Timesheets ---")

firms = [f"Consulting_Firm_{i+1}" for i in range(NUM_FIRMS)]

contractors = []
for i in range(NUM_CONTRACTORS):
    contractors.append({
        "EMPLID": f"C{50000+i}",
        "NAME": f"Consultant_{i+1}",
        "FIRM": random.choice(firms),
        "RATE": random.choice([150, 185, 225, 275, 350, 450])
    })

timesheet_rows = []
project_current_spend_map = {pid: 0 for pid in df_projects['PROJECT_ID']}

for _ in range(ROW_LIMIT):
    c = random.choice(contractors)

    # Prefer Active projects
    if random.random() > 0.1:
        valid_projects = df_projects[df_projects['STATUS'] == 'Active']['PROJECT_ID'].tolist()
    else:
        valid_projects = df_projects['PROJECT_ID'].tolist()

    pid = random.choice(valid_projects)

    is_ot = random.random() < 0.20

    # ✅ HOURS → ONLY 2 DECIMALS
    hours = round(
        random.uniform(8.5, 12.0), 2
    ) if is_ot else round(
        random.uniform(4.0, 8.0), 2
    )

    rate_mult = 1.5 if is_ot else 1.0
    trc = "OT" if is_ot else "REG"

    # TOTAL_COST unchanged
    cost = hours * c["RATE"] * rate_mult

    project_current_spend_map[pid] = project_current_spend_map.get(pid, 0) + cost

    timesheet_rows.append({
        "EMPLID": c["EMPLID"],
        "NAME": c["NAME"],
        "FIRM": c["FIRM"],
        "PROJECT_ID": pid,
        "WORK_DATE": "2026-01-05",   # ✅ FIXED DATE WITH YEAR
        "TRC": trc,
        "HOURS": hours,              # ✅ 2 DECIMALS
        "BILL_RATE": c["RATE"],
        "TOTAL_COST": cost
    })

# -------------------------------
# CREATE DATAFRAME
# -------------------------------
df_ts = pd.DataFrame(timesheet_rows)

# 🔴 IMPORTANT FIX: FORCE YYYY-MM-DD (YEAR WILL NOT DROP)
df_ts["WORK_DATE"] = pd.to_datetime(df_ts["WORK_DATE"]).dt.strftime("%Y-%m-%d")

# -------------------------------
# SAVE CSV
# -------------------------------
df_ts.to_csv(FILE_TIMESHEETS, index=False)

print(f"Created {FILE_TIMESHEETS} ({len(df_ts)} rows)")

# ==========================================
# PART 4: GENERATE FINANCIAL STATUS
# ==========================================
print("--- Generating Project Status (Burn Logic) ---")
status_rows = []

# Select Targets for Narrative
active_ids = df_projects[df_projects['STATUS'] == 'Active']['PROJECT_ID'].tolist()
closed_ids = df_projects[df_projects['STATUS'] == 'Closed']['PROJECT_ID'].tolist()
random.shuffle(active_ids)
random.shuffle(closed_ids)

over_ids = active_ids[:3]        # 3 Active Over
near_ids = active_ids[3:11]      # 8 Active Near
closed_over_ids = closed_ids[:14] # 14 Closed Overruns

for _, row in df_projects.iterrows():
    pid = row['PROJECT_ID']
    budget = row['TOTAL_BUDGET_USD']
    current = project_current_spend_map.get(pid, 0)
    
    # Calculate Prior Spend to match desired Total Status
    if pid in over_ids: target_pct = random.uniform(1.05, 1.20)
    elif pid in near_ids: target_pct = random.uniform(0.92, 0.98)
    elif pid in closed_over_ids: target_pct = random.uniform(1.02, 1.15)
    elif row['STATUS'] == 'Closed': target_pct = random.uniform(0.70, 0.95)
    else: target_pct = random.uniform(0.10, 0.85)
    
    target_total = budget * target_pct
    prior = max(0, target_total - current)
    
    status_rows.append({
        "PROJECT_ID": pid, "PROJECT_NAME": row['PROJECT_NAME'], "STATUS": row['STATUS'],
        "TOTAL_BUDGET": budget, "PRIOR_SPEND": round(prior, 2),
        "CURRENT_TIMESHEET_SPEND": round(current, 2),
        "TOTAL_SPEND": round(prior + current, 2),
        "PERCENT_USED": round(((prior + current)/budget)*100, 1)
    })

df_status = pd.DataFrame(status_rows)
df_status.sort_values(by=["STATUS", "PERCENT_USED"], ascending=[True, False], inplace=True)
df_status.to_csv(FILE_STATUS, index=False)
print(f"Created {FILE_STATUS} ({len(df_status)} rows)")
print("DONE.")
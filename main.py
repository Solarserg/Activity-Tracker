# ============================================================
# Daily Activity Tracker
# ============================================================
# This app lets you check off your daily habits, saves your
# progress to a CSV file, and shows a dashboard with your
# monthly completion rates.
#
# To run this app, type in your terminal:
#   streamlit run main.py
# ============================================================

# --- IMPORTS ---
# We import the tools (libraries) that this program needs.

import streamlit as st  # Builds the interactive web app
import pandas as pd     # Works with tables of data (like Excel in Python)
import os               # Lets us check whether files exist on disk
from datetime import date, timedelta  # Gives us today's date and date arithmetic

# ============================================================
# CONFIGURATION
# ============================================================
# Edit these two constants to personalise the tracker.

# The file where all your activity data will be saved.
# It lives in the same folder as this script.
ACTIVITY_LOG = "activity_log.csv"

# The list of daily habits you want to track.
# Add, remove, or rename items here — the rest of the app
# adapts automatically.
ACTIVITIES = [
    "Sleep 7+ hours",
    "Daily Mass",
    "15 min Structured Prayer",
    "15 min Mental Prayer",
    "Social Activity or 15 min Call",
    "60 min Reading",
    "Bands Exercise",
    "15 min Walk",
    "Cardio/Strength HIIT",
    "30 min Russian",
    "2 hr Coding",
    "No Fast-food",
    "No Alcohol",
    "No Nicotine or Marijuana",
    "No Naproxen",
    "No Caffeine",
    "No Video Games",
]

# ============================================================
# DATA FUNCTIONS
# These functions handle loading and saving your data.
# ============================================================

def load_data():
    """
    Load saved activity data from the CSV file.

    A CSV file is a simple text file that stores data in rows
    and columns (like a spreadsheet).  If the file doesn't
    exist yet, this function returns an empty table.
    """
    if not os.path.exists(ACTIVITY_LOG):
        return pd.DataFrame(columns=["date"] + ACTIVITIES)

    df = pd.read_csv(ACTIVITY_LOG)

    # The 'date' column is stored as plain text in the file.
    # We convert it to real date objects so Python can
    # compare and sort dates properly.
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df

def save_entry(entry_date, activity_results):
    """
    Save (or update) one day's worth of activity data.

    Parameters
    ----------
    entry_date      : the date being saved, e.g. today's date
    activity_results: a dictionary mapping each activity name
                      to True (done) or False (not done),
                      e.g. {"Exercise": True, "Read": False, …}
    """
    df = load_data()

    # Build the new row we want to store.
    # We start with the date and then add every activity result.
    new_row = {"date": entry_date}
    new_row.update(activity_results)

    # Check whether today's date already exists in the file
    # so we can update it rather than add a duplicate row.
    if len(df) > 0 and entry_date in df["date"].values:
        # Update each activity column for the matching row.
        for activity, done in activity_results.items():
            df.loc[df["date"] == entry_date, activity] = done
    else:
        # No entry for this date yet — append a brand new row.
        # pd.concat joins two DataFrames together vertically.
        new_df = pd.DataFrame([new_row])
        df = pd.concat([df, new_df], ignore_index=True)

    # Write the updated DataFrame back to the CSV file.
    # index=False stops pandas from adding a useless row-number column.
    df.to_csv(ACTIVITY_LOG, index=False)


def get_todays_entry(df):
    """
    Return the row for today if one already exists, or None if not.

    This lets the Log page pre-fill the checkboxes when the user
    comes back to update their entry.
    """
    today = date.today()
    if len(df) > 0 and today in df["date"].values:
        # .iloc[0] picks the first (and only) matching row.
        return df[df["date"] == today].iloc[0]
    return None


def calculate_streak(df, activity):
    """
    Count how many consecutive calendar days (ending on the most
    recent logged entry) an activity was completed without a break.

    The streak resets to 0 the moment we find either:
      - a logged day where the activity was NOT completed, or
      - a gap of more than one calendar day between entries.

    Example: if the log shows Mon=True, Tue=True, Wed=False,
    the streak is 0 because the most recent entry (Wed) was False.
    """
    if df.empty or activity not in df.columns:
        return 0

    # Sort entries newest-first so we walk backwards through time.
    sorted_df = df.sort_values("date", ascending=False).reset_index(drop=True)

    streak = 0
    prev_date = None

    for _, row in sorted_df.iterrows():
        # Ensure we have a plain date object (not a datetime).
        row_date = row["date"].date() if hasattr(row["date"], "date") else row["date"]

        if prev_date is not None:
            # If this entry is not exactly one day before the previous one,
            # there is a gap in the log and the streak is broken.
            if (prev_date - row_date).days != 1:
                break

        if row[activity]:
            streak += 1
            prev_date = row_date
        else:
            # Activity was logged but marked as not done — streak ends.
            break

    return streak


# ============================================================
# PAGE: LOG TODAY
# ============================================================

def show_log_page():
    """
    The 'Log Today' page.

    Shows one checkbox per activity.  When the user clicks
    'Save', their choices are written to the CSV file.
    """
    st.header("Daily Activity Log")

    today = date.today()
    # strftime formats a date as text; %A = full weekday name,
    # %B = full month name, %d = day number, %Y = 4-digit year.
    st.write(f"**{today.strftime('%A, %B %d, %Y')}**")

    # Load saved data so we can check for an existing entry.
    df = load_data()
    existing = get_todays_entry(df)

    if existing is not None:
        st.info("You've already logged today — update your entries below and save again.")

    st.write("Check every activity you completed today:")
    st.write("---")

    # Loop through each activity and draw a checkbox for it.
    # We store every checkbox result in a dictionary called
    # activity_results so we can save it all at once.
    activity_results = {}
    for activity in ACTIVITIES:
        # If there is an existing entry, pre-tick the checkbox
        # with the value that was saved earlier.
        default = bool(existing.get(activity, False)) if existing is not None else False
        # st.checkbox returns True when ticked, False when not.
        activity_results[activity] = st.checkbox(activity, value=default)

    st.write("---")

    # Count completed activities for the summary line.
    completed_count = sum(activity_results.values())
    total_count = len(ACTIVITIES)
    st.write(f"**Completed today: {completed_count} / {total_count}**")

    # Draw the Save button.  type="primary" makes it stand out.
    if st.button("Save Today's Log", type="primary"):
        save_entry(today, activity_results)
        st.success(f"Saved!  You completed {completed_count} of {total_count} activities today.")
        if completed_count == total_count:
            st.balloons()  # Celebrate a perfect day!


# ============================================================
# PAGE: DASHBOARD
# ============================================================

def show_dashboard_page():
    """
    The 'Dashboard' page.

    Lets the user pick a month and displays how often each
    activity was completed as a percentage and a bar chart.
    """
    st.header("Monthly Dashboard")

    df = load_data()

    # Guard: if no data exists yet, tell the user what to do.
    if df.empty:
        st.info("No data yet!  Go to 'Log Today' to start tracking.")
        return

    # Convert the date column to pandas datetime so we can
    # extract the year and month from each date.
    df["date"] = pd.to_datetime(df["date"])

    # Create a 'year_month' column that looks like "2025-01".
    # pd.Period groups dates into monthly buckets.
    df["year_month"] = df["date"].dt.to_period("M").astype(str)

    # Get the list of months that have at least one entry,
    # sorted newest first so the current month appears first.
    available_months = sorted(df["year_month"].unique(), reverse=True)

    # Drop-down selector so the user can pick any recorded month.
    # format_func converts "2025-01" into a human-readable "January 2025".
    selected_month = st.selectbox(
        "Select month:",
        options=available_months,
        format_func=lambda m: pd.Period(m).strftime("%B %Y"),
    )

    # Filter the DataFrame down to only the selected month.
    month_df = df[df["year_month"] == selected_month].copy()

    # Work out how many calendar days are in the chosen month
    # (28 / 29 / 30 / 31 depending on the month and year).
    period = pd.Period(selected_month)
    days_in_month = period.days_in_month
    days_logged = len(month_df)

    # Determine the denominator for completion percentages.
    # - Current month: use today's day number so the rate reflects
    #   "month to date" (e.g. 7 days elapsed if today is the 7th).
    # - Past months: use the full number of days in that month.
    today = date.today()
    current_month_str = pd.Period(today, freq="M").strftime("%Y-%m")
    if selected_month == current_month_str:
        days_elapsed = today.day
        denominator_label = f"day 1 – {today.strftime('%b %d')} ({days_elapsed} days elapsed)"
    else:
        days_elapsed = days_in_month
        denominator_label = f"full month ({days_in_month} days)"

    st.write(
        f"**{period.strftime('%B %Y')}** — "
        f"{days_logged} day(s) logged · rate calculated over {denominator_label}"
    )
    st.write("---")

    # --- Build percentage data ---
    # For each activity we calculate:
    #   percentage = (days the activity was done / days elapsed) × 100
    #
    # For the current month 'days elapsed' is today's day-of-month so the
    # chart shows a true month-to-date rate.  For past months it is the
    # full length of the month.
    percentages = {}
    for activity in ACTIVITIES:
        if activity in month_df.columns:
            # .sum() on a True/False column counts the number of True values.
            days_done = int(month_df[activity].sum())
            pct = round(days_done / days_elapsed * 100, 1)
            percentages[activity] = {"days_done": days_done, "pct": pct}

    # --- Compute streaks ---
    # A streak is the number of consecutive calendar days (ending on the
    # most recent logged entry) where the activity was completed.
    # We use the full dataset (df), not just the selected month, so a streak
    # that started last month is counted correctly.
    streaks = {
        activity: calculate_streak(df, activity)
        for activity in ACTIVITIES
        if activity in df.columns
    }

    # --- Progress bars ---
    # Each row shows: activity name | progress bar | % | streak
    st.markdown(
        "<div style='display:flex; font-size:0.75rem; color:grey; "
        "padding-bottom:4px'>"
        "<span style='flex:3'>Activity</span>"
        "<span style='flex:4'></span>"
        "<span style='flex:1; text-align:right'>Rate</span>"
        "<span style='flex:1.5; text-align:right'>Streak</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    for activity, data in percentages.items():
        col_label, col_bar, col_pct, col_streak = st.columns([3, 4, 1, 1])
        with col_label:
            st.write(activity)
        with col_bar:
            # st.progress expects a value between 0.0 and 1.0.
            st.progress(data["pct"] / 100)
        with col_pct:
            st.write(f"**{data['pct']}%**")
        with col_streak:
            n = streaks.get(activity, 0)
            # Show the streak number; grey dash when there is no active streak.
            if n > 0:
                st.write(f"**{n}d**")
            else:
                st.write("—")

    st.write("---")

    # --- Bar chart ---
    # Build a small DataFrame just for the chart and display it.
    st.subheader("Completion Rate Chart")
    chart_df = pd.DataFrame(
        {
            "Activity": list(percentages.keys()),
            "Completion %": [v["pct"] for v in percentages.values()],
        }
    ).set_index("Activity")

    st.bar_chart(chart_df)

    # --- Raw data table (hidden by default) ---
    # st.expander hides content behind a clickable header to keep
    # the page tidy.  The user can expand it if they want the detail.
    with st.expander("View raw data for this month"):
        display_df = month_df.drop(columns=["year_month"])
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(display_df.reset_index(drop=True), use_container_width=True)


# ============================================================
# MAIN — app entry point
# ============================================================

def main():
    """
    Sets up the page layout and routes between the two pages.
    Streamlit calls this function every time the user interacts
    with the app.
    """
    # Configure the browser tab title, icon, and layout width.
    st.set_page_config(
        page_title="Daily Activity Tracker",
        page_icon="✅",
        layout="centered",
    )

    st.title("✅ Daily Activity Tracker")

    # The sidebar is the thin panel on the left side of the page.
    # We put navigation there so it doesn't clutter the main area.
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to:",
        options=["Log Today", "Dashboard"],
    )

    # Show the correct page based on the user's selection.
    if page == "Log Today":
        show_log_page()
    else:
        show_dashboard_page()


# ============================================================
# This is the standard Python way to say:
# "Only run main() if this file is being run directly —
#  not if it's being imported by another script."
# Streamlit calls this file directly, so main() will run.
# ============================================================
if __name__ == "__main__":
    main()

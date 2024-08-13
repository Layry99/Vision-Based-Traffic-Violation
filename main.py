from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta, date
from dateutil.parser import parse as parse_date
import sqlite3
import io
import pandas as pd
import plotly.graph_objs as go

app = FastAPI()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")


def get_image_from_db(image_id):
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT image, timestamp FROM violations WHERE id=?", (image_id,))
    record = cursor.fetchone()
    conn.close()
    if record is None:
        return None, None
    return record[0], record[1]


def get_all_images():
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM violations")
    image_records = cursor.fetchall()
    conn.close()
    return image_records


def get_images_by_date(selected_date):
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM violations WHERE DATE(timestamp)=?", (selected_date,))
    image_records = cursor.fetchall()
    conn.close()
    return image_records


def get_images_last_month():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM violations WHERE DATE(timestamp) BETWEEN ? AND ?",
                   (start_date, end_date))
    image_records = cursor.fetchall()
    conn.close()
    return image_records


def get_images_last_week():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM violations WHERE DATE(timestamp) BETWEEN ? AND ?",
                   (start_date, end_date))
    image_records = cursor.fetchall()
    conn.close()
    return image_records


def get_images_last_day():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=1)
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM violations WHERE DATE(timestamp) BETWEEN ? AND ?",
                   (start_date, end_date))
    image_records = cursor.fetchall()
    conn.close()
    return image_records


def get_images_today():
    today = datetime.now().date()
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM violations WHERE DATE(timestamp)=?", (today,))
    image_records = cursor.fetchall()
    conn.close()
    return image_records


def get_total_violations():
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM violations")
    total_violations = cursor.fetchone()[0]
    conn.close()
    return total_violations


def get_max_violations_per_day():
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM violations GROUP BY DATE(timestamp) ORDER BY COUNT(id) DESC LIMIT 1")
    max_violations = cursor.fetchone()
    if max_violations:
        return max_violations[0]
    return 0


def get_min_violations_per_day():
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM violations GROUP BY DATE(timestamp) ORDER BY COUNT(id) ASC LIMIT 1")
    min_violations = cursor.fetchone()
    if min_violations:
        return min_violations[0]
    return 0


def get_avg_violations_per_day():
    conn = sqlite3.connect('violation-database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT AVG(daily_count) FROM (SELECT COUNT(id) as daily_count FROM violations GROUP BY DATE(timestamp))")
    avg_violations = cursor.fetchone()[0]
    conn.close()
    if avg_violations:
        return round(avg_violations, 2)  # Round to two decimal places
    return 0


def get_violations_timeline():
    conn = sqlite3.connect('violation-database.db')
    query = "SELECT DATE(timestamp) as date, COUNT(id) as num_violations FROM violations GROUP BY DATE(timestamp)"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_top_violation_days(limit=3):
    conn = sqlite3.connect('violation-database.db')
    query = """
    SELECT STRFTIME('%w', timestamp) as day_of_week, COUNT(id) as num_violations
    FROM violations
    GROUP BY day_of_week
    ORDER BY num_violations DESC
    LIMIT ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    top_days = cursor.fetchall()
    conn.close()

    # Convert day_of_week from number to name
    day_name_mapping = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    top_days = [(day_name_mapping[int(day)], count) for day, count in top_days]

    return top_days


def get_top_violation_hours(limit=3):
    conn = sqlite3.connect('violation-database.db')
    query = """
    SELECT STRFTIME('%H', timestamp) as hour, COUNT(id) as num_violations
    FROM violations
    GROUP BY hour
    ORDER BY num_violations DESC
    LIMIT ?
    """
    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    top_hours = cursor.fetchall()
    conn.close()

    # Format hours to be within 1 hour range
    top_hours = [(f"{int(hour):02d}:00 - {int(hour):02d}:59", count) for hour, count in top_hours]

    return top_hours


@app.get("/image/{image_id}")
async def get_image(image_id: int):
    image_data, _ = get_image_from_db(image_id)
    if image_data is None:
        raise HTTPException(status_code=404, detail="Image not found")

    return StreamingResponse(io.BytesIO(image_data), media_type="image/jpeg")


@app.get("/")
async def index(request: Request, selected_date: str = None, filter_type: str = None):
    # Fetch images based on selected filter type or date
    if filter_type == "all":
        image_records = get_all_images()
    elif filter_type == "last_month":
        image_records = get_images_last_month()
    elif filter_type == "last_week":
        image_records = get_images_last_week()
    elif filter_type == "last_day":
        image_records = get_images_last_day()
    elif filter_type == "today":
        image_records = get_images_today()
    elif selected_date:
        try:
            parsed_date = parse_date(selected_date).date()
            image_records = get_images_by_date(parsed_date)
        except ValueError:
            image_records = []
    else:
        image_records = get_all_images()  # Default to showing all images

    # Prepare a list of dictionaries containing id and timestamp for each image
    image_data = []
    for image_id, timestamp in image_records:
        image_data.append({"id": image_id, "timestamp": timestamp})

    # Flag to indicate if no records were found for the selected date
    no_records_found = len(image_data) == 0

    # Statistics
    total_violations = get_total_violations()
    max_violations = get_max_violations_per_day()
    min_violations = get_min_violations_per_day()
    avg_violations = get_avg_violations_per_day()

    # Violations Timeline for Chart
    df = get_violations_timeline()
    if not df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['date'], y=df['num_violations'], mode='lines+markers'))
        fig.update_layout(
            title='Violations Over Time',
            xaxis_title='Date',
            yaxis_title='Number of Violations',
            xaxis_rangeslider_visible=True
        )
        chart = fig.to_html(full_html=False)
    else:
        chart = None

    # Top Violations Days Pie Chart
    top_days_data = get_top_violation_days()
    if top_days_data:
        labels = [f"{day[0]} (Rank: {idx + 1}, Violations: {day[1]})" for idx, day in enumerate(top_days_data)]
        values = [day[1] for day in top_days_data]
        fig_top_days = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig_top_days.update_layout(title='Top Violations Days')
        top_days_chart = fig_top_days.to_html(full_html=False)
    else:
        top_days_chart = None

    # Top Violations Hours Pie Chart
    top_hours_data = get_top_violation_hours()
    if top_hours_data:
        labels = [f"{hour[0]} (Rank: {idx + 1}, Violations: {hour[1]})" for idx, hour in enumerate(top_hours_data)]
        values = [hour[1] for hour in top_hours_data]
        fig_top_hours = go.Figure(data=[go.Pie(labels=labels, values=values)])
        fig_top_hours.update_layout(title='Top Violations Hours')
        top_hours_chart = fig_top_hours.to_html(full_html=False)
    else:
        top_hours_chart = None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "image_data": image_data,
        "no_records_found": no_records_found,  # Pass the flag to the template
        "total_violations": total_violations,
        "max_violations": max_violations,
        "min_violations": min_violations,
        "avg_violations": avg_violations,
        "chart": chart,
        "top_days_chart": top_days_chart,
        "top_hours_chart": top_hours_chart
    })


app.mount("/static", StaticFiles(directory="static"), name="static")
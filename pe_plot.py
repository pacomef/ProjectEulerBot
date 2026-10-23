from typing import Optional

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import math

import pe_api
import pe_image
import pe_global_objects as pe_global
import pe_setup

import datetime
import pytz
import time

import os
import glob
import shutil

import asyncio

import locale


# Called when started
def graph_start():
    pio.templates.default = "plotly"


def _github_grid_rows(total_days: int, target_ratio: float = 3.0) -> int:
    """Round the grid height up to the next multiple of 7 rows."""
    base_rows = max(1, math.ceil(math.sqrt(total_days / target_ratio)))
    return int(math.ceil(base_rows / 7) * 7)
    
    
def project_euler_date_converter(s: str):
    minimal_date = datetime.datetime(1980, 1, 1, 0, 0, 0)
    project_euler_time_format = "%d %b %y (%H:%M)"
    # print(datetime.datetime.strftime(datetime.datetime.now(), project_euler_time_format))
    if "date" in s:
        return minimal_date
    else:
        try:
            return datetime.datetime.strptime(s, project_euler_time_format)
        except:
            changes = [(m, m.lower() + ".") for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]]
            for change in changes:
                s = s.replace(change[0], change[1])
            return datetime.datetime.strptime(s, project_euler_time_format)
            


# Return a graph of the last solves during the last 'day_counts' days.
def graph_solves(day_counts: int, local: bool, smoothing = 1):

    save_location = "graphs/solves_figure.png"

    database_format = "%Y-%m-%d"
    output_format = "%Y-%m-%d"

    if local is True:

        data = pe_api.get_solves_in_database()
        data_len = day_counts + 1

        current_day = datetime.datetime.now(pytz.utc)
        days_list = [(current_day - datetime.timedelta(days=x)).strftime(output_format) for x in range(data_len)]

        counts = {day: 0 for day in days_list}

        for element in data:
            day_as_key = datetime.datetime.strptime(element["solve_date"].split()[0], database_format).strftime(output_format)
            if day_as_key in counts:
                counts[day_as_key] += 1

    else:

        data: list = pe_api.get_global_solves_in_database()
        minimum_day = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=day_counts)

        filtered_data = []

        for element in data:
            
            d = datetime.datetime.strptime(element["date_stat"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
            if d >= minimum_day:
                filtered_data.append({"date_stat": element["date_stat"], "solves": element["solves"]}) 

        data_len = len(filtered_data)

        days_list = [element["date_stat"] for element in filtered_data]
        counts = {element["date_stat"]: element["solves"] for element in filtered_data}
        

    plot_data = sorted(zip(map(datetime.datetime.fromisoformat, days_list), counts.values()))

    plt.style.use("ggplot")
    plt.cla()
    plt.title("Solves versus time")
    plt.plot(*zip(*plot_data))
    plt.gcf().autofmt_xdate()
    plt.savefig(save_location, bbox_inches="tight")
    return save_location



def format_data_for_individual_graph(file_content: str, username: str) -> list:
    
    seperator = ","
    path = f"graphs/{username}/"

    try:
        locale.setlocale(locale.LC_TIME, "en_US")
    except Exception as e:
        pass

    try:
        os.mkdir(path)
    except:
        files = glob.glob(path + "*")
        for f in files:
            os.remove(f)

    new_file_content = file_content.split("\n")
    
    # Remove \r at end of lines
    lines = list(map(lambda line: line.replace("\r", ""), new_file_content))

    solves = list(map(lambda l: l.split(seperator), lines))

    # Remove blank lines
    solves = list(filter(lambda element: len(element) > 1, solves))

    # Not showing up bonus problems for now
    solves = list(filter(lambda element: element[0][0] != "B", solves))

    for i in range(len(solves)):
        solves[i][1] = str(solves[i][1])
        # print(solves[i])
        solves[i] = [int(solves[i][0]), project_euler_date_converter(solves[i][-1])]
    solves = solves[::-1]
    
    return solves




async def generate_individual_graph(file_content: str, username: str) -> Optional[str]:
    
    minimal_date = datetime.datetime(1980, 1, 1, 0, 0, 0)
    solves = format_data_for_individual_graph(file_content, username)
    
    frame_count = 100
    additional_frame_count = 25

    temp_epsilon = 1000

    starting_timestamp = list(filter(
        lambda el: el[1].timestamp() - temp_epsilon > minimal_date.timestamp(), 
        solves
    ))[0][1].timestamp()

    difference = solves[-1][1].timestamp() - starting_timestamp + temp_epsilon

    try:
        problems = (await pe_api.problems_list())[1:-1]
    except Exception as _:
        return None

    for percentage in range(frame_count + 1):
        
        current_timestamp = starting_timestamp + difference * percentage / frame_count
        last_pb = len(list(filter(lambda el: pe_global.pe_unix_from_time(el[2]) < current_timestamp, problems)))
        
        pe_image.image_for_timestamp_user_solve(
            solves, current_timestamp, username, percentage, 
            frame_count, percentage, last_pb
        )

    for addition in range(1, additional_frame_count + 1):
        
        current_timestamp = starting_timestamp + difference
        last_pb = len(problems)

        pe_image.image_for_timestamp_user_solve(
            solves, current_timestamp, username, frame_count, 
            frame_count, frame_count + addition, last_pb
        )

    pe_image.concatenate_image_gif(username)

    return f"graphs/{username}/{username}.gif"


def generate_simple_individual_graph(solves, username):
    
    # solves = format_data_for_individual_graph(file_content, username)
    
    solve_times = []
    solve_count = 0
    
    minimal_date = datetime.datetime(1980, 1, 1, 0, 0, 0)
    temp_epsilon = 1000
    
    for solve in solves:
        solve_count += 1
        if solve[1].timestamp() - temp_epsilon > minimal_date.timestamp():
            solve_times.append([solve_count, solve[1]])

    counts = [s[0] for s in solve_times]
    times = [s[1] for s in solve_times]

    save_path = f"graphs/{username}/{username}-linear-plot.png"

    plt.cla()

    plt.style.use('ggplot')
    plt.title("Solves versus time")

    plt.plot(times, counts)    
    plt.gcf().autofmt_xdate()
    
    plt.savefig(save_path, bbox_inches='tight')
    
    return save_path
 


async def generate_graph_monthly(member: pe_api.Member) -> str:
    r = await member.solves_by_csv(True)
    username = await member.username_option()
    
    # 1. Process dates
    df = pd.DataFrame([{"date": datetime.datetime.fromtimestamp(s.unixtime())} for s in r]).sort_values(by="date")
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    
    # 2. Fill empty months and calculate cumulative solves
    df_months = pd.DataFrame({'month': pd.date_range(start=df['month'].min(), end=df['month'].max(), freq='MS')})
    df_months = df_months.merge(df.groupby('month').size().reset_index(name='monthly'), on='month', how='left').fillna(0)
    df_months['cumulative'] = df_months['monthly'].cumsum()

    # 3. Build the plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_months['month'], y=df_months['monthly'], marker_color='rgba(150,150,150,0.4)'), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_months['month'], y=df_months['cumulative'], mode='lines', line=dict(color='#d62728', width=4)), secondary_y=True)
    
    fig.update_layout(
        title=dict(text=f"Monthly and Cumulative Solves - {username}", font=dict(size=24)),
        plot_bgcolor='#f0f0f0',         # Inner graph area (light gray)
        paper_bgcolor='white',          # Outer margins (solid white)
        showlegend=False, 
        bargap=0.1,
        width=1200,
        height=600,
        margin=dict(l=20, r=20, t=60, b=20) 
    )
    
    # Add white grid lines for the X-axis (vertical lines)
    fig.update_xaxes(showgrid=True, gridcolor='white', gridwidth=1.5)
    
    # Add white grid lines for the primary Y-axis (horizontal lines)
    fig.update_yaxes(title_text="Monthly Solves", showgrid=True, gridcolor='white', gridwidth=1.5, secondary_y=False)
    
    # Keep the secondary Y-axis grid off to prevent messy overlapping lines
    fig.update_yaxes(title_text="Cumulative Solves", showgrid=False, secondary_y=True)
    
    # 4. Save and return path
    filename = f"images_saves/{member._username}_graph_monthly.png" 
    fig.write_image(filename, scale=2) 
    
    return filename



async def generate_graph_github(member: pe_api.Member) -> str:
    r = await member.solves_by_csv(True)
    username = await member.username_option()
    
    # 1. Process dates and build continuous timeline
    dates = [datetime.datetime.fromtimestamp(s.unixtime()).date() for s in r]
    df = pd.DataFrame({'date': pd.date_range(start=min(dates), end=max(dates), freq='D')})
    
    # Count solves and merge
    solve_counts = pd.Series(dates).value_counts().reset_index()
    solve_counts.columns = ['date', 'solves']
    df['date'] = df['date'].dt.date
    df = df.merge(solve_counts, on='date', how='left').fillna({'solves': 0})
    
    # 2. Grid Math (Target Aspect Ratio 3:1)
    num_rows = _github_grid_rows(len(df))
    df['x_index'] = df.index // num_rows
    df['y_index'] = df.index % num_rows
    
    # 3. Locate years for X-axis labels
    df['year'] = pd.to_datetime(df['date']).dt.year
    years = df.drop_duplicates(subset=['year'])
    
    # 4. Build the plot
    heatmap = df.pivot(index='y_index', columns='x_index', values='solves')
    heatmap = heatmap.reindex(index=range(num_rows), fill_value=0)
    colors = [[0.0, '#ebedf0'], [0.01, '#9be9a8'], [0.33, '#40c463'], [0.66, '#30a14e'], [1.0, '#216e39']]
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap.values, x=heatmap.columns, y=heatmap.index,
        colorscale=colors, xgap=2, ygap=2, showscale=False, hoverongaps=False
    ))
    
    fig.update_layout(
        title=dict(text=f"Solve Activity - {username}", font=dict(size=24)),
        plot_bgcolor='white', 
        paper_bgcolor='white',
        width=1200, height=500, # Adjusted height for the 3:1 ratio
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(
            showgrid=False, zeroline=False, side='top', ticks="", constrain="domain",
            tickmode='array', tickvals=years['x_index'].tolist(), ticktext=years['year'].astype(str).tolist()
        ),
        yaxis=dict(
            autorange="reversed", showgrid=False, zeroline=False, showticklabels=False, 
            scaleanchor="x", scaleratio=1, constrain="domain" # Forces perfect squares
        )
    )
    
    # 5. Save and return path
    filename = f"images_saves/{member._username}_graph_github.png"
    fig.write_image(filename, scale=2)
    
    return filename


async def generate_graph_difficulty(member: pe_api.Member) -> str:
    r = await member.solves_by_csv(True)
    username = await member.username_option()
    
    # 1. Process dates and fetch difficulties asynchronously
    data = []
    for s in r:
        diff = await s.problem().difficulty()
        data.append({
            "date": datetime.datetime.fromtimestamp(s.unixtime()),
            "difficulty": diff if diff is not None else 0
        })
        
    df = pd.DataFrame(data).sort_values(by="date").reset_index(drop=True)
    
    # 2. Smooth by a rolling average of the last 20 solves
    df['smoothed_diff'] = df['difficulty'].rolling(window=20, min_periods=1).mean()
    
    # 3. Build the plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['smoothed_diff'], 
        mode='lines', line=dict(color='#ff7f0e', width=4) # Just the solid orange line
    ))
    
    fig.update_layout(
        title=dict(text=f"Average Difficulty Progression (Rolling 20 Solves) - {username}", font=dict(size=24)),
        plot_bgcolor='#f0f0f0',         # Inner graph area (light gray)
        paper_bgcolor='white',          # Outer margins (solid white)
        width=1200, height=600,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False
    )
    
    # Add the white gridlines to match the monthly graph
    fig.update_xaxes(showgrid=True, gridcolor='white', gridwidth=1.5)
    fig.update_yaxes(title_text="Difficulty level", showgrid=True, gridcolor='white', gridwidth=1.5, rangemode='tozero')
    
    # 4. Save and return path
    filename = f"images_saves/{member._username}_graph_difficulty.png"
    fig.write_image(filename, scale=2)
    
    return filename


BEST_SOLVERS_CRITERIA = [
    "Number of solves",
    "Sum of the difficulty levels of the solves (a level 0 problem adds 0, a level 40 adds 40)",
    "Average difficulty level of the solves (only members with at least 3 rated solves)",
    "Number of solves made among the first 100 solvers of the problem",
]

# (legend name, highest level of the bucket, color), the difficulty of a problem is its level (0, 1, ..., 40),
# and problems without a level yet have a difficulty of None
DIFFICULTY_BUCKETS = [
    ("Levels 0-9", 9, "#9ecae1"),
    ("Levels 10-19", 19, "#4292c6"),
    ("Levels 20-29", 29, "#08519c"),
    ("Levels 30+", float("inf"), "#08306b"),
    ("Not rated yet", None, "#bdbdbd"),
]


def _difficulty_bucket(difficulty: Optional[int]) -> str:
    if difficulty is None:
        return DIFFICULTY_BUCKETS[-1][0]
    return next(name for name, high, _ in DIFFICULTY_BUCKETS[:-1] if difficulty <= high)


async def generate_graph_best_solvers(days: int, criterion: str, top: int, caller_username: Optional[str]) -> Optional[str]:
    rows = pe_api.get_recent_public_solves_in_database(days)
    if len(rows) == 0:
        return None

    # 1. Gather the stats of each member
    stats = {}
    for row in rows:
        difficulty = await pe_api.Problem(row["problem"]).difficulty() if row["problem"] > 0 else None
        s = stats.setdefault(row["member"], {"solves": [], "count": 0, "rated": 0, "difficulty_sum": 0, "first_100": 0})
        s["solves"].append((difficulty, row["position"]))
        s["count"] += 1
        s["rated"] += difficulty is not None
        s["difficulty_sum"] += difficulty or 0
        s["first_100"] += row["position"] is not None and row["position"] <= 100

    # 2. Score each member, and the contribution of each solve to the bar
    def score(s):
        if criterion == BEST_SOLVERS_CRITERIA[0]:
            return s["count"]
        if criterion == BEST_SOLVERS_CRITERIA[1]:
            return s["difficulty_sum"]
        if criterion == BEST_SOLVERS_CRITERIA[2]:
            return s["difficulty_sum"] / s["rated"] if s["rated"] >= 3 else 0
        return s["first_100"]

    def contribution(s, difficulty, position):
        if criterion == BEST_SOLVERS_CRITERIA[0]:
            return 1
        if criterion == BEST_SOLVERS_CRITERIA[1]:
            return difficulty or 0
        if criterion == BEST_SOLVERS_CRITERIA[2]:
            return (difficulty or 0) / s["rated"]
        return int(position is not None and position <= 100)

    ranking = sorted(
        [(member, s) for member, s in stats.items() if score(s) > 0],
        key=lambda x: (score(x[1]), x[1]["count"], x[1]["difficulty_sum"]), reverse=True
    )
    if len(ranking) == 0:
        return None

    # 3. Keep the top, and add the caller at the bottom if they are not in it
    displayed = [(rank + 1, member, s) for rank, (member, s) in enumerate(ranking)]
    shown = displayed[:top]
    shown += [d for d in displayed[top:] if d[1] == caller_username]

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    labels = []
    for rank, member, _ in shown:
        label = f"{medals.get(rank, f'{rank}.')} {member}"
        labels.append(f"<b>{label}</b>" if member == caller_username else label)

    # 4. Build the plot, one stacked bar per member, split by difficulty
    fig = go.Figure()
    for name, _, color in DIFFICULTY_BUCKETS:
        values = [
            sum(contribution(s, d, p) for d, p in s["solves"] if _difficulty_bucket(d) == name)
            for _, _, s in shown
        ]
        fig.add_trace(go.Bar(y=labels, x=values, name=name, orientation='h', marker_color=color))

    def value_text(s):
        value = score(s)
        text = f"level {value:.1f}" if criterion == BEST_SOLVERS_CRITERIA[2] else str(int(value))
        return text if criterion == BEST_SOLVERS_CRITERIA[0] else f"{text}  ({s['count']} solve{'s' * (s['count'] > 1)})"

    fig.add_trace(go.Scatter(
        y=labels, x=[score(s) for _, _, s in shown], mode='text', showlegend=False,
        text=[" " + value_text(s) for _, _, s in shown], textposition='middle right', textfont=dict(size=14)
    ))

    start = (datetime.datetime.now(pytz.utc) - datetime.timedelta(days=days)).strftime("%b %d")
    end = datetime.datetime.now(pytz.utc).strftime("%b %d")
    fig.update_layout(
        title=dict(text=f"Best solvers of the last {days} day{'s' * (days > 1)} ({start} - {end}, UTC)<br>"
                        f"<sup>{criterion} · {len(rows)} solves by {len(stats)} members</sup>", font=dict(size=24)),
        barmode='stack',
        plot_bgcolor='#f0f0f0',         # Inner graph area (light gray)
        paper_bgcolor='white',          # Outer margins (solid white)
        width=1200, height=200 + 40 * len(shown),
        margin=dict(l=20, r=20, t=100, b=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.0, xanchor='right', x=1, traceorder='normal')
    )

    # Leave some room on the right for the value labels
    max_score = max(score(s) for _, _, s in shown)
    fig.update_xaxes(showgrid=True, gridcolor='white', gridwidth=1.5, range=[0, max_score * 1.25])
    fig.update_yaxes(autorange='reversed', tickfont=dict(size=14), ticksuffix="  ")

    # 5. Save and return path
    filename = f"images_saves/best_solvers_{days}_{int(time.time() * 1000)}.png"
    fig.write_image(filename, scale=2)

    return filename


def _build_gol_gif(r, username: str) -> str:

    # Process dates and build continuous timeline
    dates = [datetime.datetime.fromtimestamp(s.unixtime()).date() for s in r]
    df = pd.DataFrame({'date': pd.date_range(start=min(dates), end=max(dates), freq='D')})
    
    solve_counts = pd.Series(dates).value_counts().reset_index()
    solve_counts.columns = ['date', 'solves']
    df['date'] = df['date'].dt.date
    df = df.merge(solve_counts, on='date', how='left').fillna({'solves': 0})
    
    # Grid Math (Target Aspect Ratio 3:1)
    num_rows = _github_grid_rows(len(df))
    df['x_index'] = df.index // num_rows
    df['y_index'] = df.index % num_rows
    
    # Create the initial state matrix
    heatmap = df.pivot(index='y_index', columns='x_index', values='solves').fillna(0)
    heatmap = heatmap.reindex(index=range(num_rows), fill_value=0)
    grid = (heatmap.values > 0).astype(int)
    
    h, w = grid.shape
    
    # Drawing parameters
    cell_size = 12
    gap = 3
    step_size = cell_size + gap
    title_space = 52
    img_h = h * step_size + gap + title_space
    img_w = w * step_size + gap
    
    color_dead = np.array([235, 237, 240], dtype=np.uint8)
    color_alive = np.array([33, 110, 57], dtype=np.uint8)
    color_bg = np.array([255, 255, 255], dtype=np.uint8)
    color_text = (60, 60, 60)

    title = f"Game of Life for member {username}"
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", size=22)
    except Exception:
        font = ImageFont.load_default()
    
    frames = []

    # Timing model
    accel_generations = 50
    fastest_frame_duration_ms = 50
    steady_phase_ms = 20_000
    steady_generations = max(1, steady_phase_ms // fastest_frame_duration_ms)
    num_generations = accel_generations + steady_generations

    durations = [1500]
    for i in range(1, accel_generations):
        progress = i / (accel_generations - 1)
        current_duration = fastest_frame_duration_ms + 750 * ((1 - progress) ** 2)
        durations.append(int(current_duration))

    durations.extend([fastest_frame_duration_ms] * steady_generations)
    
    # Game of Life Simulation Loop
    for _ in range(num_generations):
        img_array = np.full((img_h, img_w, 3), color_bg, dtype=np.uint8)
        
        for i in range(h):
            for j in range(w):
                color = color_alive if grid[i, j] else color_dead
                y = gap + title_space + i * step_size
                x = gap + j * step_size
                img_array[y:y+cell_size, x:x+cell_size] = color

        frame_img = Image.fromarray(img_array)
        draw = ImageDraw.Draw(frame_img)
        bbox = draw.textbbox((0, 0), title, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = max(0, (img_w - text_w) // 2)
        draw.text((text_x, 14), title, fill=color_text, font=font)

        frames.append(frame_img)
        
        # Calculate next generation
        padded = np.pad(grid, 1, mode='constant')
        neighbors = sum(np.roll(np.roll(padded, i, 0), j, 1)
                        for i in (-1, 0, 1) for j in (-1, 0, 1)
                        if (i != 0 or j != 0))
        neighbors = neighbors[1:-1, 1:-1]
        
        # Conway's Rules
        grid = ((neighbors == 3) | (grid & (neighbors == 2))).astype(int)

    # Save as GIF
    filename = f"images_saves/{username}_gol_github.gif"
    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=durations, 
        loop=0
    )
    
    return filename


# 2. Keep the async wrapper for network calls and thread offloading
async def generate_graph_github_gol(member: pe_api.Member) -> str:

    r = await member.solves_by_csv(True)
    username = await member.username_option()
    
    filename = await asyncio.to_thread(_build_gol_gif, r, username)
    
    return filename




if __name__ == "__main__":

    # with open("pjt33_history_2023_04_25_2325.csv", "r") as f:
    #     content = "".join(f.readlines())

    # tic = time.time()

    # generate_individual_graph(content, "Teyzer18")

    # print(time.time() - tic)

    pe_setup.setup()    

    m = pe_api.Member(_username="pacome_f")
    r = asyncio.run(m.solves_by_csv())

    

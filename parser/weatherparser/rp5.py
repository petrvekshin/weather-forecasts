import datetime as dt
from typing import List, Tuple
from bs4 import BeautifulSoup


datetime_format = "%Y-%m-%d %H:%M:%S"


months = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "мая": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
}


def replace_empty_str(value: str) -> str:
    if value == "":
        return "-"
    else:
        return value


def get_cells(row: List[any]):
    res = row.find_all("td", recursive=False)[1:]
    return res


def last_update_delta(items):
    days = 0
    hours = 0
    minutes = 0
    for item in items:
        val, unit = item.split("&")
        if unit[5] == "м":
            minutes = int(val)
        elif unit[5] == "ч":
            hours = int(val)
        elif (unit[5] == "д") or (unit[5] == "с"):
            days = int(val)
    return dt.timedelta(days=days, hours=hours, minutes=minutes)


def rp5(content, request_time) -> List[any]:
    request_time_str = request_time.strftime(datetime_format)
    year_now = request_time.year
    soup = BeautifulSoup(content, "lxml")
    table = soup.find_all("table", class_="forecastTable")[-1]
    rows = table.find_all("tr", recursive=False, limit=12)
    row_names = {}
    for ind, row in enumerate(rows):
        try:
            row_names[row.td.a.text.split(" ")[0]] = ind
        except:
            continue
    
    try:
        a = soup.find("div", id="FheaderContent")
        update_time_text = a.find("div", class_="qIconHintInfo qIconNotActive")["onmouseover"][15:-18].split(" ")
        update_time = (request_time - last_update_delta(update_time_text[5:-1])).strftime(datetime_format)
    except:
        update_time = "-"

    days_colspans = []
    for td in rows[0].find_all("td", recursive=False):
        items = td.find("span", class_="weekDay").text.split(" ")
        days_colspans.append([items, int(td["colspan"])])
    days_colspans[0][1] -= 1
    third_day_day = int(days_colspans[2][0][-2])
    third_day_month = months[days_colspans[2][0][-1][:3].lower()]
    third_day_date = dt.datetime(year=year_now, month=third_day_month, day=third_day_day)
    if (third_day_date - request_time).days < -30:
        third_day_date = dt.datetime(year=year_now + 1, month=third_day_month, day=third_day_day)
    days = []
    for d, (_, n_times) in enumerate(days_colspans, start=-2):
        delta = dt.timedelta(days=d)
        day = third_day_date + delta
        days += [day] * n_times

    times = [int(td.text) for td in get_cells(rows[1])[:-1]]

    days_times = []
    for i, t in enumerate(times):
        dt_str = days[i] + dt.timedelta(hours=t)
        days_times.append(dt_str.strftime(datetime_format))

    clouds = [td.div.div["onmouseover"][18:-11].replace("</b><br/>", " ") for td in get_cells(rows[row_names["Облачность"]])[:-1]]
    precips = [td.div["onmouseover"][15:-11] for td in get_cells(rows[row_names["Осадки,"]])[:-1]]
    temps = [td.div.text for td in get_cells(rows[row_names["Температура"]])[:-1]]
    feels_like = []
    try:
        for ind, td in enumerate(get_cells(rows[row_names["Ощущается"]])[:-1]):
            try:
                feels_like.append(td.div.text)
            except AttributeError:
                feels_like.append(temps[ind])
    except KeyError:
        feels_like = ["-"] * len(temps)
    # feels_like = [td.div.text for td in get_cells(rows[row_names["Ощущается"]])]
    pressures = [td.div.text for td in get_cells(rows[row_names["Давление"]])[:-1]]
    try:
        fogs = [replace_empty_str(td.text) for td in get_cells(rows[row_names["Туман,"]])[:-1]]
    except KeyError:
        fogs = ["-"] * len(temps)
    wind_speeds = []
    for td in get_cells(rows[row_names["Ветер:"]])[:-1]:
        if td.has_attr("onmouseover"):
            if td["onmouseover"] == "tooltip(this, 'Штиль, безветрие' , 'hint')":
                wind_speeds.append("0")
            else:
                wind_speeds.append("-")
        else:
            wind_speeds.append(replace_empty_str(td.div.text))
    # wind_speeds = [replace_empty_str(td.div.text) for td in get_cells(rows[row_names["Ветер:"]])]
    wind_gusts = [replace_empty_str(td.div.text) for td in get_cells(rows[row_names["Ветер:"]+1])[:-1]]
    wind_dirs = [replace_empty_str(td.text) for td in get_cells(rows[row_names["Ветер:"]+2])[:-1]]
    hums = [td.text for td in get_cells(rows[row_names["Влажность"]])[:-1]]
    db_lines = []
    request_times = [""] * len(days_times)
    update_times = request_times.copy()
    request_times[0] = request_time_str
    update_times[0] = update_time
    for i, t in enumerate(days_times):
        db_line = ";".join([request_times[i], update_times[i], days_times[i], 
        temps[i], feels_like[i], hums[i], pressures[i], 
        wind_speeds[i], wind_gusts[i], wind_dirs[i], fogs[i], precips[i], clouds[i]
        ])
        db_lines.append(db_line)

    fields = [
        "Request time",
        "Update time",
        "Time",
        "Temperature, deg. C",
        "Feels like, deg. C",
        "Humidity, pct",
        "Pressure, mmHg",
        "Wind speed, m/s",
        "Wind gusts, m/s",
        "Wind direction",
        "Fog, pct",
        "Precipitation",
        "Cloud cover"
    ]

    return ";".join(fields), db_lines

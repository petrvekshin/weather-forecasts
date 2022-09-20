import datetime as dt
from bs4 import BeautifulSoup


datetime_format = "%Y-%m-%d %H:%M:%S"

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.87 Safari/537.36"
}

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

js_array_names = set(["arr_temperature=[", "arr_wind_dir=[", "arr_wind_dir_name=[",
"arr_wind_speed=[", "arr_pressure=[", "arr_precip_val=[", "arr_precip_ver=[",
"arr_humidity=[", "arr_phenomenon_name=["])

def get_arr_name_vals(array_string):
    points = array_string.split("{")
    if points[0] not in js_array_names:
        return points[0], None

    n = 1 if points[0][-6:] == "name=[" else 0
    vals = {}
    for point in points[1:]:
        y_ind = point.find("y:", 24)
        x_vals = point[12:y_ind-3]
        ind_ind = point.find(", i", -14)
        year, month, day, hour = x_vals.split(",")
        y_val = point[y_ind+3+n:ind_ind-n]
        if y_val == "null":
            y_val = "0"
        vals[(int(year), int(month) + 1, int(day), int(hour))] = y_val

    return points[0], vals


def combine_day_night(day_array, night_array):
    array = [day_array[0]]
    for n, d in zip(night_array, day_array[1:]):
        array.extend([n, d])
    return array


def meteinfo(content, request_time):
    year_now = request_time.year
    rt = request_time.strftime(datetime_format)

    soup = BeautifulSoup(content, "lxml")
    table = soup.find("table", class_="fc_tab_1")
    ut = table.next_sibling.text.split("обновлена ")[-1]
    rows = table.contents
    day_text, month_text = rows[0].find("nobr").text.split(" ")
    month = months[month_text[:3]]
    day = int(day_text)
    hour = 14
    first_dt = dt.datetime(year=year_now, month=month, day=day, hour=hour)
    if (first_dt - request_time).days < -30:
        first_dt = dt.datetime(year=year_now + 1, month=month, day=day, hour=hour)

    d_conditions = [t.div.img["title"] for t in rows[1].contents[1:]]
    n_conditions = [t.div.img["title"] for t in rows[7].contents[2:]]
    conditions = combine_day_night(d_conditions, n_conditions)

    d_max_temps = [t.text[:-1] for t in rows[2].contents[1:]]
    n_min_temps = [t.text[:-1] for t in rows[8].contents[2:]]
    temps = combine_day_night(d_max_temps, n_min_temps)

    assert len(d_max_temps) - 1 == len(n_min_temps)

    times = []
    for i in range(len(temps)):
        times.append((first_dt + dt.timedelta(hours=i*12)).strftime(datetime_format))

    d_precips = []
    for pp in [t.text.lstrip() for t in rows[4].contents[1:]]:
        if pp == "0":
            d_precips.append(("0", "-"))
        else:
            p1, p2 = pp.split(" (")
            d_precips.append((p1, p2[:-2]))
    n_precips = []
    for pp in [t.text.lstrip() for t in rows[10].contents[2:]]:
        if pp == "0":
            n_precips.append(("0", "-"))
        else:
            p1, p2 = pp.split(" (")
            n_precips.append((p1, p2[:-2]))
    precips = combine_day_night(d_precips, n_precips)

    d_winds = [(t.div.span.nobr.text, t.div.span["title"]) for t in rows[5].contents[1:]]
    n_winds = [(t.div.span.nobr.text, t.div.span["title"]) for t in rows[11].contents[2:]]
    winds = combine_day_night(d_winds, n_winds)

    d_pressures = [t.div.text for t in rows[6].contents[1:]]
    n_pressures = [t.div.text for t in rows[12].contents[2:]]
    pressures = combine_day_night(d_pressures, n_pressures)

    db_lines = []
    rts = [''] * len(times)
    uts = rts.copy()
    rts[0] = rt
    uts[0] = ut
    for i, t in enumerate(times):
        db_line = (rts[i] + ";" + uts[i] + ";" + t + ";"
                + temps[i] + ";" + pressures[i] + ";"
                + winds[i][0] + ";" + winds[i][1] + ";"
                + precips[i][0] + ";" + precips[i][1] + ";"
                + conditions[i])
        db_lines.append(db_line)

    # extract information from JS tag
    js_tag = soup.find("script", language="JavaScript")
    js_lines = js_tag.string.split("; ")
    arrays = {k:None for k in js_array_names}

    for i in range(13, 23):
        name, vals = get_arr_name_vals(js_lines[i])
        if vals:
            arrays[name] = vals

    js_db_lines = []

    for key in sorted([k for k in arrays["arr_temperature=["].keys()]):
        t = dt.datetime(year=key[0], month=key[1], day=key[2], hour=key[3]).strftime(datetime_format)
        tmp = arrays["arr_temperature=["][key]
        wdr = arrays["arr_wind_dir=["][key]
        wdn = arrays["arr_wind_dir_name=["][key]
        wsp = arrays["arr_wind_speed=["][key]
        prs = arrays["arr_pressure=["][key]
        hum = arrays["arr_humidity=["][key]
        try:
            pvl = arrays["arr_precip_val=["][key]
            pvr = arrays["arr_precip_ver=["][key]
            phn = arrays["arr_phenomenon_name=["][key]
        except KeyError:
            pvl = pvr = phn = "-"
        js_db_lines.append(f"{rt};{t};{tmp};{hum};{prs};{wsp};{wdr};{wdn};{pvl};{pvr};{phn}")
        # reassign rt so not to write the same timestamp in every row
        rt = ''

    fields = [
        "Request time",
        "Update time",
        "Time",
        "Min/max temperature, deg. C",
        "Pressure, mmHg",
        "Wind speed, m/s",
        "Wind direction",
        "Precipitation, mm",
        "Probability of precipitation, pct",
        "Conditions"
    ]
    fields_js = [
        "Request time",
        "Time",
        "Temperature, deg. C",
        "Humidity, pct",
        "Pressure, mmHg",
        "Wind speed, m/s",
        "Wind direction, deg",
        "Wind direction",
        "Precipitation, mm",
        "Probability of precipitation, pct",
        "Conditions"
    ]

    return (";".join(fields), db_lines), (";".join(fields_js), js_db_lines)

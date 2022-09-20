import datetime as dt
from time import sleep
from random import uniform
from bs4 import BeautifulSoup


datetime_format = "%Y-%m-%d %H:%M:%S"


def utc_to_local(date: str, time: str) -> str:
    Y, m, d = date.split("-")
    H, M, S = time.split(":")
    dt_utc = dt.datetime(
        year=int(Y), month=int(m), day=int(d), hour=int(H), minute=int(M), second=int(S)
    )
    dt_loc = dt_utc + dt.timedelta(hours=5)
    dt_str_loc = dt_loc.strftime(datetime_format)
    return dt_str_loc


def gismeteo_datetime(datetime_str: str):
    items = datetime_str.split(" ")
    if len(items) == 8:
        forecast_dt = utc_to_local(*items[2:4])
        weather_dt = utc_to_local(*items[-2:])
    else:
        forecast_dt = ""
        weather_dt = utc_to_local(*items[-3:-1])
    return forecast_dt, weather_dt


def len_check(values):
    if len(values) != 8:
        raise Exception


def gismeteo(content, request_time):

    len_errors = [""] * 8
    request_times = len_errors.copy()
    request_times[0] = request_time.strftime(datetime_format)

    db_lines = []

    soup = BeautifulSoup(content, "lxml")
    soup = soup.find("section", class_="content wrap")

    item_tag = soup.find("div", class_="widget-items")
    time_tag = soup.find("div", class_="widget-row widget-row-time")
    times = [
        gismeteo_datetime(t["title"])
        for t in time_tag.find_all("div", class_="row-item")
    ]
    len_check(times)

    try:
        icon_tag = item_tag.find("div", class_="widget-row widget-row-icon")
        conditions = [
            d["data-text"]
            for d in icon_tag.find_all("div", class_="weather-icon tooltip")
        ]
        len_check(conditions)
    except:
        conditions = len_errors

    try:
        temp_tag = item_tag.find(
            "div", class_="widget-row-chart widget-row-chart-temperature"
        )
        temps = [
            t.text.replace("−", "-")
            for t in temp_tag.find_all("span", class_="unit unit_temperature_c")
        ]
        len_check(temps)
    except:
        temps = len_errors

    try:
        wind_tag = item_tag.find(
            "div", class_="widget-row widget-row-wind-speed-gust row-with-caption"
        )
        wind_items = wind_tag.find_all("div", class_="row-item")
        wind_speeds = [w.span.text.strip() for w in wind_items]
        len_check(wind_speeds)
    except:
        wind_speeds = len_errors

    try:
        precip_tag = item_tag.find(
            "div",
            class_="widget-row widget-row-precipitation-bars row-with-caption",
        )
        precips = [p.text.strip() for p in precip_tag.find_all("div", class_="row-item")]
        len_check(precips)
    except:
        precips = len_errors

    try:
        wind_widget = soup.find("div", class_="widget widget-wind widget-oneday")
        widget_items = wind_widget.find("div", class_="widget-items")
        wind_dir_tag = widget_items.find(
            "div", class_="widget-row widget-row-wind-direction"
        )
        items = [
            item.find("div", class_="direction")
            for item in wind_dir_tag.find_all("div", class_="row-item")
        ]
        len_check(items)
        wind_dirs = []
    except:
        wind_dirs = len_errors

    for item in items:
        if item is not None:
            wind_dirs.append(item.text)
        else:
            wind_dirs.append("-")

    try:
        snow_tag = soup.find("div", class_="widget widget-snow widget-oneday")
        snow_precip_tag = snow_tag.find(
            "div", class_="widget-row widget-row-icon-snow row-with-caption"
        )
        snow_precips = [
            p.text.strip() for p in snow_precip_tag.find_all("div", class_="row-item")
        ]
        len_check(snow_precips)
    except:
        snow_precips = len_errors

    try:
        snow_depth_tag = snow_precip_tag.next_sibling
        snow_depths = [p.text for p in snow_depth_tag.div.div.find_all("div")]
        len_check(snow_depths)
    except:
        snow_depths = len_errors

    try:
        road_tag = soup.find(
            "div", class_="widget widget-roadcondition widget-oneday"
        )
        road_tag = road_tag.find(
            "div", class_="widget-row widget-row-roadcondition"
        )
        roads = [r.text.strip() for r in road_tag.find_all("div", class_="row-item")]
        len_check(roads)
    except:
        roads = len_errors

    try:
        press_tag = soup.find("div", class_="widget widget-pressure widget-oneday")
        press_tag = press_tag.find(
            "div", class_="widget-row-chart widget-row-chart-pressure"
        )
        pressures = [
            p.text.strip()
            for p in press_tag.find_all(
                "span", class_="unit unit_pressure_mm_hg_atm"
            )
        ]
        len_check(pressures)
    except:
        pressures = len_errors

    try:
        hum_tag = soup.find("div", class_="widget widget-humidity widget-oneday")
        hum_tag = hum_tag.find("div", class_="widget-row widget-row-humidity")
        humidities = [h.text.strip() for h in hum_tag.find_all("div")]
        len_check(humidities)
    except:
        humidities = len_errors

    try:
        vis_tag = soup.find("div", class_="widget widget-visibility widget-oneday")
        vis_tag = vis_tag.find("div", class_="widget-row widget-row-visibility")
        visibilities = [v.text.strip() for v in vis_tag.find_all("div")]
        len_check(visibilities)
    except:
        visibilities = len_errors

    try:
        rad_tag = soup.find("div", class_="widget widget-radiation widget-oneday")
        rad_tag = rad_tag.find("div", class_="widget-row widget-row-radiation")
        radiations = [r.text.strip() for r in rad_tag.find_all("div")]
        len_check(radiations)
    except:
        radiations = len_errors

    try:
        geomag_tag = soup.find(
            "div", class_="widget widget-geomagnetic widget-oneday"
        )
        geomag_tag = geomag_tag.find(
            "div", class_="widget-row widget-row-geomagnetic"
        )
        geomags = [
            g.div.text.strip() for g in geomag_tag.find_all("div", class_="row-item")
        ]
        len_check(geomags)
    except:
        geomags = len_errors

    try:
        pol_tag = soup.find("div", class_="widget widget-pollen widget-oneday")
        pol_tag = pol_tag.find("div", class_="widget-row widget-row-pollen-birch-point row-with-caption")
        birch_pol = [r.text.strip() for r in pol_tag.find_all("div", class_="row-item")]
        len_check(birch_pol)
    except:
        birch_pol = len_errors


    for i in range(8):
        db_line = ";".join(
            [
                request_times[i],
                *times[i],
                temps[i],
                humidities[i],
                pressures[i],
                precips[i],
                snow_precips[i],
                snow_depths[i],
                wind_speeds[i],
                wind_dirs[i],
                conditions[i],
                roads[i],
                visibilities[i],
                radiations[i],
                geomags[i],
                birch_pol[i]
            ]
        )
        db_lines.append(db_line)

        # sleep(uniform(0.0, 0.35))
    fields = [
        "Request time",
        "Update time",
        "Time",
        "Temperature, deg. C",
        "Humidity, pct",
        "Pressure, mmHg",
        "Precipitation, mm",
        "Snowfall, sm",
        "Snow depth, sm",
        "Wind speed, m/s",
        "Wind direction",
        "Conditions",
        "Road conditions",
        "Visibility",
        "UV index",
        "Kp-index",
        "Birch pollen, points"
    ]

    return ";".join(fields), db_lines

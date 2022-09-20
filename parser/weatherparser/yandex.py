import datetime as dt
from bs4 import BeautifulSoup


datetime_format = "%Y-%m-%d %H:%M:%S"


months = {
    "янв": 1,
    "jan": 1,
    "фев": 2,
    "feb": 2,
    "мар": 3,
    "mar": 3,
    "апр": 4,
    "apr": 4,
    "мая": 5,
    "may": 5,
    "июн": 6,
    "jun": 6,
    "июл": 7,
    "jul": 7,
    "авг": 8,
    "aug": 8,
    "сен": 9,
    "sep": 9,
    "окт": 10,
    "oct": 10,
    "ноя": 11,
    "nov": 11,
    "дек": 12,
    "dec": 12,
}

time_of_day = {
    "утром": 9,
    "morning": 9,
    "днём": 15,
    "day": 15,
    "вечером": 21,
    "evening": 21,
    "ночью": 27,
    "night": 27,
}


def yandex(content, request_time):
    year_now = request_time.year
    request_time_fmt = request_time.strftime(datetime_format)
    soup = BeautifulSoup(content, "lxml")
    # print(soup.prettify())
    cards = soup.find_all("article", class_="card")
    if not cards:
        # print("no cards found")
        return None
    db_lines = []
    for card in cards:
        day_tag = card.find("strong", class_="forecast-details__day-number")
        if day_tag is None:
            continue
        try:
            day = int(day_tag.text)
            month = months[
                card.find("span", class_="forecast-details__day-month").text[:3].lower()
            ]
        except:
            continue

        card_date = dt.datetime(year=year_now, month=month, day=day)
        if (card_date - request_time).days < -30:
            card_date = dt.datetime(year=year_now + 1, month=month, day=day)

        dl = card.find("dl", class_="forecast-fields")
        
        try:
            dds = dl.find_all("dd", class_="forecast-fields__value")
            uv_title = dds[0].previous_sibling.text
            uv_title_found = (uv_title == "УФ-индекс") or (uv_title == "UV Index")
            mf_title = dds[-1].previous_sibling.text
            mf_title_found = (mf_title == "Магнитное поле") or (mf_title == "Magnetic field")
        except:
            uv_title_found = mf_title_found = False

        uv = dds[0].text if uv_title_found else "-"
        mf = dds[-1].text if mf_title_found else "-"

        rows = card.find_all("tr", class_="weather-table__row")
        for row in rows:
            # day_part & temp cell
            cell = row.find(
                "td",
                class_="weather-table__body-cell weather-table__body-cell_type_daypart weather-table__body-cell_wrapper",
            )
            daypart_delta = time_of_day[
                cell.find("div", class_="weather-table__daypart").text
            ]
            row_datetime = (
                card_date + dt.timedelta(hours=daypart_delta)
            ).strftime(datetime_format)
            temp_tags = cell.find_all(
                "span", class_="temp__value temp__value_with-unit"
            )
            temps = [t.text for t in temp_tags]
            min_temp = temps[0]
            if len(temps) > 1:
                max_temp = temps[1]
            else:
                max_temp = min_temp
            # condition cell
            condition_tag = row.find(
                "td",
                class_="weather-table__body-cell weather-table__body-cell_type_condition",
            )
            conditions = condition_tag.text
            pressure_tag = condition_tag.next_sibling
            pressure = pressure_tag.text
            humidity_tag = pressure_tag.next_sibling
            humidity = humidity_tag.text
            if humidity[-1] == "%":
                humidity = humidity[:-1]

            wind_tag = humidity_tag.next_sibling
            wind_speed_tag = wind_tag.span.div.span
            wind_dir_tag = wind_speed_tag.next_sibling
            if wind_speed_tag is not None:
                wind_speed = wind_speed_tag.text
            else:
                wind_speed = wind_tag.text
            if wind_dir_tag is not None:
                wind_dir = wind_dir_tag.abbr.text
            else:
                wind_dir = "-"

            cell = row.find(
                "td",
                class_="weather-table__body-cell weather-table__body-cell_type_feels-like",
            )
            temp_tags = cell.find_all(
                "span", class_="temp__value temp__value_with-unit"
            )
            feels_like = [t.text for t in temp_tags][0]

            db_line = ";".join(
                [
                    request_time_fmt,
                    row_datetime,
                    min_temp,
                    max_temp,
                    feels_like,
                    humidity,
                    pressure,
                    wind_speed,
                    wind_dir,
                    conditions,
                    uv,
                    mf,
                ]
            )
            # reassign request_time_fmt so not to write the same timestamp in every row
            request_time_fmt = ''
            db_lines.append(db_line)

    fields = [
        "Request time",
        "Time",
        "Min temperature, deg. C",
        "Max temperature, deg. C",
        "Feels like, deg. C",
        "Humidity, pct",
        "Pressure, mmHg",
        "Wind speed, m/s",
        "Wind direction",
        "Conditions",
        "UV index",
        "Magnetic field",
    ]

    return ";".join(fields), db_lines

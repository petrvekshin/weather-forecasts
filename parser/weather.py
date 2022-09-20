import os
import requests
import datetime as dt
from weatherparser import yandex, gismeteo, rp5, meteinfo


yandex_locations = ["artyomovsky"]
rp5_locations = ["Погода_в_Артемовском,_Свердловская_область"]
gismeteo_locations = ["artemovsky-4495"]
meteoinfo_locations = ["russia/sverdlovsk-area/artenovsky"]

weather_dir = "../data/forecast"
html_weather_dir = "../data/forecast/failed_pages"

# datetime format for prefixing of names of html files
datetime_format = "%Y%m%d%H%M%S"

headers = {
"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.87 Safari/537.36"}


def lines_to_file(file_name, lines, header=None):
    if not os.path.exists(file_name) and (header is not None):
        with open(file_name, "w") as f:
            f.write(header + "\n")
    with open(file_name, "a") as f:
        for line in lines:
            f.write(line + "\n")


for location in yandex_locations:
    file_name = "yandex-" + location
    full_path = f"{weather_dir}/{file_name}.csv"
    # get html content
    url = f"https://yandex.ru/pogoda/{location}/details"
    request_time = dt.datetime.now()
    content = requests.get(url, headers=headers).text
    # parse html
    try:
        header, lines = yandex(content, request_time)
    except:
        # save failed pages to parse later
        dt_str = request_time.strftime(datetime_format)
        html_full_path = f"{html_weather_dir}/{dt_str}_{file_name}.html"
        with open(html_full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        continue
    lines_to_file(full_path, lines, header=header)


for location in rp5_locations:
    file_name = "rp5-" + location.replace(',', '')
    full_path = f"{weather_dir}/{file_name}.csv"
    # get html content
    url = "https://rp5.ru/" + location
    request_time = dt.datetime.now()
    content = requests.get(url, headers=headers).text
    # parse html
    try:
        header, lines = rp5(content, request_time)
    except:
        # save failed pages to parse later
        dt_str = request_time.strftime(datetime_format)
        html_full_path = f"{html_weather_dir}/{dt_str}_{file_name}.html"
        with open(html_full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        continue
    lines_to_file(full_path, lines, header=header)


for location in meteoinfo_locations:
    name = location.replace("/", "-")
    file_name = "meteoinfo-" + name
    full_path = f"{weather_dir}/{file_name}.csv"
    file_name_js = "meteoinfo-js-" + name
    full_path_js = f"{weather_dir}/{file_name_js}.csv"
    # get html content
    url = f"https://meteoinfo.ru/forecasts/{location}"
    request_time = dt.datetime.now()
    content = requests.get(url).text
    # parse html
    try:
        (header, lines), (header_js, lines_js) = meteinfo(content, request_time)
    except:
        # save failed pages to parse later
        dt_str = request_time.strftime(datetime_format)
        html_full_path = f"{html_weather_dir}/{dt_str}_{file_name}.html"
        with open(html_full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        continue
    lines_to_file(full_path, lines, header=header)
    lines_to_file(full_path_js, lines_js, header=header_js)


gm_day_urls = [
    "",
    "tomorrow",
    "3-day",
    "4-day",
    "5-day",
    "6-day",
    "7-day",
    "8-day",
    "9-day",
    "10-day",
]


for location in gismeteo_locations:
    file_name = "gismeteo-" + location
    full_path = f"{weather_dir}/{file_name}.csv"
    # interate through all pages
    url_base = f"https://www.gismeteo.ru/weather-{location}/"
    for num, day_url in enumerate(gm_day_urls, start=1):
        # get html content
        url = url_base + day_url
        request_time = dt.datetime.now()
        content = requests.get(url, headers=headers).text
        # parse html
        try:
            header, lines = gismeteo(content, request_time)
        except:
            # save failed pages to parse later
            dt_str = request_time.strftime(datetime_format)
            html_full_path = f"{html_weather_dir}/{dt_str}_{file_name}_{num:0>2}.html"
            with open(html_full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            continue
        lines_to_file(full_path, lines, header=header)

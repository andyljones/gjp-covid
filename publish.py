import numpy as np
import pandas as pd
import requests
import jinja2
from bs4 import BeautifulSoup
from pathlib import Path

URL = 'https://goodjudgment.io/covid/dashboard/bin/loadSub.php'

# Right boundary on deaths is the same ratio to the stated boundary as cases
BOUNDARIES = pd.DataFrame([
    [1, 5.3e6, 53e6, 530e6, 5.3e9, 7.8e9],
    [1, 80e3, 800e3, 8e6, 80e6, 120e6],
    [1, 230e3, 2.3e6, 23e6, 230e6, 330e6],
    [1, 3.5e3, 35e3, 350e3, 3.5e6, 5e6]], 
    index=['world_cases', 'world_deaths', 'us_cases', 'us_deaths'])

def prettify(x):
    suffixes = np.array(['', ' thousand', ' million', ' billion', ' trillion'])

    order = np.log10(max(abs(x), 1))
    index = min(int(order//3), len(suffixes)-1)
    suffix = suffixes[index]

    significand = x / (10**(3*(order//3)))
    rounded = float(f'{significand:.2g}')
    head = str(int(rounded) if rounded % 1 == 0 else rounded)

    return head + suffix

def fetch(date):
    r = requests.get(URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, features='html5lib')

    return pd.DataFrame({
        'field': BOUNDARIES.index.repeat(5),
        'lower': BOUNDARIES.values[:, :-1].flatten(),
        'upper': BOUNDARIES.values[:, 1:].flatten(),
        'fractions': [int(t.attrs['style'][6:-2])/100 for t in soup.select('.prob')]})

def central_estimates():
    df = fetch(pd.Timestamp.now().floor('H'))

    # Geometric averages
    df['mid'] = (df.lower*df.upper)**.5
    return df.mid.pow(df.fractions).groupby(df.field).prod()

def render():
    template = jinja2.Template(Path('template.j2').read_text())

    central = central_estimates().apply(prettify)
    rendered = template.render(**central)

    Path('index.html').write_text(rendered)






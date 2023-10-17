import pandas as pd
import numpy as np
import csv
from helper import convert_percentage_to_float
from helper import convert_befragte
from helper import convert_weird_date_to_date

with open("urls.csv") as f:
    reader = csv.DictReader(f)
    urls = [d for d in reader]

all_data = []

for row in urls:

    institut = row["Institut"]
    region = row["Region"]
    url = row["url"]
    table = pd.read_html(url)
    data = table[1]

    # Finde die Zeile mit dem Ende der Tabelle
    m = data[data["Sonstige"] == "Sonstige"].index.to_numpy()[0]
    l = len(data) - m

    # Entferne die letzten l Zeilen
    data.drop(
        index=data.tail(l).index,
        axis=0,
        inplace=True
    )

    # Entferne die leeren Spalten
    data.dropna(
        how="all",
        axis=1,
        inplace=True
    )

    # Benenne die erste Spalte um
    data.rename(
        columns={
            "Unnamed: 0": "Datum"
        },
        inplace=True
    )

    # Extrahiere die Parteinamen
    parteinamen = [x for x in data.columns if not x in ["Datum", "Befragte", "Zeitraum"]]
    variablen = [x for x in data.columns if not x in parteinamen]

    # Fülle leere Ergebnisse mit "-"
    for partei in parteinamen:
        data[partei].fillna("-", inplace=True)

    # Schmelze die Tabelle
    data = pd.melt(
        data,
        id_vars=variablen,
        value_vars=parteinamen,
        var_name="Partei",
        value_name="Ergebnis"
    )

    # Entferne alle Daten ohne klares Datum
    data.Datum.fillna("..", inplace=True)
    data.Datum = data.Datum.apply(
        lambda x: ".." if "?" in x else x.strip("*")
    )

    # Hardgecodete Sonderfälle...
    data.Datum = data.Datum.apply(
        lambda x: "27.09.1998" if x == "Wahl 1998" else x
    )
    if institut == "INSA / YouGov":
        data.drop(data[data["Datum"] == "02.02.2017"].index, inplace=True)

    # Konvertiere komische Datumsangaben..
    data.Datum = data.Datum.apply(convert_weird_date_to_date)

    # Erstelle Tag, Monat, Jahr anstelle von Datum
    datum_split = data.Datum.str.split(".", expand=True)
    data["Tag"] = pd.to_numeric(datum_split[0])
    data["Monat"] = pd.to_numeric(datum_split[1])
    data["Jahr"] = pd.to_numeric(datum_split[2])
    data.drop(
        columns=["Datum"],
        axis=1,
        inplace=True
    )

    # Konvertiere die Prozentangaben zu floats
    data.Ergebnis = data.Ergebnis.apply(convert_percentage_to_float)

    # Ergänze die Spalte Befragte, falls diese nicht existiert
    if not ("Befragte" in data):
        data["Befragte"] = np.NaN

    # Unterscheide zwischen Umfragen und Wahlen
    data["Art"] = data.Befragte.apply(
        lambda x: "Wahl" if x == "Bundestagswahl" else "Umfrage"
    )
    # Konvertiere die Befragtenzahlen zu ints
    data.Befragte = data.Befragte.astype("string")
    data.Befragte.fillna("?", inplace=True)
    data.Befragte = data.Befragte.apply(convert_befragte)

    # Ergänze die Spalte Zeitraum, falls diese nicht existiert
    if not ("Zeitraum" in data):
        data["Zeitraum"] = np.NaN

    # Entferne "Bundestagswahl" aus der Spalte "Zeitraum"
    data.Zeitraum = data.Zeitraum.apply(
        lambda x: np.NaN if x == "Bundestagswahl" else x
    )

    # Ergänze die Spalten Institut und Region
    data["Region"] = region
    data["Institut"] = institut

    # Lösche Einträge, wo weder Datum noch Zeitraum gegeben ist
    data.dropna(
        subset=["Tag", "Monat", "Jahr", "Zeitraum"],
        how="all",
        inplace=True
    )

    # Ergänze Jahreszahlen
    data.Jahr.bfill(inplace=True)

    # Ergänze Tage und Monate, wo verfügbar
    if not data.Zeitraum.isnull().all():
        data.Tag.fillna(pd.to_numeric(data.Zeitraum.str[-6:-4], errors="coerce"), inplace=True)
        data.Monat.fillna(pd.to_numeric(data.Zeitraum.str[-3:-1], errors="coerce"), inplace=True)

    # Konvertiere Tage, Monate und Jahre zu ints
    data.Tag = data.Tag.astype("int")
    data.Monat = data.Monat.astype("int")
    data.Jahr = data.Jahr.astype("int")

    all_data.append(data)

complete_data = pd.concat(all_data).reset_index(drop=True)

# Entferne Duplikate bei den Wahlen
complete_data.drop_duplicates(
    subset=["Tag", "Monat", "Jahr", "Partei", "Art"],
    inplace=True
)

complete_data["Datum"] = pd.to_datetime(dict(year=complete_data.Jahr, month=complete_data.Monat, day=complete_data.Tag),
                                        errors="coerce")

print(complete_data.info())
print(complete_data)

# Schreibe die Daten in eine csv
complete_data.to_csv("sonntagsfrage.csv", index=False)

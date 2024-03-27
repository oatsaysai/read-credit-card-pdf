from pypdf import PdfReader
import re
import pandas as pd
import plotly.graph_objects as go
from cli_args_system import Args

args = Args(convert_numbers=False)
filename = args.flag_str("f", "filename", "")
password = args.flag_str("p", "password", "")

# Read PDF and convert to temp.csv
reader = PdfReader(stream=filename, password=password)

f = open("temp.csv", "w")
stop = False

for page in reader.pages:
    data = page.extract_text()
    for lineNum, line in enumerate(data.split("\n")):

        line = line.split("วันที่สรุปยอด", 1)[0]

        if "PREVIOUS BALANCE" in line:
            f.write(
                "||PREVIOUS BALANCE||" + line.split(" ")[2].replace(",", "", -1) + "\n"
            )

        pattern = "[0-9]{2}/[0-9]{2}/[0-9]{2} [0-9]{2}/[0-9]{2}/[0-9]{2}"
        if re.search(pattern, line):

            tmp = ""

            colInLine = line.split(" ")
            for i, x in enumerate(colInLine):
                if i <= 1:
                    f.write(x + "|")
                elif i == len(colInLine) - 3:
                    if ":" in x:
                        tmp = x
                    else:
                        f.write(x)
                elif i == len(colInLine) - 2 or i == len(colInLine) - 1:
                    if tmp != "":
                        x = tmp + x
                        tmp = ""
                    f.write("|" + x.replace(",", "", -1))
                else:
                    f.write(x + " ")

            f.write("\n")

        if "TOTAL BALANCE" in line:
            f.write(
                "||TOTAL BALANCE||" + line.split(" ")[4].replace(",", "", -1) + "\n"
            )
            stop = True
            break

    if stop:
        break

f.close()

# Read the CSV file into a DataFrame
colNames = ["TRANS DATE", "POSTING DATE", "DESCRIPTION", "REFERENCE", "AMOUNT"]
df = pd.read_csv(
    "temp.csv",
    delimiter="|",
    names=colNames,
    header=None,
    converters={"DESCRIPTION": str.strip},
)

# Convert amount to numeric
df["AMOUNT"] = pd.to_numeric(df["AMOUNT"])

# Remove some rows
df = df.drop(df[df["DESCRIPTION"] == "PAYMENT - THANK YOU - MOB"].index)
df = df.drop(df[df["DESCRIPTION"] == "PREVIOUS BALANCE"].index)
df = df.drop(df[df["DESCRIPTION"] == "TOTAL BALANCE"].index)

dfg = (
    df.groupby(["DESCRIPTION", "REFERENCE"])["AMOUNT"]
    .sum()
    .sort_values(ascending=True)
    .to_frame()
    .reset_index()
)
dfg["TEXT"] = dfg["DESCRIPTION"] + " (" + dfg["REFERENCE"] + ")"

fig = go.Figure(
    go.Bar(
        x=dfg["AMOUNT"],
        y=dfg["TEXT"],
        text=dfg["AMOUNT"],
        texttemplate="%{text:.2f}",
        orientation="h",
    )
)

latestDate = df["TRANS DATE"].iloc[len(df) - 1]
totalSum = "{:,.2f}".format(df["AMOUNT"].sum())

fig.update_layout(
    title={
        "text": "Latest Tx Date: {}, Total Sum {}".format(latestDate, totalSum),
        "y": 0.95,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
    }
)

fig.show()

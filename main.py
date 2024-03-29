from pypdf import PdfReader
import os
import re
import pandas as pd
import plotly
import plotly.graph_objects as go
from cli_args_system import Args
from pdfminer.high_level import extract_text
from datetime import datetime

args = Args(convert_numbers=False)
filename = args.flag_str("f", "filename", "")
password = args.flag_str("p", "password", "")
genHtml = args.flag_str("g", "gen-html", "")

bank = ""
date = ""

# parse text for find Bank
text = extract_text(pdf_file=filename, password=password)
if "KASIKORNBANK" in text:
    bank = "KASIKORNBANK"
elif "Citi" in text:
    bank = "CITIBANK"
elif "UOB" in text:
    bank = "UOB"
else:
    print("Support KASIKORNBANK, CITIBANK, UOB only")

# Read PDF and convert to temp.csv
reader = PdfReader(stream=filename, password=password)

csvFileName = filename.split(".")[0] + ".csv"
f = open(csvFileName, "w")

if bank == "CITIBANK":

    # flag for check data
    stop = False
    foundPreviousBalance = False
    dateFound = 2
    numbersFound = 0
    previousIsCreditCard = False
    name = ""

    descriptionArr = ["PREVIOUS BALANCE"]
    amountArr = []

    for lineNum, line in enumerate(text.split("\n")):
        line = line.strip()
        if line != "":

            if foundPreviousBalance:

                datePattern = r"^(0[1-9]|[12][0-9]|3[01])\s(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)$"
                numberPattern = r"^\d{1,3}(,\d{3})*\.\d{2}-?$"
                creditCardPattern = r"^\d{4}-\d{2}XX-XXXX-\d{4}$"
                notContainLower = r"^[^a-z]*$"
                if re.match(datePattern, line):
                    dateFound = dateFound + 1
                elif re.match(numberPattern, line) and numbersFound * 2 < dateFound:
                    amountArr.append(line)
                    numbersFound = numbersFound + 1
                elif re.match(creditCardPattern, line) and name == "":
                    previousIsCreditCard = True
                elif re.match(notContainLower, line) or " TH" in line:
                    if previousIsCreditCard:
                        name = line
                        previousIsCreditCard = False

                    if (
                        line != name
                        and line != "SUB-TOTAL"
                        and line != "TOTAL"
                        and numbersFound * 2 < dateFound
                    ):
                        if line == "BANGKOK TH":
                            descriptionArr[len(descriptionArr) - 1] = (
                                descriptionArr[len(descriptionArr) - 1] + line
                            )
                        else:
                            descriptionArr.append(line)
                else:
                    if "Total accounts" in line:
                        stop = True

                    if previousIsCreditCard:
                        name = line
                        previousIsCreditCard = False

            if line == "PREVIOUS BALANCE":
                foundPreviousBalance = True

            pattern = (
                r"^\d{1,2} (JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC) \d{2}$"
            )
            if re.match(pattern, line) and date == "":
                input_format = "%d %b %y"
                output_format = "%d/%m/%y"
                date_obj = datetime.strptime(line, input_format)
                date = date_obj.strftime(output_format)

        if stop:
            break

    for value in range(len(descriptionArr)):

        amountStr = str(amountArr[value]).replace(",", "")
        if "-" in amountStr:
            amountStr = "-" + amountStr.replace("-", "")

        ref = "TH"
        descriptionStr = descriptionArr[value]

        if "BANGKOK TH" in descriptionStr:
            ref = "BANGKOK TH"
            descriptionStr = descriptionStr.replace(ref, "")
        elif "SAMUTPRAKAN TH" in descriptionStr:
            ref = "SAMUTPRAKAN TH"
            descriptionStr = descriptionStr.replace(ref, "")
        elif " TH" in descriptionStr:
            ref = "TH"
            descriptionStr = descriptionStr.replace(" TH", "")

        data = f"{date}|{date}|{descriptionStr}|{ref}|{amountStr}\n"
        f.write(data)

# KASIKORN Bank Case
if bank == "KASIKORNBANK":
    stop = False
    for page in reader.pages:
        data = page.extract_text()

        for lineNum, line in enumerate(data.split("\n")):
            line = line.split("วันที่สรุปยอด", 1)[0]
            if "PREVIOUS BALANCE" in line:
                f.write(
                    "||PREVIOUS BALANCE||"
                    + line.split(" ")[2].replace(",", "", -1)
                    + "\n"
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

            # Support 26/02/2426/02/24 pattern
            pattern = "[0-9]{2}/[0-9]{2}/[0-9]{2}[0-9]{2}/[0-9]{2}/[0-9]{2}"
            if re.search(pattern, line):
                date = re.search(pattern, line).group(0)
                f.write(date[:8] + "|" + date[8:] + "|")

                line = re.sub(pattern, "", line)
                line = re.sub("USD\d{1,3}(,\d{3})*\.\d{2}", " ", line)
                line = re.sub("USD\d+(\.\d{2})?", " ", line)

                tmp = ""
                colInLine = line.split(" ")
                for i, x in enumerate(colInLine):
                    if i == len(colInLine) - 3:
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

# UOB
if bank == "UOB":
    stop = False
    for page in reader.pages:
        data = page.extract_text()

        for lineNum, line in enumerate(data.split("\n")):

            numberPattern = r"\b\d{1,3}(?:,\d{3})*\.\d{2}\b"
            datePattern = (
                r"\b(\d{2} (?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC))"
            )
            statementDate = (
                r"\b\d{2} (?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC) \d{4}\b"
            )

            if "STATEMENT DATE" in line:
                matches = re.findall(statementDate, line)
                input_format = "%d %b %Y"
                output_format = "%d/%m/%y"
                date_obj = datetime.strptime(matches[0], input_format)
                date = date_obj.strftime(output_format)
            elif re.search(numberPattern, line):
                if re.search(datePattern, line):
                    numberMatches = re.findall(numberPattern, line)
                    dateMatches = re.findall(datePattern, line)
                    # print(line)
                    # print(matches)
                    # print(dateMatches)

                    for data in numberMatches:
                        line = line.replace(data, "")

                    for data in dateMatches:
                        line = line.replace(data, "")

                    amountStr = str(numberMatches[len(numberMatches) - 1]).replace(
                        ",", ""
                    )
                    if "CR" in line:
                        line = line.replace("CR", "")
                        amountStr = "-" + amountStr

                    if "PAYMENT THANK YOU" not in line:
                        lineArr = line.strip().split(" ")
                        line = line.replace(lineArr[len(lineArr) - 1], "")
                        line = line.strip()
                        # print(lineArr)
                        # print(line)

                        f.write(
                            f"{date}|{date}|{line}|{lineArr[len(lineArr)-1]}|{amountStr}\n"
                        )

                elif "PREVIOUS BALANCE" in line:
                    numberMatches = re.findall(numberPattern, line)
                    if matches[0] != "0.00":
                        amountStr = str(numberMatches[0]).replace(",", "")
                        f.write(f"||PREVIOUS BALANCE||{amountStr}\n")

f.close()

# Read the CSV file into a DataFrame
colNames = ["TRANS DATE", "POSTING DATE", "DESCRIPTION", "REFERENCE", "AMOUNT"]
df = pd.read_csv(
    csvFileName,
    delimiter="|",
    names=colNames,
    header=None,
    converters={"DESCRIPTION": str.strip},
)

# Convert amount to numeric
df["AMOUNT"] = pd.to_numeric(df["AMOUNT"])

# Remove some rows
df = df.drop(df[df["DESCRIPTION"] == "PAYMENT PROMPTPAY"].index)
df = df.drop(df[df["DESCRIPTION"] == "PAYMENT - THANK YOU - MOB"].index)
df = df.drop(df[df["DESCRIPTION"] == "PAYMENT - OTHER"].index)
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

if date == "":
    date = df["TRANS DATE"].iloc[len(df) - 1]
totalSum = "{:,.2f}".format(df["AMOUNT"].sum())

fig.update_layout(
    title={
        "text": "Statement Date: {}, Total Sum {}".format(date, totalSum),
        "y": 0.95,
        "x": 0.5,
        "xanchor": "center",
        "yanchor": "top",
    }
)

os.remove(csvFileName)

if genHtml == "True":
    plotly.offline.plot(fig, filename=filename + ".html")
else:
    fig.show()

__author__ = 'calx'

from scbapi import ScbApi
from flask import Flask
from flask import render_template
from threading import Timer

app = Flask(__name__)
scb = ScbApi()

interval = 15.0
timer = None
table = None

class Table():
    def __init__(self, table_metadata, table_data, url, result, values, columns):
        self.table_metadata = table_metadata
        self.table_data = table_data
        self.url = url
        self.result = result
        self.values = values
        self.columns = columns


def orig_value_to_float(str_value):
    try:
        return float(str_value)
    except ValueError:
        return 0.0


def load_table():
    table_metadata = scb.get_random_table()
    print(table_metadata.data)
    table_data = scb.get_random_table_values()
    data = table_data.data["data"]
    print(data[0])
    columns = []
    i = 0
    for key in table_data.get_constant_keys():
        column = table_data.data["columns"][i]
        columns.append(column["text"]+"="+table_metadata.get_value_text_for_value(column["code"], key)+" ")
        i += 1
    values = []
    variable_code = table_data.get_variable_code()
    variable_col_ind = table_data.get_column_index(variable_code)
    for datum in data:
        values.append({"name": datum["key"][variable_col_ind],
                       "origValue": datum["values"][0],
                       "value": orig_value_to_float(datum["values"][0])})

    result = "resultat = "+str(table_data.get_content_column()["text"])
    print(table_data.data["columns"])
    print(result)
    print(values)

    global table
    global timer
    table = Table(table_metadata, table_data, scb.get_location(), result, values, columns)
    timer = Timer(interval, load_table)
    timer.start()


@app.route("/")
def index():
    return render_template("index.html",
                           title=table.table_metadata.data["title"],
                           tableUrl=table.url,
                           unit=table.result,
                           valuesY=table.values,
                           columns=table.columns)


if __name__ == "__main__":
    load_table()
    app.run(debug=True)
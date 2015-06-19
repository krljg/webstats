__author__ = 'calx'

from scbapi import ScbApi
from flask import Flask
from flask import render_template
from threading import Timer
import traceback
import sys

app = Flask(__name__)
scb = ScbApi("en")

interval = 15.0
timer = None
table = None
ended = False

class Table():
    def __init__(self, table_metadata, table_data, url, result, values, columns, c3values):
        self.table_metadata = table_metadata
        self.table_data = table_data
        self.url = url
        self.result = result
        self.values = values
        self.columns = columns
        self.c3data = dict()
        #self.c3data["columns"] = c3values
        self.c3data = c3values


def orig_value_to_float(str_value):
    try:
        return float(str_value)
    except ValueError:
        return 0.0


def convert_time(orig_value):
    if len(orig_value) == 4:
        return orig_value+"-1-1"
    elif len(orig_value) == 6:

        # Assume 2001K1 type (also possible 2001k1)
        if orig_value.endswith("1"):
            return orig_value[:4]+"-3-31"
        elif orig_value.endswith("2"):
            return orig_value[:4]+"-6-30"
        elif orig_value.endswith("3"):
            return orig_value[:4]+"-9-30"
        elif orig_value.endswith("4"):
            return orig_value[:4]+"-12-31"
    elif len(orig_value) == 7:
        # Assume 2003M04 type value
        return orig_value[:4]+"-"+orig_value[4:]+"1"
    elif len(orig_value) == 9:
        # Assume 2011-M041 type value
        return orig_value[:4]+"-"+orig_value[6:8]+"-"+orig_value[-1]


    return orig_value
def restart_timer():
    global timer
    timer = Timer(interval, load_table)
    timer.start()

def load_table():
    try:
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
        result = str(table_data.get_content_column()["text"])
        values = []
        c3values = [['x'], ["data1"]]
        #c3values = ["data1"]
        variable_code = table_data.get_variable_code()
        variable_col_ind = table_data.get_column_index(variable_code)
        for datum in data:
            c3values[0].append(convert_time(datum["key"][variable_col_ind]))
            c3values[1].append(orig_value_to_float(datum["values"][0]))
            #c3values.append(orig_value_to_float(datum["values"][0]))
            values.append({"name": datum["key"][variable_col_ind],
                           "origValue": datum["values"][0],
                           "value": orig_value_to_float(datum["values"][0])})

        print(table_data.data["columns"])
        print(result)
        print(values)

        global table
        table = Table(table_metadata, table_data, scb.get_location(), result, values, columns, c3values)
    except Exception as ex:
        print(ex)
        sys.stderr.write(traceback.format_exc())
        #print(traceback.format_exc())
    if not ended:
        restart_timer()

@app.route("/")
def index():
    return render_template("index.html",
                           title=table.table_metadata.data["title"],
                           tableUrl=table.url,
                           unit=table.result,
                           valuesY=table.values,
                           columns=table.columns,
                           c3data=table.c3data)


if __name__ == "__main__":
    load_table()
    app.run(debug=True)
    ended = True
    timer.cancel()
__author__ = 'calx'

from scbapi import ScbApi
from flask import Flask
from flask import render_template

app = Flask(__name__)
scb = ScbApi()

def orig_value_to_float(str_value):
    try:
        return float(str_value)
    except ValueError:
        return 0.0

@app.route("/")
def index():
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

    #var_key = table_data.get_variable_code()
    result = "resultat = "+str(table_data.get_content_column()["text"])
    print(table_data.data["columns"])
    print(result)
    print(values)
    #print(var_key)
    #print(table_metadata.get_values(var_key))
    return render_template("index.html",
                           title=table_metadata.data["title"],
                           tableUrl=scb.get_location(),
                           unit=result,
                           valuesY=values,
                           columns=columns)


if __name__ == "__main__":
    app.run(debug=True)
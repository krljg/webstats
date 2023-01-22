import requests
import random
import json
import logging


__author__ = 'calx'

baseUrl = "https://api.scb.se/OV0104/v1/doris/"


def get(url, expected=200):
    response = requests.get(url)
    if response.status_code != expected:
        raise Exception("Unexpected response from url= "+url+"-> "+str(response.status_code)+": "+response.text)
    return response.json()


def orig_value_to_float(str_value):
    try:
        return float(str_value)
    except ValueError:
        return 0.0


def convert_time(orig_value):
    if len(orig_value) == 4:
        # Just a year
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
        return orig_value[:4]+"-"+orig_value[5:]+"-1"
    elif len(orig_value) == 9:
        # Assume 2011-M041 type value
        return orig_value[:4]+"-"+orig_value[6:8]+"-"+orig_value[-1]


class ScbApi:
    def __init__(self, lang="sv"):
        self.lang = lang
        self.current = baseUrl+self.lang+"/ssd/"
        self.current_data = None
        self.cache = {}

    def cached_get(self, url):
        if url in self.cache:
            return self.cache[url]
        data = get(url)
        self.cache[url] = data
        return data

    def get_location(self):
        return self.current

    def get_current(self):
        self.current_data = self.cached_get(self.current)
        return self.current_data

    def get_sub(self, id):
        sub = self.current + id + "/"
        self.current_data = self.cached_get(sub)
        self.current = sub
        return self.current_data

    def get_super(self):
        s = self.current.split("/")
        sup = "/".join(s[:-1])
        self.current_data = self.cached_get(sup)
        self.current = sup
        return self.current_data

    def get_random_table(self):
        self.current = baseUrl+self.lang+"/ssd/"
        self.get_current()
        while not self.is_at_table():
            self.get_sub(random.choice(self.current_data)['id'])
        return Table(self.current_data, self.current)
        #return TableMetaData(self.current_data)

    def is_at_table(self):
        return isinstance(self.current_data, dict)

    @staticmethod
    def create_variable_selection(code, choice):
        if choice is None:
            selection = {"filter": "all", "values": ["*"]}
        else:
            selection = {"filter": "item", "values": [choice]}
        return {'code': code, 'selection': selection }

    def get_random_table_values(self, scbTable):
        query = []
        allVariable = None

        allVariable, constantVariables = scbTable.get_query_variables()
        query.append(self.create_variable_selection(allVariable, None))
        for constantVariable in constantVariables:
            query.append(self.create_variable_selection(constantVariable[0], constantVariable[1]))
        resp = {"format": "json"}
        jreq = {"query": query, "response": resp}

        logging.info("Query: "+str(jreq))
        logging.info("Location: "+str(self.current))
        response = requests.post(self.current, data=json.dumps(jreq))

        if response.status_code != 200:
            raise Exception("Unexpected response "+str(response.status_code)+": "+response.text)

        logging.info("response.text: "+response.text)

        rspStr = json.loads(response.text[1:])
        scbTable.add_data(rspStr, allVariable)
        #return TableData(json.loads(response.text[1:]), allVariable)

    def get_random_table_values_old(self):
        query = []
        allVariable = None
        # todo: move selected variable into table meta data so we can make multiple queries for the same table
        #       without repetitions
        for variable in self.current_data["variables"]:
            code = variable['code']
            if code == 'Tid':
                selection = {"filter": "all", "values": ["*"]}
                allVariable = variable
            else:
                selection = {"filter": "item", "values": [random.choice(variable["values"])]}
            jvar = {'code': variable['code'], 'selection': selection}
            query.append(jvar)

        resp = {"format": "json"}
        jreq = {"query": query, "response": resp}
        #print(json.dumps(jreq))
        logging.info("Query: {}".format(jreq))
        logging.info("Location: {}".format(self.current))
        response = requests.post(self.current, data=json.dumps(jreq))
        if response.status_code != 200:
            raise Exception("Unexpected response "+response.status_code+": "+response.text)
        return TableData(json.loads(response.text[1:]), allVariable)
        #return response.text


class Table:
    def __init__(self, metadata, location):
        self.metadata = metadata
        self.location = location
        self.data = None
        self.variable = None

    def get_variables(self):
        return self.metadata["variables"]

    def get_value_text_for_value(self, code, value):
        for variable in self.get_variables():
            if variable["code"] == code:
                values = variable["values"]
                for valueIndex in range(0, len(values)):
                    if value == values[valueIndex]:
                        return variable["valueTexts"][valueIndex]
        return value

    def get_values(self, code):
        for variable in self.get_variables():
            if variable["code"] == code:
                return variable["values"]
        return []

    def get_title(self):
        return self.metadata["title"]

    def get_location(self):
        return self.location

    # todo: need to keep track of already received data so we don't ask for stuff we already have
    # todo: support tables that don't have  a 'Tid' column
    def get_query_variables(self):
        # print("metadata:")
        # print(self.metadata)
        constants = []
        variables = self.metadata["variables"]
        allVariable = None
        for variable in variables:
            code = variable['code']
            if code == 'Tid':
                allVariable = variable['code']
            else:
                constants.append((variable['code'], random.choice(variable["values"])))
        if allVariable is None:
            code_value = random.choice(constants)
            constants.remove(code_value)
            allVariable = code_value[0]
        return allVariable, constants

    # Return a list of tuples with column name and set value
    def get_constants(self):
        columns = []
        i = 0
        for key in self.get_constant_keys():
            column = self.data["columns"][i]
            text = self.get_value_text_for_value(column["code"], key)
            columns.append((column["text"], text))
            i += 1
        return columns

    # Return the value text for the content column
    def get_content(self):
        return str(self.get_content_column()["text"])

    # todo: take already fetched data into consideration
    def add_data(self, data, variable):
        self.data = data
        self.variable = variable

    def get_constant_keys(self):
        data = self.data["data"]
        if data is None or len(data) == 0:
            return []
        if len(data) == 1:
            return data[0]["key"]
        else:
            c_keys = []
            for i in range(0, len(data[0]["key"])):
                if data[0]["key"][i] == data[1]["key"][i]:
                    c_keys.append(data[0]["key"][i])
            return c_keys

    def get_code(self, index):
        return self.data["columns"][index]["code"]

    def get_variable_code(self):
        data = self.data["data"]
        if data is None or len(data) <= 1:
            return None
        for i in range(0, len(data[0]["key"])):
                if data[0]["key"][i] != data[1]["key"][i]:
                    return self.get_code(i)

        return None

    def get_unit(self):
        for column in self.data["columns"]:
            if "unit" in column:
                return column["unit"]
        return None

    def get_content_column(self):
        for column in self.data["columns"]:
            if column["type"] == "c":
                return column
        raise KeyError("A column with 'type==c' does not exist in "+str(self.data["columns"]))

    def get_column_index(self, code):
        for i in range(0, len(self.data["columns"])):
            if self.data["columns"][i]["code"] == code:
                return i
        raise KeyError(code + " does not exist in "+str(self.data["columns"]))

    def get_c3_values(self):
        c3values = [['x'], ["data1"]]
        variable_code = self.get_variable_code()
        variable_col_ind = self.get_column_index(variable_code)
        if self.data is None:
            return c3values
        for datum in self.data["data"]:
            c3values[0].append(convert_time(datum["key"][variable_col_ind]))
            c3values[1].append(orig_value_to_float(datum["values"][0]))
        return c3values

    def print(self):
        print("# "+self.get_title())
        print("location: "+self.location)
        print("metadata:")
        print(self.metadata)
        print("data:")
        print(self.data)

    @staticmethod
    def pad(length, char=" "):
        text = ""
        if length > 0:
            for i in range(0, length):
                text += char
        return text

    def calculate_widths(self):
        widths = {}
        columns = self.data["columns"]
        for column in columns:
            widths[column["code"]] = len(column["text"])
        for datum in self.data["data"]:
            i = 0
            for key in datum["key"]:
                code = columns[i]["code"]
                value = self.get_value_text_for_value(code, key)
                width = len(value)
                if widths[code] < width:
                    widths[code] = width
                i += 1
        return widths

    def values_as_table_str(self):
        text = ""
        if self.data is None:
            return text
        columns = self.data["columns"]
        line1 = "|"
        line2 = "|"
        logging.info("columns: "+str(columns))
        widths = self.calculate_widths()
        for column in columns:
            coltext = column["text"]
            line1 += coltext + self.pad(widths[column["code"]] - len(coltext))
            line2 += self.pad(widths[column["code"]], "-")
            line1 += "|"
            line2 += "|"
        text += line1 + "\n" + line2 + "\n"
        for datum in self.data["data"]:
            text += "|"
            i = 0
            for key in datum["key"]:
                code = columns[i]["code"]
                value = self.get_value_text_for_value(code, key)
                text += value + self.pad(widths[code]-len(value))+"|"
                i += 1
            value = str(datum["values"])
            text += value + self.pad(widths[columns[-1]["code"]]-len(value))+"|\n"
        return text

    def __str__(self):
        text = "# "+self.get_title()
        if self.location is None:
            text += "\n  location: <none>"
        else:
            text += "\n location: "+self.location
        if self.metadata is None:
            text += "\n  metadata: <none>"
        else:
            text += "\n metadata: "+str(self.metadata)
        if self.data is None:
            text += "\n data: <none>"
        else:
            text += "\n data: "+str(self.data)
            text += "\n"+self.values_as_table_str()
        return text


class TableData:
    def __init__(self, data, variable):
        self.data = data
        self.variable = variable

    def get_constant_keys(self):
        data = self.data["data"]
        if data is None or len(data) == 0:
            return []
        if len(data) == 1:
            return data[0]["key"]
        else:
            c_keys = []
            for i in range(0, len(data[0]["key"])):
                if data[0]["key"][i] == data[1]["key"][i]:
                    c_keys.append(data[0]["key"][i])
            return c_keys

    def get_code(self, index):
        return self.data["columns"][index]["code"]

    def get_variable_code(self):
        data = self.data["data"]
        if data is None or len(data) <= 1:
            return None
        for i in range(0, len(data[0]["key"])):
                if data[0]["key"][i] != data[1]["key"][i]:
                    return self.get_code(i)
                    #return data[0]["key"][i]

        return None

    def get_unit(self):
        for column in self.data["columns"]:
            if "unit" in column:
                return column["unit"]
        return None

    def get_content_column(self):
        for column in self.data["columns"]:
            if column["type"] == "c":
                return column

    def get_variable_code(self):
        return self.variable['code']

    def get_column_index(self, code):
        for i in range(0, len(self.data["columns"])):
            if self.data["columns"][i]["code"] == code:
                return i


class TableMetaData:
    def __init__(self, data):
        self.data = data

    def get_variables(self):
        return self.data["variables"]

    def get_value_text_for_value(self, code, value):
        for variable in self.get_variables():
            if variable["code"] == code:
                values = variable["values"]
                for valueIndex in range(0, len(values)):
                    if value == values[valueIndex]:
                        return variable["valueTexts"][valueIndex]
        return value

    def get_values(self, code):
        for variable in self.get_variables():
            if variable["code"] == code:
                return variable["values"]
        return []


def print_hex_str(s):
    print(":".join("{:02x}".format(ord(c)) for c in s))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    scb = ScbApi()
    table = scb.get_random_table()
    print(scb.get_location())
    print(table.get_title())
    for variable in table.get_variables():
        print(variable)
    tv = scb.get_random_table_values(table)
    #print_hex_str(tv)
    #print("'"+tv+"'")
    #print(json.loads(tv[1:]))
    print(tv)
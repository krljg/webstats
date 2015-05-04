__author__ = 'calx'

import requests
import random
import json

baseUrl = "http://api.scb.se/OV0104/v1/doris/en/ssd/"

def get(url, expected=200):
    response = requests.get(url)
    if response.status_code != expected:
        raise Exception("Unexpected response from url= "+url+"-> "+str(response.status_code)+": "+response.text)
    return response.json()

class ScbApi():
    def __init__(self):
        self.lang = "sv"
        self.current = "http://api.scb.se/OV0104/v1/doris/"+self.lang+"/ssd/"
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
        self.current = "http://api.scb.se/OV0104/v1/doris/"+self.lang+"/ssd/"
        self.get_current()
        while not self.is_at_table():
            self.get_sub(random.choice(self.current_data)['id'])
        return TableMetaData(self.current_data)

    def is_at_table(self):
        return isinstance(self.current_data, dict)

    def get_random_table_values(self):
        query = []
        allVariable = None
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
        response = requests.post(self.current, data=json.dumps(jreq))
        if response.status_code != 200:
            raise Exception("Unexpected response "+response.status_code+": "+response.text)
        return TableData(json.loads(response.text[1:]), allVariable)
        #return response.text

class TableData():
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

class TableMetaData():
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
    scb = ScbApi()
    table = scb.get_random_table()
    print(scb.get_location())
    print(table["title"])
    for variable in table["variables"]:
        print(variable)
    tv = scb.get_random_table_values()
    #print_hex_str(tv)
    #print("'"+tv+"'")
    #print(json.loads(tv[1:]))
    print(tv)
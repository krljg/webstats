# Web Stats

A web server that shows random graphs using statistics from [Statistiska Centralbyrån (Statistics Sweden)](http://www.scb.se/).

## How to Run

Install the required dependencies in the requirements.txt file

`pip install -r requirements.txt`

Then you should be able to run webstats:

`python webstats.py`

Once it's running you can point your web browser at http://localhost:5000
and you should see graphs and stuff.

#### If You Are Using Virtualenv You Can Do This

```
$ virtualenv webstats
$ source webstats/bin/activate
$ pip install -r requirements.txt
$ python webstats.py
```

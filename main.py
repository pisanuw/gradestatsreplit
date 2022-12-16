from flask import Flask, render_template, request
import statistics
from matplotlib.figure import Figure
import base64
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

decBuckets = [50, 60, 70, 80, 90]


def buckets2labels(buckets):
  label = []
  label.append("<" + str(buckets[0]))
  i = 1
  while i < len(buckets):
    label.append(str(buckets[i - 1]) + "-" + str(buckets[i]))
    i = i + 1
  label.append(">=" + str(buckets[-1]))
  label.append("NaN")
  return label


def process_post():
  ip_addr = request.environ['REMOTE_ADDR']
  dateTimeObj = datetime.now()
  with open('log.txt', 'a') as f:
    f.write(str(dateTimeObj) + ": " + ip_addr + "\n")
  return "<h3>Grades received</h3>\n" + \
      plot_png() + \
      "<p><a href=\"/\">" + \
      "Back to submit more grades (/)</a><p>\n"


@app.route("/", methods=['POST', 'GET'])
def hello_world():
  if request.method == 'GET':
    return render_template('input-grades.html')
  else:
    return process_post()


def plot_png():
  fig = create_bar_plot()
  buf = BytesIO()
  fig.savefig(buf, format="png")
  data = base64.b64encode(buf.getbuffer()).decode("ascii")
  return f"<img src='data:image/png;base64,{data}'/>"


def create_bar_plot():
  fig = Figure()
  axis = fig.add_subplot(1, 1, 1)
  global decBuckets
  decBuckets = [int(x) for x in request.form['cutoffs'].split('\n') if x.strip() != ""]
  props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
  data = [x for x in request.form['grades'].split('\n') if x.strip() != ""]
  textstr = get_dist_stats(data)
  axis.text(0.02,
            0.95,
            textstr,
            transform=axis.transAxes,
            fontsize=10,
            verticalalignment='top',
            bbox=props)
  # xs = ["<50", "50-59", "60-69", "70-79", "80-89", ">=90", "NaN"]
  xs = buckets2labels(decBuckets)
  ys = data_into_buckets(data)
  axis.bar(xs, ys)
  axis.set_xlabel("Decimal Grades")
  axis.set_ylabel("# of Students")
  # fig.suptitle("Course Number")
  return fig


def get_dist_stats(data):
  intData = [int(x) for x in data if isInt(x)]
  stdevA = "0"
  if len(intData) > 1:
    stdevA = str(round(statistics.stdev(intData), 1))
  textstr = '\n'.join(
    ("Total: " + str(len(data)),
     "Mean: " + str(round(statistics.mean(intData), 1)),
     "Median: " + str(round(statistics.median(intData), 1)),
     "Mode: " + str(round(statistics.mode(intData), 1)), "Stdev: " + stdevA,
     "Min: " + str(round(min(intData), 1)),
     "Max: " + str(round(max(intData), 1)),
     "Dist: [" + ", ".join([str(x) for x in data_into_buckets(data)]) + "]"))
  return textstr


def data_into_buckets(data):
  # buckets = [0, 0, 0, 0, 0, 0, 0]
  buckets = [0] * (len(decBuckets) + 2)
  # ["<50", "50-59", "60-69", "70-79", "80-89", ">=90", "NaN"]
  for grade in data:
    if not isInt(grade):
      buckets[-1] = buckets[-1] + 1
      continue
    else:
      grade = int(grade)
    i = 0
    inserted = False
    while not inserted and i < len(decBuckets):
      if grade < decBuckets[i]:
        inserted = True
        buckets[i] = buckets[i] + 1
      i = i + 1
    if not inserted:
      buckets[-2] = buckets[-2] + 1
  return buckets


def isInt(s):
  try:
    int(s)
    return True
  except ValueError:
    return False


app.run(host='0.0.0.0', port=8080)
import time
import os
import RPi.GPIO as io
io.setmode(io.BCM)
import datetime
import pytz
 
PIR_PIN = 17

MOTION_ON_TIME = 300  # seconds
SLEEP_BETWEEN_CYCLES = 2  # seconds

io.setup(PIR_PIN, io.IN)
 
class Activity(object):
  def __init__(self, input_pin):
    self.input_pin = input_pin
    

class LightActivity(Activity):
  def __init__(self, input_pin):
    super(self.__class__, self).__init__(input_pin)
    self.on_state = None
    self.off_time = time.time()

  def poll(self):
    """Run light activity functionality."""
    if io.input(self.input_pin):
      self.off_time = time.time() + MOTION_ON_TIME
        
      if not self.on_state:
        self.on_state = True
        os.system("wemo switch \"Room\" on")
        time.sleep(2)
        os.system("wemo switch \"Room\" on")

    if time.time() > self.off_time:
      if self.on_state:
        self.on_state = False
        os.system("wemo switch \"Room\" off")
        time.sleep(2)
        os.system("wemo switch \"Room\" off")

    time.sleep(SLEEP_BETWEEN_CYCLES)


class ActivityTimeRange(object):
  def __init__(self, start, end, activity):
    self.start = start
    self.end = end
    self.activity = activity


class ActivityProfile(object):
  def __init__(self, time_ranges):
    self.time_ranges = time_ranges if time_ranges else []
    self.current_time_range = None

  def poll(self):
    current_hour = datetime.datetime.now(pytz.timezone('US/Pacific')).hour

    time_range = self._findTimeRange(current_hour)
    if time_range is None:
      self._sleepUntilNextTimeRange(current_hour)
      return

    if self.current_time_range != time_range:
      self.current_time_range = time_range

    if self.current_time_range.activity:
      self.current_time_range.activity.poll()
    else:
      self._sleepUntilNextTimeRange(current_hour)

  def _sleepUntilNextTimeRange(self, current_hour):
    # Case handling 0 and 1 TimeRange entries
    pass

    # More than one TimeRange
    next_range = None
    for time_range in self.time_ranges:
      time_till_next_range = time_range.start - current_hour
      if time_till_next_range < 0:
        time_till_next_range + 24

      if not next_range:
        next_range = time_range
      elif next_range.start - current_hour < time_till_next_range:
        next_range = time_range
          
    # Sleep until next TimeRange
    t = datetime.datetime.now(pytz.timezone('US/Pacific'))
    future = datetime.datetime(t.year, t.month, t.day, next_range.start, 0, tzinfo=t.tzinfo)
    time.sleep((future-t).seconds)

  def _findTimeRange(self, current_hour):
    for time_range in self.time_ranges:
      if time_range.start <= current_hour < time_range.end:
        return time_range
    return None
    

def main():
  morning = ActivityTimeRange(start=6, end=11, activity=LightActivity(input_pin=PIR_PIN))
  afternoon = ActivityTimeRange(start=11, end=18, activity=None)
  evening = ActivityTimeRange(start=18, end=24, activity=LightActivity(input_pin=PIR_PIN))
  activity_profile = ActivityProfile(time_ranges=[morning, afternoon, evening])

  while 1:
    activity_profile.poll()


if __name__ == '__main__':
  main()

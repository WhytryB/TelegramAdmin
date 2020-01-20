from datetime import datetime

date_now = datetime.now()
date_was = datetime(date_now.year, date_now.month, date_now.day-1,
               date_now.hour, date_now.minute, date_now.second)
dif = date_now - date_was
print(dif.total_seconds()/60/60)
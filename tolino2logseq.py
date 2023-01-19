from datetime import datetime
from typing import List
from hashlib import md5
import os
import re

day_endings = {
  1: 'st',
  2: 'nd',
  3: 'rd',
  21: 'st',
  22: 'nd',
  23: 'rd',
  31: 'st'
}

logseq_folder = os.path.join(os.getcwd(), "pages")

class TolinoHighlight():
  def __init__(self, title: str, page: str, date: datetime, marker: str, note: str = None):
    self.id = md5(f"{title}{page}{date}{marker}{note or ''}".encode()).hexdigest()
    self.title = title
    self.page = page
    day = date.day
    day = day + day_endings if int(day) in day_endings else f"{day}th"
    month = date.strftime("%h")
    year = date.year
    self.date = f"{month} {day}, {year}"
    self.marker = marker
    self.note = note
  
  def to_markdown(self):
    nl = "\n"
    s = f"""	- {self.title}
	      date_saved:: [[{self.date}]]
        page:: {self.page}
		- > {self.marker}
    {f'  - *Note:*{nl}        > {self.note}' if self.note else ''}"""
    return s
  
  # def to_markdown(self):
  #   s = f"""  - **{self.title}**
  #       date_saved:: [[{self.date}]]
  #       page:: {self.page}
  #     - *Marked text:*
  #       > {self.marker}"""
  #   if self.note:
  #     s += f"\n      - *Note:*\n        > {self.note}"
  #   return s

devices = os.listdir("/run/user/1000/gvfs")
tolino_dir = next(
    (os.path.join(f"/run/user/1000/gvfs/{device}")
     for device in devices if "tolino" in device),
    None,
)
if not tolino_dir:
  print("No tolino device detected!")
  exit(1)

shared_storage = os.path.join(tolino_dir, os.listdir(tolino_dir)[0])

with open(os.path.join(shared_storage, "notes.txt"), "r") as f:
  data = f.read().split("-----------------------------------")[:-1]
  data = [line.strip() for line in data]


highlights: List[TolinoHighlight] = []
ids: List[str] = []
for line in data:
  title = line.splitlines()[0]
  date = re.findall(r'[^\d]+(\d+\.\d+\.\d+\s\|\s\d+:\d+).*', line)[0]
  date = datetime.strptime(date, "%d.%m.%Y | %H:%M")

  if line.splitlines()[1].startswith("Notiz"):
    note = re.findall(r'\d+:\s([^\"]+)', line, flags=re.MULTILINE)[0].strip()
    marker = re.findall(r'\d+:\s[^\"]+\n\"([^\"]+)', line, flags=re.MULTILINE)[0]
    marker = re.sub(r'\n\s+', r' ', marker)
    page = re.findall(r'(\d+):\s[^\"]+', line)[0]
    th = TolinoHighlight(
      title=title,
      page=page,
      date=date,
      marker=marker,
      note=note
    )
    if th.id not in ids:
      highlights.append(th)
      ids.append(th.id)
  elif "Markierung" in line:
    marker = re.findall(r'\d+:\s\"([^\"]+)\"', line, flags=re.MULTILINE)[0]
    marker = re.sub(r'\n\s+', r' ', marker)
    page = re.findall(r'(\d+): \"', line)[0]
    th = TolinoHighlight(
      title=title,
      page=page,
      date=date,
      marker=marker
    )
    if th.id not in ids:
      highlights.append(th)
      ids.append(th.id)

with open(os.path.join(logseq_folder, "TolinoHighlights.md"), "w") as f:
  f.write("- ## 📕 Tolino Highlights\n")
  for highlight in highlights:
    f.write(highlight.to_markdown())
    f.write("\n\n")
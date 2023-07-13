from datetime import datetime
import flask
from webapp.spreadsheet import get_sheet, MissingCredential


SPREADSHEET_ID = "1fFumFWIM3oHwLr9pcBlaANcadAU0bNJxbkfGKwC_1pg"

masterclasses = flask.Blueprint(
    "masterclasses",
    __name__,
    template_folder="/templates",
    static_folder="/static",
)


def get_value_row(row, type):
    if row:
        if type == datetime:
            if "formattedValue" in row:
                return {
                    "Formatted": datetime.strptime(
                        row["formattedValue"], "%d %B %Y"
                    ).strftime("%d %b %Y"),
                    "Object": datetime.strptime(
                        row["formattedValue"], "%d %B %Y"
                    ),
                }
        elif "userEnteredValue" in row:
            if "stringValue" in row["userEnteredValue"]:
                if (
                    "userEnteredFormat" in row
                    and "textFormat" in row["userEnteredFormat"]
                    and "link" in row["userEnteredFormat"]["textFormat"]
                ):
                    return row["userEnteredFormat"]["textFormat"]["link"][
                        "uri"
                    ]
                return type(row["userEnteredValue"]["stringValue"])
            if "numberValue" in row["userEnteredValue"]:
                return type(row["userEnteredValue"]["numberValue"])

    return ""


def index_in_list(a_list, index):
    return index < len(a_list)


# Parse the id from a google url
# https://drive.google.com/open?id=15cy6HFRkzgidDQ1Ff1wBDP-TVihfg_15
# https://drive.google.com/file/d/1YkOAdSwmAHmddwhQ2l0sbEQyflbkhQ5L/view
# https://drive.google.com/file/d/1nCbTZtX380e6lD1kkQ6BjTA0aAknZJGY/view?usp=drivesdk
# https://drive.google.com/file/d/1TQLA53RPhf20Q9BeqMN6e1DFb_kPsF91/view?usp=drive_web
def get_id(video_link):
    if video_link:
        if "id=" in video_link:
            return video_link.split("id=")[1]
        elif "file/d/" in video_link:
            return video_link.split("file/d/")[1].split("/view")[0]
    return ""


@masterclasses.route("/")
def index():
    previous_sessions = get_previous_sessions()
    upcoming_sessions = get_upcoming_sessions()
    tags = get_tags()

    return flask.render_template(
        "masterclasses.html",
        previous_sessions=previous_sessions,
        upcoming_sessions=upcoming_sessions,
        tags=tags,
    )


def get_upcoming_sessions():
    try:
        sheet = get_sheet()
    except MissingCredential as error:
        flask.abort(500, str(error))

    SHEET = "Upcoming"
    RANGE = "A2:E1000"
    COLUMNS = [
        ("Topic", str),
        ("Owner", str),
        ("Duration", str),
        ("Date", datetime),
        ("Notes", str),
        ("Event", str),
    ]
    res = sheet.get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=[f"{SHEET}!{RANGE}"],
        includeGridData=True,
    ).execute()

    sessions = []
    for row in res["sheets"][0]["data"][0]["rowData"]:
        if _has_row_value(row):
            session = {}
            for column_index in range(len(COLUMNS)):
                (column, type) = COLUMNS[column_index]
                session[column] = get_value_row(
                    row["values"][column_index]
                    if index_in_list(row["values"], column_index)
                    else None,
                    type,
                )
                if COLUMNS[column_index][0] == "Recording":
                    session["Link"] = get_id(session[column])

            sessions.append(session)

    return sessions


def get_previous_sessions():
    try:
        sheet = get_sheet()
    except MissingCredential as error:
        flask.abort(500, str(error))

    SHEET = "Completed"
    RANGE = "A2:I1000"
    COLUMNS = [
        ("Topic", str),
        ("Owner", str),
        ("Duration", str),
        ("Date", datetime),
        ("Slides", str),
        ("Recording", str),
        ("Description", str),
        ("Chat log", str),
        ("Tags", str),
    ]
    res = sheet.get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=[f"{SHEET}!{RANGE}"],
        includeGridData=True,
    ).execute()

    sessions = []
    for row in res["sheets"][0]["data"][0]["rowData"]:
        if "values" in row and row["values"][0]:
            session = {}
            for column_index in range(len(COLUMNS)):
                (column, type) = COLUMNS[column_index]
                session[column] = get_value_row(
                    row["values"][column_index]
                    if index_in_list(row["values"], column_index)
                    else None,
                    type,
                )
                if COLUMNS[column_index][0] == "Recording":
                    session["Link"] = get_id(session[column])

            sessions.append(session)

    # Sort sessions by date
    sessions.sort(key=lambda x: x["Date"]["Object"], reverse=True)

    return sessions

def get_tags():
    try:
        sheet = get_sheet()
    except MissingCredential as error:
        flask.abort(500, str(error))

    SHEET = "Completed"
    RANGE = "I2:I1000"
    COLUMNS = [
        ("Tag", str),
    ]
    res = sheet.get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=[f"{SHEET}!{RANGE}"],
        includeGridData=True,
    ).execute()

    tags = {}
    for row in res["sheets"][0]["data"][0]["rowData"]:
        if "values" in row and row["values"][0]:
            for column_index in range(len(COLUMNS)):
                (column, type) = COLUMNS[column_index]
                temp_tag = get_value_row(
                    row["values"][column_index]
                    if index_in_list(row["values"], column_index)
                    else None,
                    type,
                )
                for tag in temp_tag.strip().split(","):
                    tag = tag.strip()
                    if tag:
                        if tag not in tags:
                            tags[tag] = 1
                        else:
                            tags[tag] += 1
    return tags


def _has_row_value(row):
    if (
        "values" in row
        and row["values"][0]
        and "userEnteredValue" in row["values"][0]
    ):
        return True
    return False

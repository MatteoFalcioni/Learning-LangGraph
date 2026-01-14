from langchain_google_community import GmailToolkit, CalendarToolkit
from langchain_google_community.calendar.utils import get_google_credentials

# Can review scopes here: https://developers.google.com/calendar/api/auth
# For instance, readonly scope is https://www.googleapis.com/auth/calendar.readonly
google_credentials = get_google_credentials(
    token_file="token.json",
    scopes=["https://mail.google.com/", "https://www.googleapis.com/auth/calendar"],
    client_secrets_file="credentials.json",
)

# Initialize Toolkits
calendar_toolkit = CalendarToolkit(credentials=google_credentials)

gmail_toolkit = GmailToolkit(credentials=google_credentials)

# Filter out the email sending tool - only allow reading/searching/creating drafts
gmail_tools = [
    tool for tool in gmail_toolkit.get_tools() 
    if tool.name != "send_gmail_message"
]

# Filter calendar tools to only include: CalendarCreateEvent, CalendarSearchEvents, GetCalendarsInfo, GetCurrentDatetime
allowed_calendar_tools = [
    "create_calendar_event",
    "search_events", 
    "get_calendars_info",
    "get_current_datetime"
]

calendar_tools = [
    tool for tool in calendar_toolkit.get_tools()
    if tool.name in allowed_calendar_tools
]

google_tools = gmail_tools + calendar_tools

if __name__ == "__main__":
    print([tool.name for tool in google_tools])






'''
[GmailCreateDraft(api_resource=<googleapiclient.discovery.Resource object at 0x7c47478d6350>), 
GmailSendMessage(api_resource=<googleapiclient.discovery.Resource object at 0x7c47478d6350>), 
GmailSearch(api_resource=<googleapiclient.discovery.Resource object at 0x7c47478d6350>), 
GmailGetMessage(api_resource=<googleapiclient.discovery.Resource object at 0x7c47478d6350>), 
GmailGetThread(api_resource=<googleapiclient.discovery.Resource object at 0x7c47478d6350>), 
CalendarCreateEvent(api_resource=<googleapiclient.discovery.Resource object at 0x7c474771ff50>), 
CalendarSearchEvents(api_resource=<googleapiclient.discovery.Resource object at 0x7c474771ff50>), 
CalendarUpdateEvent(api_resource=<googleapiclient.discovery.Resource object at 0x7c474771ff50>), 
GetCalendarsInfo(api_resource=<googleapiclient.discovery.Resource object at 0x7c474771ff50>), 
CalendarMoveEvent(api_resource=<googleapiclient.discovery.Resource object at 0x7c474771ff50>), 
CalendarDeleteEvent(api_resource=<googleapiclient.discovery.Resource object at 0x7c474771ff50>), 
GetCurrentDatetime(api_resource=<googleapiclient.discovery.Resource object at 0x7c474771ff50>)]
'''
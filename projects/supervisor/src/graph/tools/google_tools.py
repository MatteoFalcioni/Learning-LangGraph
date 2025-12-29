from langchain_google_community import GmailToolkit, CalendarToolkit

gmail_toolkit = GmailToolkit()
calendar_toolkit = CalendarToolkit()

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
from langchain_google_community import GmailToolkit, CalendarToolkit

gmail_toolkit = GmailToolkit()
calendar_toolkit = CalendarToolkit()
google_tools = gmail_toolkit.get_tools() + calendar_toolkit.get_tools()

if __name__ == "__main__":
    print(google_tools)

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
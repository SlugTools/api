import requests

# POST to https://financial.ucsc.edu/Pages/Food_Trucks.aspx
# doesn't work, probably because of server-side auth
# TODO: workaround with timed request for waiting on full content
# or using selenium on a headless browser hosted through repl.it

endpoint_url = "https://financial.ucsc.edu/_vti_bin/lists.asmx"

list_name = "{F7A7608C-F360-41E2-BDB4-13E9A636C10F}"

view_name = ""

query = (
    f'<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
    f'xmlns:ns="http://schemas.microsoft.com/sharepoint/soap/">'
    f"<soapenv:Body>"
    f"<ns:GetListAndView>"
    f"<ns:listName>{list_name}</ns:listName>"
    f"<ns:viewName>{view_name}</ns:viewName>"
    f"</ns:GetListAndView>"
    f"</soapenv:Body>"
    f"</soapenv:Envelope>"
)

headers = {
    "Content-Type": "text/xml; charset=utf-8",
    "SOAPAction": "http://schemas.microsoft.com/sharepoint/soap/GetListAndView",
}

response = requests.post(endpoint_url, data=query, headers=headers)

print(response.text)  # 403 forbidden

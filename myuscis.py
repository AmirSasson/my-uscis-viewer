import os
import requests
from cases import cases
import webbrowser
from html import escape
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service

def get_uscis_session_cookie():
    options = EdgeOptions()
    # options.add_argument('--headless')  # Optional: Remove this line if you want to see the browser
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    profile_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default")
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--profile-directory=Default")
    service = Service(executable_path="msedgedriver.exe")
    driver = webdriver.Edge(options=options, service=service)

    try:
        driver.get("https://my.uscis.gov")

        print("🔑 Please log in manually if not automated.")
        input("⏳ Press Enter once you're logged in and the page has fully loaded...")

        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie['name'] == '_myuscis_session_rx':
                print("✅ Found session cookie.")
                return cookie['value']

        print("⚠ Cookie not found. Make sure you're fully logged in.")
        return None

    finally:
        driver.quit()

# Example usage
session_cookie = get_uscis_session_cookie()
print("Session cookie value:", session_cookie)
  

if not session_cookie:
# Get cookie value from user
  print("Please enter your _myuscis_session_rx cookie value from my.uscis.gov:")
  cookie_value = input("> ").strip()

else:
    cookie_value = session_cookie

results = []
cookies = {
      '_myuscis_session_rx': cookie_value
}

headers = {
    'User-Agent': 'Mozilla/5.0',  # Mimic a browser
    'Referer': 'https://my.uscis.gov/',
}

print("\nStarting USCIS case status check...\n")

for case in cases:
    print(f"\nProcessing case for {case['name']} - {case['form']} ({case['number']})")
    status_url = f"https://my.uscis.gov/account/case-service/api/case_status/{case['number']}"
    processing_url = f"https://my.uscis.gov/account/case-service/api/cases/{case['form']}/processing_times/{case['number']}"
    print(f"Status URL: {status_url}")
    print(f"Processing URL: {processing_url}")

    try:
        print("\nFetching case status...")
        status_res = requests.get(status_url, headers=headers, cookies=cookies)
        print(f"Status Response Code: {status_res.status_code}")
        status_data = status_res.json()

        form = status_data.get('data', 'Unknown')["formType"]
        title = status_data.get('data', 'Unknown')["statusTitle"]
        text = status_data.get('data', 'Unknown')["statusText"]
        action_date = status_data.get('data', 'Unknown')["currentActionCodeDate"]

        print("\nFetching processing times...")
        processing_res = requests.get(processing_url, headers=headers, cookies=cookies)
        print(f"Processing Response Code: {processing_res.status_code}")
        processing_data = processing_res.json()

        proc_time = processing_data.get('data', {}).get('time_until_case_decision', 'N/A')
        proc_time_next_milestone = processing_data.get('data', {}).get('time_until_next_milestone', 'N/A')
        proc_milestone_days_remaining = processing_data.get('data', {}).get('milestone_days_remaining', '')
        proc_text = processing_data.get('data', {}).get('display_text', '')

        print(f"\nSuccessfully retrieved data for case {case['number']}")
        print(f"Current Status: {title}")
        print(f"Action Date: {action_date[:10]}")
        print(f"Processing Time: {proc_time}")
        
        results.append({
            'name': case['name'],
            'case_number': case['number'],
            'form': form,
            'status': f"{title} ({action_date[:10]})",
            'Details': f"{text}",
            'processing_time': proc_time,
            'next_milestone': proc_time_next_milestone,
            'milestone_days_remaining': proc_milestone_days_remaining,
            'display_text': proc_text
        })

    except Exception as e:
        print(f"\nError processing case {case['number']}: {str(e)}")
        results.append({
            'name': case['name'],
            'case_number': case['number'],
            'form': case['form'],
            'status': f"Error: {escape(str(e))}",
            'Details': f"Error: {escape(str(e))}",
            'processing_time': 'N/A',
            'next_milestone': 'N/A',
            'milestone_days_remaining': f"Error: {escape(str(e))}",
            'display_text': ''
        })

# HTML generation
html = """
<html>
<head>
  <title>USCIS Case Summary</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
    th, td { border: 1px solid #ccc; padding: 10px; text-align: left; vertical-align: top; }
    th { background-color: #f4f4f4; }
    h2 { color: #333; margin-top: 30px; }
    .status-table th { background-color: #e6f3ff; }
    .processing-table th { background-color: #f0f7e6; }
  </style>
</head>
<body>
  <h1>USCIS Case Status Report</h1>
  
  <h2>Case Status Information</h2>
  <table class="status-table">
    <tr><th>Name</th><th>Case Number</th><th>Form</th><th>Current Status</th><th>Details</th></tr>
"""

# Add status information
for item in results:
    html += f"<tr><td>{escape(item['name'])}</td><td>{escape(item['case_number'])}</td>"
    html += f"<td>{escape(item['form'])}</td><td>{item['status']}</td><td>{item['Details']}</td></tr>"

html += """
  </table>

  <h2>Processing Time Information</h2>
  <table class="processing-table">
    <tr>
      <th>Name</th>
      <th>Case Number</th>
      <th>Form</th>
      <th>Time Until Decision</th>
      <th>Time Until Next Milestone</th>
      <th>milestone_days_remaining</th>
      <th>Additional Information</th>
    </tr>
"""

# Add processing time information
for item in results:
    html += f"""
    <tr>
      <td>{escape(item['name'])}</td>
      <td>{escape(item['case_number'])}</td>
      <td>{escape(item['form'])}</td>
      <td>{escape(item['processing_time'])}</td>
      <td>{escape(item['next_milestone'])}</td>
      <td>{escape(str(item['milestone_days_remaining']))}</td>
      <td>{escape(item['display_text'])}</td>
    </tr>"""

html += "</table></body></html>"

html_file = "uscis_cases.html"
print(f"\nGenerating HTML report: {html_file}")
with open(html_file, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML report generated successfully")

webbrowser.open_new_tab(html_file)

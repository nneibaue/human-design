#!/usr/bin/env python3
"""Test bodygraph endpoint and save HTML."""

import requests

response = requests.get(
    "http://localhost:8000/api/bodygraph",
    params={
        "date": "1992-08-13",
        "time": "09:13",
        "city": "Albuquerque",
        "country": "NM",
    }
)

if response.status_code == 200:
    data = response.json()

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Nate's Bodygraph - {data['type']}</title>
    <style>
        body {{
            font-family: Georgia, serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #8B4513;
        }}
        .info {{
            text-align: center;
            margin: 20px 0;
        }}
        svg {{
            display: block;
            margin: 0 auto;
            border: 1px solid #ccc;
            background: white;
            max-width: 600px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Nate's Bodygraph (via API Endpoint)</h1>
        <div class="info">
            <strong>Type:</strong> {data['type']} |
            <strong>Authority:</strong> {data['authority']} |
            <strong>Profile:</strong> {data['profile']}
        </div>
        <div class="info">
            <strong>Birth:</strong> August 13, 1992 at 9:13 AM<br>
            <strong>Location:</strong> Albuquerque, NM
        </div>
        <div class="info">
            <strong>Defined Centers:</strong> {', '.join(data['defined_centers'])}<br>
            <strong>Active Channels:</strong> {', '.join(f"{ch[0]}-{ch[1]}" for ch in data['active_channels'])}
        </div>
        {data['svg']}
    </div>
</body>
</html>"""

    with open("nate_bodygraph_api.html", "w") as f:
        f.write(html_content)

    print("✅ Saved to nate_bodygraph_api.html")
    print()
    print(f"Type: {data['type']}")
    print(f"Authority: {data['authority']}")
    print(f"Defined Centers: {data['defined_centers']}")
    print(f"Active Channels: {data['active_channels']}")
else:
    print(f"Error: {response.text}")

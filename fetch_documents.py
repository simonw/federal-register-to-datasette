import datetime
import urllib.parse
import urllib.request
import json
import os


def fetch_documents(date):
    base_url = "https://www.federalregister.gov/api/v1/documents.json"
    url = (
        base_url
        + "?"
        + urllib.parse.urlencode(
            {
                "conditions[publication_date][is]": date.strftime("%m/%d/%Y"),
                "per_page": 100,
            }
        )
    )
    while url:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            for result in data["results"]:
                yield result
            url = data.get("next_page_url")


def send_documents(documents, api_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(api_token),
    }
    body = {
        "table": "documents",
        "rows": documents,
        "pk": "document_number",
        "replace": True,
    }
    req = urllib.request.Request(
        "https://demos.datasette.cloud/data/-/create",
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        print(response.status, len(documents))


def save_documents_for_date(date, api_token):
    batch = []
    for document in fetch_documents(date):
        batch.append(
            dict(
                document,
                agencies=[
                    agency.get("name", agency["raw_name"])
                    for agency in document["agencies"]
                ],
            )
        )
        if len(batch) == 100:
            send_documents(batch, token)
            batch = []
    if batch:
        send_documents(batch, token)


if __name__ == "__main__":
    token = os.environ.get("DATASETTE_API_TOKEN")
    for date in (
        datetime.date.today(),
        datetime.date.today() - datetime.timedelta(days=1),
    ):
        save_documents_for_date(date, token)


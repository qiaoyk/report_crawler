import requests
import json
import re
import random
import os
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class EastmoneyReportScraper:
    """
    Scraper for fetching research reports from Eastmoney's data center.
    This class handles fetching the report list and downloading individual reports as PDFs.
    """
    API_URL = "https://reportapi.eastmoney.com/report/list"

    def __init__(self, industry_code: str):
        if not industry_code:
            raise ValueError("Industry code cannot be empty.")
        self.industry_code = industry_code
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh,zh-CN;q=0.9',
            'Connection': 'keep-alive',
            # Note: The cookie is crucial for authentication. If the script fails,
            # this cookie might have expired. A new one should be copied from the browser's
            # network request headers.
            'Cookie': 'qgqp_b_id=3fb73c6aa17f647e1a8978d1b940463b; fullscreengg=1; fullscreengg2=1; st_nvi=QiXIC-DtXdDGM5i6kxgR94840; websitepoptg_api_time=1759203802096; nid=03cb3969a2160584820f20508bc96432; nid_create_time=1759203802870; gvi=elxVl_gbziHXpHaXvIe7b47fd; gvi_create_time=1759203802870',
            'DNT': '1',
            'Referer': f'https://data.eastmoney.com/report/industry.jshtml?hyid={self.industry_code}',
            'Sec-Fetch-Dest': 'script',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }

    def get_reports(self, page_num: int = 1, page_size: int = 50) -> list | None:
        """
        Fetches a paginated list of reports.
        :param page_num: The page number to retrieve.
        :param page_size: The number of reports per page.
        :return: A list of report data dictionaries, or None if the request fails.
        """
        end_time = datetime.now()
        begin_time = end_time - timedelta(days=365 * 2)

        params = {
            'cb': f'datatable{random.randint(1000000, 9999999)}',
            'industryCode': self.industry_code,
            'pageSize': page_size,
            'industry': '*',
            'rating': '*',
            'ratingChange': '*',
            'beginTime': begin_time.strftime('%Y-%m-%d'),
            'endTime': end_time.strftime('%Y-%m-%d'),
            'pageNo': page_num,
            'fields': '',
            'qType': '1',
            'orgCode': '',
            'rcode': '',
            '_': int(datetime.now().timestamp() * 1000),
        }

        print(f"Fetching report list for page {page_num}...")
        try:
            response = requests.get(self.API_URL, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            jsonp_data = response.text
            match = re.search(r'\(({.*})\)', jsonp_data)
            if not match:
                print("Error: Could not find JSON data in the JSONP response.")
                print(f"Response content:\n{jsonp_data}")
                return None

            json_data = json.loads(match.group(1))
            # The API returns a list directly in the 'data' field.
            return json_data.get("data")

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the network request: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON from the response: {e}")
            return None

    def download_report_pdf(self, report: dict):
        """
        Downloads the full report as a PDF.
        :param report: A dictionary containing individual report information.
        """
        info_code = report.get("infoCode")
        if not info_code:
            print(f"Warning: Report '{report.get('title')}' is missing an infoCode and cannot be downloaded.")
            return

        report_url = f"https://data.eastmoney.com/report/zw_industry.jshtml?infocode={info_code}"
        print(f"Processing report: {report.get('title')}")

        try:
            # First, fetch the report detail page to find the PDF link
            page_response = requests.get(report_url, headers=self.headers, timeout=20)
            page_response.raise_for_status()
            soup = BeautifulSoup(page_response.text, 'lxml')
            
            # Use the specific selector to locate the PDF link
            selector = "div.c-infos span.to-link a.pdf-link"
            pdf_link_tag = soup.select_one(selector)

            if not pdf_link_tag or not pdf_link_tag.has_attr('href'):
                print(f"Could not find a PDF download link for '{report.get('title')}'. It may not have a PDF version.")
                return

            pdf_url = pdf_link_tag['href']
            print(f"Found PDF link: {pdf_url}")
            
            # Download the PDF with streaming and retries for robustness
            retries = 3
            for i in range(retries):
                try:
                    print(f"Attempting download ({i + 1}/{retries})...")
                    pdf_response = requests.get(pdf_url, headers=self.headers, timeout=60, stream=True)
                    pdf_response.raise_for_status()

                    output_dir = "reports_pdf"
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)

                    # Sanitize the title for use as a filename
                    title = report.get('title', f"Untitled_{info_code}")
                    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
                    date = report.get('publishDate', '').split('T')[0]
                    filename = f"{output_dir}/{date}_{safe_title}.pdf"

                    with open(filename, 'wb') as f:
                        for chunk in pdf_response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    print(f"Successfully downloaded and saved '{safe_title}' to: {filename}")
                    return # Exit after successful download

                except requests.exceptions.RequestException as e:
                    print(f"Download attempt {i + 1} failed: {e}")
                    if i < retries - 1:
                        print("Retrying in 5 seconds...")
                        time.sleep(5)
                    else:
                        print(f"Failed to download report '{safe_title}' after {retries} attempts. Giving up.")

        except requests.exceptions.RequestException as e:
            print(f"Failed to process report '{report.get('title')}': {e}")


def main():
    """
    Main execution function.
    """
    print("Starting the report scraping process...")
    
    # Industry ID from the provided URL: https://data.eastmoney.com/report/industry.jshtml?hyid=738
    industry_id = "738"
    scraper = EastmoneyReportScraper(industry_code=industry_id)
    
    # Fetch the first page of reports
    reports_data = scraper.get_reports(page_num=1)

    if reports_data and isinstance(reports_data, list):
        print(f"Found {len(reports_data)} reports on the current page.")
        print("Downloading the first 3 reports as a demonstration...\n")

        for report in reports_data[:3]: # Download first 3 for demonstration
            scraper.download_report_pdf(report)
            print("--------------------")
    else:
        print("No reports were found. Please check the configuration or website availability.")


if __name__ == "__main__":
    main()

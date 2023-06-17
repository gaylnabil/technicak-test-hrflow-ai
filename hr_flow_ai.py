from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from dotenv import dotenv_values
from hrflow import Hrflow
import re

from crawler import Crawler

PATH = 'C:\chromedriver_win32\chromedriver.exe'

# Get The last version of the chromedriver in this link:
# https://chromedriver.storage.googleapis.com/index.html


settings = {
    **dotenv_values(".env")
}

c = Crawler(settings)

driver = c.get_driver()

# job_0aa9dc37ec9aa503
print("*************************************")
driver.get("https://uk.indeed.com/jobs?l=All")


total_jobs = int(re.sub("\D", "", driver.find_element(
    By.CLASS_NAME, "jobsearch-JobCountAndSortPane-jobCount").text))

count_jobs = 15  # count jobs per Page
# total_pages = 66  # Maximum number of pages
total_pages = int(total_jobs // count_jobs + 1)
total_pages = 2  # number of pages for test

print("Total jobs: %d" % total_jobs)
print("count_jobs: %d" % count_jobs)
print("total_pages: %d" % total_pages)

for page in range(0, total_pages):

    print(f"******************** Page {page + 1} ************************")

    if page != 0:
        driver.get("https://uk.indeed.com/jobs?q=&l=All&start=%s" %
                   (page * count_jobs))

    tags_jobTitles = driver.find_elements(By.CLASS_NAME, "jcs-JobTitle")

    # Get ID and href attributes of <a /> tags
    links = [{"id": a.get_attribute("id"), "url": a.get_attribute(
        "href")} for a in tags_jobTitles]

    for a in links:
        print("=====================================================")
        reference = a["id"]
        url = a["url"]
        print("reference:", reference)
        print("url:", url)

        # Browse to specific job URL to get specific data on the page
        driver.get(url)

        # Get Job Name
        name = driver.find_element(
            By.CLASS_NAME, "jobsearch-JobInfoHeader-title-container").text

        print("name:", name)

        # Get all Tags Names (salary: 30K-40K, Job type: Fixed term contract, etc.)
        tags_job = []
        try:
            tag_list = driver.find_elements(
                By.CSS_SELECTOR, ".css-4m8ia3:not(.jobsearch-JobDescriptionSection-title)")

            if len(tag_list) > 0:
                tags_job = [
                    {"name": tag.find_element(By.CSS_SELECTOR, ".css-fhkva6").text, "value": ', '.join(
                        [v.text for v in tag.find_elements(By.CSS_SELECTOR, ".css-tvvxwd")])} for tag in tag_list]
        except NoSuchElementException:
            tag_list = None

        tags_job.append({"name": "company", "value": driver.find_element(
            By.XPATH, "//*[@data-company-name='true']").text})

        # Get Description
        description = driver.find_element(By.ID, 'jobDescriptionText').text

        # Initial JSON representation of the job
        json_job = c.format_job()

        json_job["agent_key"] = reference
        json_job["reference"] = reference
        json_job["name"] = name
        json_job["url"] = url
        json_job["sections"] = [
            {"name": "description", "title": "Description",
                "description": description}
        ],

        json_job["tags"] = tags_job

        # Verify that the job exists in the database
        is_exists = c.is_job_exists(reference)
        if not is_exists:
            # Save JSON job data into hrflow.ai database (API).
            code = c.save(json_job)
            print("code: ", code)
            print("verify_job:", is_exists)
        else:
            print("verify_job:", is_exists)
            # print("verify_job: ", list(verify_job.items())[:4])


# Check some jobs exists in hrflow.ai database (API).

print(" Check some jobs exists in hrflow.ai database: ")
references = [
    'job_0aa9dc37ec9aa503',
    'job_fd3244632c3893c0',
    'job_ee5cacc50ab8d624'
]

for ref in references:

    print("=====================")
    print(f'{ref} : ', c.get_job(ref))


print(f"\ndriver process is closing...")

c.close()
print(f"\n********************* finished ***********************")

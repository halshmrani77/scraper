import os
import re
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from config import driver_type, driver_path, username, password


def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # create webdriver based on config
    # TODO: Add cmdline arguments for these?
    if driver_type == "chrome":
        driver = webdriver.Chrome(driver_path)
    elif driver_type == "phantomjs":
        driver = webdriver.PhantomJS(driver_path)
    else:
        raise RuntimeError("Unknown driver type: %s" % driver_type)

    # log in to my.chevrolet.com
    driver.get("https://my.chevrolet.com/login")
    driver.find_element_by_id("Login_Username").send_keys(username)
    driver.find_element_by_id("Login_Password").send_keys(password)
    driver.find_element_by_id("Login_Button").click()

    # get status elements within certain time parameters/retries
    retries = 5
    timeout = 3*60  # seconds
    args = []
    for _ in range(retries):
        try:
            args = WebDriverWait(driver, timeout).until(find_status_elements)
        except TimeoutException:
            print "Timeout searching for elements -- refreshing..."
            driver.refresh()
        else:
            if len(args) == 3:
                print "Found status elements"
                break
            else:
                print "Error boxes found -- refreshing..."
                driver.refresh()

    # we should have 3 elements of information
    if len(args) != 3:
        print "Unable to get stats"
        cleanup(driver, script_dir)
        return 1

    # parse elements
    status_box, status_right, info_table = args
    stats = []

    # get current charge
    lines = status_box.text.splitlines()
    stats.append(lines[2])

    # get estimated electric and total range
    lines = status_right.text.splitlines()
    for s in ['Estimated Electric Range:',
              'Estimated Total Range:']:
        idx = lines.index(s) + 1
        match = re.search(r"[\d,]+", lines[idx]).group()
        stats.append(match.replace(',', ''))

    # get vehicle info table stats
    lines = info_table.text.splitlines()
    for s in ['Electric Miles',
              'Electric Economy',
              'Electricity Used',
              'Est Fuel Saved',
              'Est. CO2 Avoided']:
        idx = lines.index(s) + 1
        match = re.search(r"[\d,]+", lines[idx]).group()
        stats.append(match.replace(',', ''))

    # create stats string
    stats.insert(0, str(datetime.now()))
    stats = ','.join(stats)
    print stats

    # write stats to csv
    csv = os.path.join(script_dir, "stats.csv")
    open(csv, 'a').write(stats + '\n')

    # clean up and return
    cleanup(driver, script_dir)
    return 0


def cleanup(driver, script_dir):
    """function to properly close driver and remove log files"""
    driver.close()
    driver.quit()

    ghostdriverlog = os.path.join(script_dir, "ghostdriver.log")
    if os.path.isfile(ghostdriverlog):
        os.remove(ghostdriverlog)


def find_status_elements(driver):
    """function to check if status elements or error boxes have loaded"""
    try:
        status_box = driver.find_element_by_class_name("status-box")
        status_right = driver.find_element_by_class_name("status-right")
        info_table = driver.find_element_by_class_name("panel-vehicle-info-table")
        return status_box, status_right, info_table
    except NoSuchElementException:
        # return error elements if any
        error_selector = "[data-cms-content-id='vehicleProfile_EV_error1']"
        errors = driver.find_elements_by_css_selector(error_selector)
        return errors


###########################################################################

if __name__ == "__main__":
    main()

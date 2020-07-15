from ..scraper import Scraper
from ..course import Course
from bs4 import BeautifulSoup
import requests



class UCIScraper(Scraper):
    def __init__(self):
        Scraper.__init__(self, "UCI")

        # used to specify which term / tear
        self.yearTerm = "2020-92"

        # used for requests to WebSoc
        self.params = {"YearTerm": self.yearTerm, "ShowFinals": 1,
                        "ShowComments": 0}

        # list of department codes (str) for the queries
        self.deptCodes = list()

        # keeps track of the current name and title of the courses
        # Stored as HTML
        self.courseLabel = None


        # UCI's WebSoc requires that we identify ourselves (User-Agent)
        # The use of session will help for form submissions
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "User"})

        self.getDepartments()
        print("UCIScraper -- initialized")







    def getDepartments(self):
        page = self.session.get(self.url)
        soup = BeautifulSoup(page.content, "lxml")

        # find departments (in the form)
        departments = soup.find("select", {"name": "Dept"}).findChildren("option")
        for dept in departments:
            # print("UCIScraper -- getDepartments --", dept["value"])

            # getting ALL as a dept will lead to an error
            if (dept["value"].strip() != "ALL"):
                self.deptCodes.append(dept["value"])

        print("UCIScraper -- getDepartments --","Departments initialized")



    def getDepartmentCourses(self, dept: str) -> dict:
        '''
        Retrieves list of courses by querying department name
        '''

        # use params to "submit" the form data
        # (but for simplicity, we aren't using the form)
        params = {"Dept": dept}

        # add the base params
        params.update(self.params)
        page = self.session.get(self.url, params = params)
        courses = self.scrapePage(page)

        return courses



    def getCourseCodeCourses(self, courseCodes: str) -> dict:
        '''
        Retrieves list of courses by querying course codes
        i.e. 30000-35000 or 32140
        '''
        params = {"CourseCodes": courseCodes}

        # add the base params
        params.update(self.params)
        page = self.session.get(self.url, params = params)
        courses = self.scrapePage(page)

        return courses



    def scrapePage(self, page) -> dict:
        # Get course table
        courses = dict()
        soup = BeautifulSoup(page.content, "lxml")

        try:
            courseTable = soup.find("div", {"class": "course-list"}).findChildren("table")[0]
            rows = courseTable.findChildren("tr")


            # flag to identify a valid course row
            rowIsCourse = False

            # stores previous row so we can refer back to it
            prevRow = rows[0]
            for row in rows:
                courses.update(self.scrapeRow(row, prevRow))
                prevRow = row


        except IndexError:
            # index error means no course list was in the page
            # We want to print out the error message
            print("UCIScraper -- scrapePage --","ERROR:", soup.find("div", {"style":"color: red; font-weight: bold;"}).text.strip())
        return courses



    def scrapeRow(self, row, prevRow) -> list:
        courses = dict()
        cells = row.findChildren(["th", "td"])

        # make sure this is a valid row
        if (len(cells) > 10):
            if self.isCourse:

                course = self.scrapeCells(cells, self.courseLabel)
                courses[course.code] = course

            else:
                for cell in cells:
                    if (cell.text.strip().lower() == "code"):
                        # If this row has the word "Code",
                        # then the next row is a course
                        self.isCourse = True

                        self.courseLabel = prevRow.findChildren("td")[0]
                        print("UCIScraper -- scrapeRow --", "label found:", self.courseLabel.find(text=True, recursive = False))

        elif (len(cells) > 4):
            # if this row doesn't contain a course and has more than four cells
            # It usually contains data about the course from the previous row
            # But we'll ignore it for now
            pass

        elif (len(cells) < 2):
            # if this row is invalid (less than 2 cells), the next row is not a course
            self.isCourse = False

        return courses



    def scrapeCells(self, cells, courseLabel) -> Course:
        '''
        Scrapes the cells where Course information is located

        Course Label has both the course name and title
        '''
        course = Course()

        # remove extra spaces
        course.name = " ".join(courseLabel.find(text = True, recursive = False).strip().split())

        course.title = courseLabel.find("b").text
        course.code = cells[0].text
        course.type = cells[1].text
        course.units = self.toInt(cells[3].text)
        course.instructor = cells[4].text
        course.time = " ".join(cells[5].text.strip().split())
        course.location = cells[6].text.strip()
        course.final = cells[7].text.strip()
        course.max = self.toInt(cells[8].text)
        course.enrolled = self.toInt(cells[9].text)
        course.waitlisted = self.toInt(cells[10].text)
        course.requestedwaitlisted = self.toInt(cells[11].text)
        course.status = cells[-1].text


        print("UCIScraper -- scrapeCells --", "added course", course)

        return course



    def getCoursesByDepartment(self) -> list:
        courses = dict()
        for dept in self.deptCodes:
            print("UCIScraper -- getCoursesByDepartment --", "scraping", dept)

            courses.update(self.getDepartmentCourses(dept))

        return courses



    def getCoursesByCourseCodes(self) -> list:
        '''
        Gets courses by searching through ranges of codes

        i.e. 0-3000, then 3001-4000, ... etc.

        For efficiency, we query codes in predefined increments.
        WebSoc throws an error when a query has > 900 courses
        '''
        courses = dict()

        # define the course code range to search
        lowerBound = 0
        upperBound = 3000
        increment = upperBound - lowerBound
        max = 99999

        while (lowerBound < max):

            if (upperBound > max):
                # we need to be able to get course code 99999, but
                # anything above that course code will give an error
                upperBound = max

            courseCodes = f"{lowerBound}-{upperBound}"
            print("UCIScraper -- getCoursesByCourseCodes --", "scraping", courseCodes)

            courses.update(self.getCourseCodeCourses(courseCodes))

            lowerBound = upperBound + 1
            upperBound += increment


        return courses



    def scrape(self) -> list:
        '''
        Gets all UCI courses
        '''
        # self.getCoursesByDepartment()
        self.courses = self.getCoursesByCourseCodes()

        return self.courses



    def toInt(self, s: str) -> int:
        try:
            return int(s)
        except ValueError:
            return -1














def main():

    '''
    for course in scraper.courses:
        print(course)
    '''

if __name__ == '__main__':
    main()



'''
Alternative:
    import urllib.request as urllib

    request = urllib.Request("https://www.reg.uci.edu/perl/WebSoc/")
    request.add_header('User-Agent', 'poop')

    #open page
    open = urllib.urlopen(request)

    page = BeautifulSoup(open, "lxml")


'''
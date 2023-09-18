from Courses import *
import aiohttp

class TTBAPI:
    """
    Class which abstracts all interactions with the UofT TTB API.
    """
    def __init__(self) -> None:
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'DNT': '1',
            'Origin': 'https://ttb.utoronto.ca',
            'Prefer': 'safe',
            'Referer': 'https://ttb.utoronto.ca/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35',
            'sec-ch-ua': '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        self.json_data = {
            'courseCodeAndTitleProps': {
                'courseCode': '',
                'courseTitle': '',
                'courseSectionCode': '',
                'searchCourseDescription': False,
            },
            'departmentProps': [],
            'campuses': [],
            'sessions': [
                '20239',
                '20241',
                '20239-20241',
            ],
            'requirementProps': [],
            'instructor': '',
            'courseLevels': [],
            'deliveryModes': [],
            'dayPreferences': [],
            'timePreferences': [],
            'divisions': [
                'APSC',
                'ARTSC',
                'FPEH',
                'MUSIC',
                'ARCLA',
                'ERIN',
                'SCAR',
            ],
            'creditWeights': [],
            'page': 1,
            'pageSize': 162500,
            'direction': 'asc',
        }
        self.version = "TTBAPI V2.1"

    async def _make_request(self, course_code: str, semester: str) -> dict:
        """
        Makes a request to the TTB API to get info on a course.
        Precondition: Coursecode is a valid coursecode, and semester is a valid semester
        Which coursecode is offered in
        """
        self.json_data['courseCodeAndTitleProps']['courseCode'] = course_code
        self.json_data['courseCodeAndTitleProps']['courseSectionCode'] = semester
        # ===== OLD SYNCRENOUS APPROACH =======
        # response = requests.post(
        # 'https://api.easi.utoronto.ca/ttb/getPageableCourses', headers=self.headers, json=self.json_data)
        # x = response.json()
        # return x
        async with aiohttp.ClientSession() as session:
            async with session.post("https://api.easi.utoronto.ca/ttb/getPageableCourses", headers=self.headers, json=self.json_data) as response:
                # Check for successful status code (e.g., 200 OK)
                if response.status == 200:
                    data = await response.json()
                    return data

    async def get_course(self, course_code: str, semester: str) -> Course:
        """
        Returns a Course object from the TTB API
        Raises CourseNotFoundException if the course is deemed to be invalid
        """
        try:
            response = await self._make_request(course_code, semester)
            course = response['payload']['pageableCourse']['courses'][0]
            to_return = Course(course['name'], course['code'], course['sectionCode'])
            activities = course['sections']
            for activity in activities:
                to_return.add_activity(Activity(activity['name'], activity['type'], activity['currentEnrolment'], activity['maxEnrolment'], activity['openLimitInd'] != 'N', activity.get('currentWaitlist', 0)))
            return to_return
        except IndexError:
            raise CourseNotFoundException("Invalid course code or semester")

    async def get_courses_from_list(self, courses_wanted: dict[str, str] = None) -> dict[str, Course]:
        """
        Returns a list of all courses from the TTB API
        """
        all_courses = await self._make_request("", "") # by leaving the coursecode and semester blank, we get all courses
        courses_wanted = [f"{course['course_code']}{course['semester']}" for course in courses_wanted] if courses_wanted else []
        to_return = {}
        for course in all_courses['payload']['pageableCourse']['courses']:
            if f"{course['code']}{course['sectionCode']}" not in courses_wanted and courses_wanted:
                continue
            curr = Course(course['name'], course['code'], course['sectionCode'])
            activities = course['sections']
            for activity in activities:
                curr.add_activity(Activity(activity['name'], activity['type'], activity['currentEnrolment'], activity['maxEnrolment'], activity['openLimitInd'] != 'N', activity.get('currentWaitlist', 0)))
            to_return[f"{course['code']}{course['sectionCode']}"] = curr
        
        return to_return

    async def validate_course(self, coursecode: str, semester: str, activity: str):
        """
        Method which validates a coursecode/semester/activity combo
        """
        try:
            course = await self.get_course(coursecode, semester)
            activity = course.get_activity(activity)
        except CourseNotFoundException:
            raise CourseNotFoundException("Invalid course code or semester")
        except KeyError:
            raise InvalidActivityException("Invalid activity")

class CourseNotFoundException(Exception):
    """
    Exception which is raised when a course is not found in the TTB API
    """
    pass

class InvalidActivityException(Exception):
    """
    Exception which is raised when an activity is not found in the TTB API
    """
    pass

if __name__ == '__main__':
    api = TTBAPI()

    import asyncio
    import time
    from twilio.rest import Client  # Import the Twilio client
    # async def main():
    #     try:
    #         course = await api.get_course("CSC309H1", "F")
    #         # print("Course Name:", course.name)
    #         # print("Course Code:", course.course_code)
    #         # print("Course Semester:", course.semester)
            
    #         # print("Activities:", course.activities)
    #         # for activity in course.activities:
    #         #         print(activity, course.activities[activity], course.activities[activity].is_seats_free())
    #         lec_sec = 'LEC0201'
    #         while True:
    #             time.sleep(5)
    #             activity = course.activities[lec_sec]
    #             print(activity, course.activities[lec_sec], course.activities[lec_sec].is_seats_free())
            
    #     except CourseNotFoundException as e:
    #         print("Error:", e)
    async def main():
        try:
            # Your existing code to get the course information
            course = await api.get_course("CSC309H1", "F")
            lec_sec = 'LEC0201'

            # Twilio configuration
            account_sid =  ''
            auth_token = ''
            client = Client(account_sid, auth_token)
            to_phone_number = ''
            from_phone_number = ''

            while True:
                # Sleep for a while (e.g., 5 seconds)
                await asyncio.sleep(5)

                # Get the activity information for the lecture section
                activity = course.activities[lec_sec]
                
                # Print to console
                print(activity, course.activities[lec_sec], course.activities[lec_sec].is_seats_free())

                # Check if seats are free
                if activity.is_seats_free():
                    message = client.messages.create(
                        body=f"Seats are available for {lec_sec}! Enroll now!",
                        from_=from_phone_number,
                        to=to_phone_number
                    )
                    print("Text message sent:", message.sid)
                    await asyncio.sleep(35) # just sleep for 35 seconds, dont want multiple SMS's for same availability
                
                
        except CourseNotFoundException as e:
            print("Error:", e)

    asyncio.run(main())
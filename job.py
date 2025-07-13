import asyncio
import sqlite3
from gemini import prompt
from maps import get_distance

con = sqlite3.connect("job_ranker.sqlite3")
cur = con.cursor()
if cur.execute("SELECT name FROM sqlite_master").fetchone() is None:
    cur.execute('''CREATE TABLE location (
        id             INTEGER PRIMARY KEY AUTOINCREMENT
                               NOT NULL,
        name           TEXT    NOT NULL,
        distance_score INTEGER NOT NULL
    );''')
    cur.execute('''
    CREATE TABLE company (
        id      INTEGER PRIMARY KEY AUTOINCREMENT
                        NOT NULL,
        name    TEXT    NOT NULL,
        url     TEXT,
        summary TEXT,
    );''')
    cur.execute('''
    CREATE TABLE job (
        id          INTEGER PRIMARY KEY AUTOINCREMENT
                            NOT NULL,
        title       TEXT    NOT NULL,
        description TEXT    NOT NULL,
        site        TEXT,
        url         TEXT,
        rank        INTEGER NOT NULL,
        applied     BOOLEAN DEFAULT (0) 
                            NOT NULL,
        dismissed   BOOLEAN NOT NULL
                            DEFAULT (0),
        location    INTEGER REFERENCES location (id),
        company     INTEGER REFERENCES company (id) 
    );''')

db_write_lock = asyncio.Lock()


class Company:
    RECRUITERS = ["efinancialcareers", "hunter bond"]
    name = ""
    summary = ""
    url = ""
    id = None
    initialised = False

    def __init__(self, name):
        if name == "":
            self.name = ""
            self.summary = ""
            self.url = ""
        else:
            self.name = name

    async def create(self):
        if self.name == "" or self.name.lower() in Company.RECRUITERS:
            self.initialised = False
        else:
            existing_company = cur.execute("SELECT summary,url,id FROM company WHERE name = (?)",
                                           (self.name,)).fetchone()
            if existing_company:
                self.summary = existing_company[0]
                self.url = existing_company[1]
                self.id = existing_company[2]
            else:
                company_info = await prompt(self.name)
                company_info = company_info.split("|")
                self.summary = company_info[0]
                try:
                    self.url = company_info[1].replace(" ", "")
                except:
                    company_info = await prompt("COMPANY_NAME:\n" + self.name)
                    company_info = company_info.split("|")
                    try:
                        self.url = company_info[1].replace(" ", "")
                    except:
                        self.url = "err"
                async with db_write_lock:
                    new_id = cur.execute("INSERT INTO company (name,summary,url) VALUES (?,?,?) RETURNING id",
                                         (self.name, self.summary, self.url)).fetchone()
                    self.id = new_id[0]
                    con.commit()
            self.initialised = True

    def __eq__(self, other):
        return self.name == other.name


class Location:
    name = ""
    distance_score = None
    id = None
    initialised = False

    def __init__(self, name):
        if name == "":
            self.name = ""
            self.distance_score = 0
        else:
            self.name = name.lower()

    async def create(self):
        if self.name == "":
            self.initialised = False
            return
        existing_location = cur.execute("SELECT distance_score,id FROM location WHERE name = (?)",
                                        (self.name,)).fetchone()
        if existing_location:
            self.name = self.name
            self.distance_score = existing_location[0]
            self.id = existing_location[1]
        else:
            self.name = await prompt(self.name, prompt_type="location")
            self.name = self.name.lower()
            existing_location = cur.execute("SELECT distance_score,id FROM location WHERE name = (?)",
                                            (self.name,)).fetchone()
            if existing_location:
                self.distance_score = existing_location[0]
                self.id = existing_location[1]
            else:
                distance = get_distance(self.name)
                if distance > 3:
                    # Location is not in the uk, or nearby european countries.
                    self.distance_score = -50
                if distance > 2.5:
                    self.distance_score = 0
                else:
                    self.distance_score = round((2.5 - distance) * 40)
                async with db_write_lock:
                    new_id = cur.execute("INSERT INTO location (name,distance_score) VALUES (?,?) RETURNING id",
                                         (self.name, self.distance_score)).fetchone()
                    self.id = new_id[0]
                    con.commit()
        self.initialised = True

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        if not self.initialised:
            raise ValueError
        else:
            return hash(self.name)


class Job:
    term_blacklist = ["senior", "associate", "lead", "head of", "principal", "director", "mandarin", "phd", "vp ",
                      "manager", " vp", "mid level"]
    term_whitelist = ["software", "developer", "python", "java", "graduate program", "cyber security", "cybersecurity"]
    terms_dict = {
        20: ["graduate scheme", "robotics", "robot"],
        10: ["python", "java", "graduate", "entry level", "entry-level", " ros ", "django", "team", "teamwork",
             "remote", "sustainabl", "energy",
             "automotive", "transport", "gaming", "game", "trains",
             "cyber security", "cybersecurity", "mentor"],
        5: ["junior", "c++", "javascript", "2022", "cyber"],
        2: ["full stack", "2:1", "engineer", "penetration testing"],
        1: ["software", "developer", "haskell", "html", "css", "sql", "git", "version control", "linux", "windows",
            "nginx", "ghidra", "php", "matlab", "ida", "latex", " c ", "llm", "train", "progression"],
        -2: ["1 year of experience"],
        -5: ["finance"],
        -20: ["2026", "msc", "meng", "3 years of experience"],
        -40: ["gambling", "casino", "3+ years", "4+ years", "5+ years"]
    }

    title = ""
    company = None
    description = ""
    site = ""
    url = ""
    location = None
    rank = 0
    valid = None
    applied = False
    ignored = False

    def __init__(self, title, description, site, url, company, location):
        self.title = title
        self.description = description
        self.company = Company(company)
        self.location = Location(location)
        self.site = site
        self.url = url

    async def create(self):
        await self.company.create()
        await self.location.create()
        if self.is_valid():
            self.get_rank()

    def set_location(self, loc_string):
        pass

    def set_company(self, company_string):
        pass

    def get_rank(self):
        rank = 0
        for term_pair in self.terms_dict.items():
            score = term_pair[0]
            for term in term_pair[1]:
                if term in self.title.lower():
                    rank += 2 * score
                if term in self.description.lower():
                    rank += score

        if "graduate" not in self.description.lower() and "junior" not in self.description.lower() and "entry-level" not in self.description.lower() and "entry level" not in self.description.lower() and "graduate" not in self.title.lower() and self.site not in [
            "Gradcracker", "GRB"]:
            rank -= 30

        if "software engineer" not in self.description.lower() and "cyber" not in self.description.lower() and "develop" not in self.description.lower():
            rank -= 50

        rank += round(self.location.distance_score * 0.4)
        self.rank = rank
        return rank

    def is_valid(self):
        if not self.location.initialised or not self.company.initialised:
            return False
        if self.valid is None:
            valid = False

            for term in Job.term_whitelist:
                if term in self.description.lower():
                    valid = True
                    break
            for term in Job.term_blacklist:
                if term in self.title.lower():
                    valid = False
                    break

            if self.company is None:
                valid = False
            self.valid = valid
        return self.valid

    def __eq__(self, other):
        if self.title != other.title:
            return False
        elif self.company != other.company:
            return False
        elif self.url == other.url:
            return True
        else:
            return self.description == other.description

    def __gt__(self, other):
        return self.rank > other.rank

    def __ge__(self, other):
        return self.rank >= other.rank

    def __lt__(self, other):
        return self.rank < other.rank

    def __le__(self, other):
        return self.rank <= other.rank

    def __hash__(self):
        hashable_string = self.title + self.description
        return hash(hashable_string)

    @staticmethod
    def test_blacklist(phrase, company=None, full_description=None):
        phrase = phrase.lower()
        passes = True
        for term in Job.term_blacklist:
            if term in phrase:
                passes = False
                break
        if company is not None and company in Company.RECRUITERS:
            passes = False
        if full_description is not None:
            passes = False
            for term in Job.term_whitelist:
                if term in full_description.lower():
                    passes = True
                    break

        return passes


class JobManager:
    jobs = set()

    async def add(self, title, description, site="", url="", company="", location=""):
        job = Job(title, description, site, url, company, location)
        await job.create()
        if job.is_valid():
            async with db_write_lock:
                db_job = cur.execute("SELECT * FROM job WHERE (description) = (?)", (description,)).fetchone()
                if db_job is None:
                    cur.execute(
                        "INSERT INTO job (title,description,site,url,company,location,rank) VALUES (?,?,?,?,?,?,?)",
                        (job.title, job.description, job.site, job.url, job.company.id, job.location.id, job.rank))
                    con.commit()
                self.jobs.add(job)

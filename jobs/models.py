#https://pypi.org/project/duckduckgo-search/
#https://public-api.org/api/854/devitjobs-uk
#https://theirstack.com/en/docs/api-reference#tag/jobs/POST/v1/jobs/search
#https://www.peopledatalabs.com/job-posting-data
import math

from django.db import models

from JobRanker.llm_manager import prompt
import jobs.maps as maps

class Terms:
    blacklist = ["senior", "associate", "lead", "head of", "principal", "director", "vp "," vp", "mid level", "founding", "sr.", "chief" " ii", " iv","mid level","mid-level","founding","sr.","chief", "staff",] #These terms should not appear in the title
    super_blacklist = ["mandarin"," phd "," phd. "," fee "," fees "] #these terms should not appear in the description
    whitelist =  ["cyber security",
    "cybersecurity",
    "information security",
    "penetration testing",
    "penetration tester",
    "ethical hacking",
    "incident response",
    "digital forensics",
    "computer forensics",
    "security operations centre",
    "security operations center",
    "soc analyst",
    "security analyst",
    "security engineer",
    "security consultancy",
    "security consultant",
    "secure software development",
    "software security",
    "devsecops",
    "application security",
    "infrastructure security",
    "systems security",
    "security research",
    "exploit development",
    "threat intelligence",
    "threat hunting",
    "governance, risk and compliance",
                  " grc ",
    "security governance",
    "security compliance",
    "security audit",
    "security assurance",
    "information assurance",
    "security risk",
    "data protection",
    "privacy engineering",
    "cloud security",
    "vulnerability assessment",
    "vulnerability management",
    "network security",
    "identity and access management",
    "ai security",
    "machine learning security",
    "embedded systems security",
    "embedded security",
    "firmware security",
    "iot security",
    "automotive cybersecurity",
    "autonomous systems security",
    "railway signalling security",
    "operational technology security",
    "graduate program",
]
    ratings = {
        30:["industrial placement","placement year","year in industry",],
        20: ["graduate scheme", "robotics", "robot", "penetration testing",
        "penetration tester","pen testing","pen tester","ethical hacking"],
        15:["security analyst","security operations centre", "devsecops","secure software development","software security","secure coding","embedded systems security",
        "embedded security",
        "firmware security",
        "iot security",
        "automotive cybersecurity",
        "autonomous systems security",
        "robotics security",
        "railway signalling security",
        "operational technology security",],
        10: ["cyber", "sustainabl", "energy", "automotive", "transport", "gaming", "game", "trains", "cyber security","msc",
             "cybersecurity","remote", "application security",
        "appsec","security operations center",
        "soc analyst","digital forensics",
        "computer forensics",
        "forensic investigation","threat intelligence",
        "threat hunting",
        "security consultancy",
        "web application security","audit","grc","training",
        "mentor",
        "mentoring",
        "professional development",
        "career development",],
        5: ["junior", "javascript", "cyber","security risk analysis","python",
        "cyber risk",
        "risk management",
        "data protection",
        "data privacy",
        "privacy engineering",
        "security engineering",
        "security engineer",
        "cloud security",],
        3: ["c++", "java", "graduate", "entry level", "entry-level", " ros ", "django", "team", "teamwork"],
        2: ["full stack", "2:1", "engineer"],
        1: ["developer", "haskell", "html", "css", "sql", "git", "version control", "linux", "windows",
            "nginx", "ghidra", "php", "matlab", "ida", "latex", " c ", "llm", "train", "progression","aes","network",
            'learning', 'information', 'data',  'program', 'compliance', 'assessment', 'ethical', 'forensics', 'systems', 'application', 'privacy', 'cloud', 'assurance', 'technology', 'operations', 'development', 'computer', 'cybersecurity', 'hacking', 'soc', 'signalling', 'intelligence', 'consultancy', 'governance,', 'digital', 'research', 'threat', 'firmware', 'railway', 'exploit', 'protection', 'operational', 'ai', 'automotive', 'machine', 'analyst', 'secure', 'testing', 'management', 'autonomous', 'vulnerability', 'tester', 'consultant', 'infrastructure', 'risk', 'software', 'penetration', 'engineering', 'governance', 'iot', 'security', 'engineer', 'response', 'incident', 'access'],
        -2: ["1 year of experience"],
        -5: ["finance"],
        -20: ["meng", "3 years of experience", "sales"],
        -50: ["gambl", "casino", "3+ years", "4+ years", "5+ years",
        "betting",
        "sportsbook",
        "bookmaker",
        "bookmaking",]
    }
    countries ={"united kingdom":3,"england":3,"scotland":3,"northern ireland":3,"wales":3,"netherlands":2,"holland":2,"the netherlands":2,"ireland":2,"belgium":2,"france":1,"germany":1,"switzerland":1,"luxembourg":1,"czechia":1,"austria":1,"denmark":1,"sweden":1,"iceland":1,"finland":1,"bulgaria":1,"croatia":1,"cyprus":1,"estonia":1,"greece":1,"hungary":1,"italy":1,"latvia":1,"lithuania":1,"malta":1,"poland":1,"portugal":1,"romania":1,"slovakia":1,"slovenia":1,"spain":1,"canada":1,"australia":1,"new zealand":1}


class Company(models.Model):
    BLACKLIST = ["efinancialcareers", "hunter bond", "itol recruit", "itol", "targetjobs uk","it career switch"] # For recruiters / job boards or other such reposters
    name = models.CharField(max_length=255,blank=False,unique=True)
    summary = models.CharField(blank=False)
    url = models.URLField(blank=True)

    @staticmethod
    def fetch(name):
        name = name.lower()
        if name == "" or name.lower() in Company.BLACKLIST:
            return Company.objects.get(name="Broken Company :(")
        else:
            try:
                existing_company = Company.objects.get(name=name)
                return existing_company
            except:
                c = Company()
                c.name = name
                company_info = prompt(c.name)
                company_info = company_info.split("|")
                c.summary = company_info[0]
                try:
                    c.url = company_info[1].replace(" ", "")
                except:
                    company_info = prompt("COMPANY_NAME:\n" + c.name)
                    company_info = company_info.split("|")
                    try:
                        c.url = company_info[1].replace(" ", "")
                    except:
                        c.url = "err"
                c.save()
                return c

    def __eq__(self, other):
        if other is None:
            return False
        return self.name == other.name
    def __str__(self):
        return self.name

    def is_broken(self):
        return self.name == "Broken Company :("

def get_unknown_company(id=True):
    x, _ = Company.objects.get_or_create(name="Broken Company :(",summary="",url="crouton.net")
    if id:
        return x.id
    else:
        return x

class Location(models.Model):
    name = models.CharField(max_length=255,blank=False,unique=True)
    lat = models.FloatField(default=0, blank=False)
    lng = models.FloatField(default=0, blank=False)
    is_country = models.BooleanField(blank=False)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __eq__(self, other:object):
        if other is None:
            return False
        elif self.name == other:
            return True
        elif type(other) != Location:
            return False
        else:
            return self.name == other.name

    def __hash__(self):
        return hash(self.name)

def get_unknown_location(id=True):
    x, _ = Location.objects.get_or_create(name="Unknown Location",lat=0,lng=0,is_country=True)
    if id:
        return x.id
    else:
        return x

class PreciseLocation(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True)
    lat = models.FloatField(default=0,blank=False)
    lng = models.FloatField(default=0, blank=False)
    location = models.ForeignKey(Location, on_delete=models.SET_DEFAULT,default=get_unknown_location,blank=False)

    @staticmethod
    def fetch(name,latlng=None):
        if name == "":
            return PreciseLocation.objects.get(name="Unknown P.Location")
        name = name.lower()
        try:
            existing_location = PreciseLocation.objects.get(name=name)
            return existing_location
        except:
            precise = PreciseLocation()
            precise.name = name
            try:
                existing_location = Location.objects.get(name=name)
                precise.location = existing_location
            except:
                loc_return = prompt(name, prompt_type="location")
                location_name, country = loc_return.lower().split("|")
                is_country = bool(int(country.strip()))
                try:
                    existing_location = Location.objects.get(name=location_name)
                    precise.location = existing_location
                except:
                    new_location = Location()
                    new_location.name = location_name
                    new_location.is_country = is_country
                    new_location.lat,new_location.lng = maps.get_latlng(location_name)
                    if not is_country and new_location.lat == 0:
                        try:
                            llm_latlng_attempt = prompt(location_name, prompt_type="custom",arg_prompt="The following location (likely in the UK) was unable to be geolocated by maps API. Your job is to provide the coordinates of this location in the format lat|lng where lat and lng are floats. if the input is a large county or similar return the geocode for the centre of the county's largest city, in terms of countries, the capital. you MUST respond only with the two floats and pipe (|) NOTHING ELSE.")
                            lat,lng = llm_latlng_attempt.split("|")
                            new_location.lat = float(lat.strip())
                            new_location.lng = float(lng.strip())
                        except Exception as e:
                            print(e)
                    new_location.save()
                    precise.location = new_location
            if latlng != None:
                precise.lat,precise.lng = latlng
            precise.save()
            return precise

    def get_rank(self):
        # Returns an 8-bit value, 2:country,6:location
        glasgow_distance = 550
        resolution = 6
        max_value = (2 ** resolution) - 1
        if self.lat == 0:
            lat = self.location.lat
            lng = self.location.lng
        else:
            lat = self.lat
            lng = self.lng
        distance = maps.get_distance_km(lat, lng)
        if distance <= 7:
            rating = max_value
        elif self.location.name == "west london":
            rating = max_value - 1
        elif self.location.name == "central london":
            rating = max_value - 2
        elif self.location.name == "central london":
            rating = max_value - 3
        elif self.location.name == "north london":
            rating = max_value - 4
        elif self.location.name == "north london":
            rating = max_value - 5
        elif self.location.name == "south london":
            rating = max_value - 6
        elif self.location.name == "united kingdom":
            rating = 0
        else:
            rating = max((max_value-7)-((max_value-7)/glasgow_distance)*distance,0) #-26.5*(distance**(1/4))+128
        rating = min(max_value, round(rating))
        if self.location.is_country:
            if self.location.name in Terms.countries:
                country_rating = Terms.countries[self.location.name]
            else:
                country_rating = 0
        else:
            country_rating = 3
        return (country_rating << resolution) + rating


    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name + " | " + str(self.location)

    def __eq__(self, other:object):
        if isinstance(other, Location) or isinstance(other, str):
            return self.location == other
        elif isinstance(other, PreciseLocation):
            return self.location == other.location
        else:
            return False

    def __hash__(self):
        return hash(self.location)

def get_unknown_precise_location(id=True):
    x, _ = PreciseLocation.objects.get_or_create(name="Unknown P.Location",lat=0,lng=0)
    if id:
        return x.id
    else:
        return x

class Job(models.Model):
    RANK_DEFAULT = -1000
    STATUS_CHOICES = {"A":"Applied","I":"Manually Ignored","X":"Not Applicable","E":"Evaluated","N":"Not Scraped for Details"}

    title = models.CharField(max_length=255,blank=False)
    description = models.CharField(max_length=255,blank=False)
    description_html = models.CharField(max_length=255, blank=True)
    scrape_method = models.CharField(max_length=20,blank=False)
    url =  models.URLField(blank=False)
    rank = models.FloatField(default=RANK_DEFAULT,blank=False)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default="N",blank=False)
    placement = models.BooleanField(default=False,blank=False)
    salary = models.PositiveIntegerField(default=0,blank=False)
    deadline = models.DateField(blank=True)
    posted = models.DateField(blank=True)
    precise_location = models.CharField(max_length=255,blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_DEFAULT,default=get_unknown_company,blank=False)
    location = models.ForeignKey(PreciseLocation, on_delete=models.SET_DEFAULT,default=get_unknown_precise_location,blank=False)


    def set_placement(self):
        self.placement = "placement" in self.description + self.title or "year in industry" in self.description + self.title

    def get_word_rank(self):
        #5-bit output
        rank = 0
        t = self.title.lower()
        d = self.description.lower()
        for term_pair in Terms.ratings.items():
            score = term_pair[0]
            for term in term_pair[1]:
                if term in t:
                    rank += 2 * score
                if term in d:
                    rank += score

        if all([x not in d for x in ["graduate","junior","placement","year in industry","entry-level","entry level"]]):
            rank -= 30

        #Normalise Rank
        sigmoid_midpoint = 85
        sigmoid_steepness = 0.035
        rank = 31 / (1 + math.exp(-sigmoid_steepness * (rank - sigmoid_midpoint)))
        return max(0, min(31, round(rank)))

    def get_distance_rank(self):
        #8 bits
        return self.location.get_rank()

    def get_wage_rank(self):
        # 3 bits
        if self.salary == 0:
            adjusted_salary = 10000
        else:
            adjusted_salary = min(self.salary,65000) - 25000
        adjusted_salary = (adjusted_salary // 5000) - 1
        return adjusted_salary


    def get_rank(self):
        self.set_placement()
        # Running Tally: 0
        rank = self.get_wage_rank()
        # Running Tally: 3
        distance = self.get_distance_rank()
        country = distance >> 6
        if self.placement:
            if country != 3:
                distance = 0
        rank += distance << 3
        #Running Tally:11
        rank += self.get_word_rank() << 11
        #running tally: 16
        if self.placement:
            rank += 1 << 16
        return rank

    def __eq__(self, other):
        if self.url == other.url:
            return True
        if self.title != other.title:
            return False
        elif self.company != other.company:
            return False
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
    def __str__(self):
        return self.title + " | " + str(self.company) + " | " + self.description[:144] + "…"

    def quick_check(self):
        print(self.title)
        if not self.passes_blacklist():
            print("BLACKLIST")
            return False
        else:
            self.description = self.description[:-3]# This removes any ellipses at the end of the file.
            if Job.objects.filter(url=self.url).count() > 0:
                print("URL FOUND")
                return False
            elif Job.objects.filter(description__contains=self.description).count() > 0:
                print("DESCRIPTION FOUND")
                return False
            else:
                print("OK")
                return True


    def passes_blacklist(self,full_description=False):
        passes = True
        for term in Terms.blacklist:
            if term in self.title.lower():
                passes = False
                break
        for term in Terms.super_blacklist:
            if term in self.title.lower() or term in self.description.lower():
                passes = False
                break
        if full_description:
            passes = False
            for term in Terms.whitelist:
                if term in self.description.lower():
                    passes = True
                    break
        return passes


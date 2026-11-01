#https://pypi.org/project/duckduckgo-search/
#https://public-api.org/api/854/devitjobs-uk
#https://theirstack.com/en/docs/api-reference#tag/jobs/POST/v1/jobs/search
#https://www.peopledatalabs.com/job-posting-data

from django.db import models

from JobRanker.llm_manager import prompt
from jobs.maps import get_distance

class Terms:
    blacklist = ["senior", "associate", "lead", "head of", "principal", "director", "vp ",
                      "manager", " vp", "mid level", "founding", "sr.", "chief" " ii", " iv"] #These terms should not appear in the title
    super_blacklist = ["mandarin"," phd "," phd. "," fee "," fees "] #these terms should not appear in the description
    whitelist = ["software", "developer", "python", "java", "graduate program", "cyber security", "cybersecurity",
                      "application engineer"]
    ratings = {
        20: ["graduate scheme", "robotics", "robot"],
        10: ["python", "java", "graduate", "entry level", "entry-level", " ros ", "django", "team", "teamwork",
             "remote", "sustainabl", "energy", "automotive", "transport", "gaming", "game", "trains", "cyber security","msc",
             "cybersecurity", "mentor"],
        5: ["junior", "c++", "javascript", "2022", "cyber"],
        2: ["full stack", "2:1", "engineer", "penetration testing"],
        1: ["software", "developer", "haskell", "html", "css", "sql", "git", "version control", "linux", "windows",
            "nginx", "ghidra", "php", "matlab", "ida", "latex", " c ", "llm", "train", "progression"],
        -2: ["1 year of experience"],
        -5: ["finance"],
        -20: ["2026", "meng", "3 years of experience", "sales"],
        -40: ["gambl", "casino", "3+ years", "4+ years", "5+ years"]
    }


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
                    prompt("COMPANY_NAME:\n" + c.name)
                    company_info = company_info.split("|")
                    try:
                        c.url = company_info[1].replace(" ", "")
                    except:
                        c.url = "err"
                c.save()
                return c

    def __eq__(self, other):
        return self.name == other.name
    def __str__(self):
        return self.name

    def is_broken(self):
        return self.name == "Broken Company :("

class LocationMapping(models.Model):
    name = models.CharField(max_length=255, blank=False, unique=True)
    simple = models.CharField(max_length=255, blank=False)

    @staticmethod
    def fetch(name):
        try:
            existing_location = LocationMapping.objects.get(name=name)
            return existing_location.simple
        except:
            simple = prompt(name, prompt_type="location")
            simple = simple.lower()
            lm = LocationMapping()
            lm.name = name
            lm.simple = simple
            lm.save()
            return simple
    def __str__(self):
        return self.name + " -> " + self.simple

class Location(models.Model):
    name = models.CharField(max_length=255,blank=False,unique=True)
    distance_score = models.FloatField(default=-50,blank=False)

    @staticmethod
    def fetch(name):
        if name == "":
            return Location.objects.get(name="Unknown Location")
        name = name.lower()
        try:
            existing_location = Location.objects.get(name=name)
            return existing_location
        except:
            name = LocationMapping.fetch(name)
            try:
                existing_location = Location.objects.get(name=name)
                return existing_location
            except:
                distance = get_distance(name)
                if distance > 3:
                    # Location is not in the uk, or nearby european countries.
                    distance_score = -50
                elif distance > 2.5:
                    distance_score = 0
                else:
                    distance_score = round((2.5 - distance) * 40)
                new_location = Location()
                new_location.name = name
                new_location.distance_score = distance_score
                new_location.save()
                return new_location

    @staticmethod
    def remote():
        Location.objects.get_or_create(name="remote", distance_score=10)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

def get_broken_company():
    return Company.objects.get_or_create(name="Broken Company :(",summary="",url="crouton.net")

def get_unknown_location():
    return Location.objects.get_or_create(name="Unknown Location",distance_score=-10)

class Job(models.Model):
    RANK_DEFAULT = -1000
    STATUS_CHOICES = {"A":"Applied","I":"Manually Ignored","X":"Not Applicable","E":"Evaluated","N":"Not Scraped for Details"}

    title = models.CharField(max_length=255,blank=False)
    description = models.CharField(max_length=255,blank=False)
    scrape_method = models.CharField(max_length=20,blank=False)
    url =  models.URLField(blank=False)
    rank = models.FloatField(default=RANK_DEFAULT,blank=False)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default="N",blank=False)
    placement = models.BooleanField(default=False,blank=False)
    salary = models.PositiveIntegerField(default=0,blank=False)
    deadline = models.DateField(blank=True)
    posted = models.DateField(blank=True)
    precise_location = models.CharField(max_length=255,blank=True)
    company = models.ForeignKey(Company, on_delete=models.SET_DEFAULT,default=get_broken_company,blank=False)
    location = models.ForeignKey(Location, on_delete=models.SET_DEFAULT,default=get_unknown_location,blank=False)


    def set_placement(self):
        self.placement =  "placement" in self.description + self.title
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
            print("Location or company not initialised!!111!!")
            self.valid = False
            return False
        if self.valid is None:
            valid = False

            for term in Job.term_whitelist:
                if term in self.description.lower():
                    valid = True
                    break
            for term in Job.term_blacklist:
                if term in self.title.lower():
                    print("Blacklist.")
                    valid = False
                    break

            if self.company is None:
                print("No Company")
                valid = False
            self.valid = valid
            if not valid:
                print("No whitelisted terms")
        return self.valid

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


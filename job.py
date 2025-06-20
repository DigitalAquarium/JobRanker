class Job:
    term_blacklist = ["senior", "associate", "lead", "head of","principal","director"]
    term_whitelist = ["software", "developer", "python", "java", "graduate program", "cyber security"]
    terms_dict = {
        20: ["graduate scheme", "robotics", "robot"],
        10: ["python", "java", "graduate", "entry level", "entry-level", "ros", "django", "team", "teamwork",
             "automotive", "transport", "gaming", "game", "london", "reading", "bracknell", "slough", "maidenhead",
             "cyber security"],
        5: ["junior", "c++", "javascript", "2022", "cyber"],
        2: ["full stack", "2:1", "engineer"],
        1: ["software", "developer", "haskell", "html", "css", "sql", "git", "version control", "linux", "windows",
            "nginx", "ghidra", "php", "matlab", "ida", "latex", " c ", "llm"],
        -2: ["1 year of experience"],
        -5: ["finance"],
        -20: ["2026", "msc", "meng", "3 years of experience"],
        -30: ["gambling"]
    }

    title = ""
    company = ""
    description = ""
    site = ""
    url = ""
    rank = 0
    valid = None

    def __init__(self, title, description, company="", site="", url=""):
        self.title = title
        self.description = description
        self.company = company
        self.site = site
        self.url = url
        if self.is_valid():
            self.get_rank()

    def get_rank(self):
        rank = 0
        for term_pair in self.terms_dict.items():
            score = term_pair[0]
            for term in term_pair[1]:
                if term in self.title.lower():
                    rank += 2 * score
                if term in self.description.lower():
                    rank += score

        if "graduate" not in self.description.lower() and "junior" not in self.description.lower():
            rank -= 30

        if "software engineer" not in self.description.lower() and "cyber" not in self.description.lower() and "software developer" not in self.description.lower():
            rank -= 50

        self.rank = rank
        return rank

    def is_valid(self):
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
        hashable_string = self.title + self.company + self.description
        return hash(hashable_string)

    @staticmethod
    def test_blacklist(phrase):
        phrase = phrase.lower()
        passes = True
        for term in Job.term_blacklist:
            if term in phrase:
                passes = False
                break
        return passes
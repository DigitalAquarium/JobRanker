from flask import Flask, render_template, redirect
from html import escape
import sqlite3

app = Flask(__name__)


@app.route("/")
async def home():
    return "<h1><a href='/view/0'>View Jobs</a> | <a href='/scrape/'>Scrape Sites</a>"


@app.route("/view/<int:job_id>")
async def view(job_id):
    con = sqlite3.connect("../job_ranker.sqlite3")
    cur = con.cursor()
    '''jobs = cur.execute("SELECT job.id, job.title,job.description,job.site,job.url,company.name,company.summary,"
                       "company.url,location.name FROM ((job"
                       " INNER JOIN company ON job.company=company.id)"
                       " INNER JOIN location ON job.location=location.id)"
                       " WHERE applied <> 1 AND dismissed <> 1 ORDER BY rank DESC;").fetchall()
    for i in jobs:
        print(i)'''

    if job_id == 0:
        job = cur.execute("SELECT job.title,job.description,job.site,job.url,company.name,company.summary,"
                          "company.url,location.name, job.rank, job.id FROM ((job"
                          " INNER JOIN company ON job.company=company.id)"
                          " INNER JOIN location ON job.location=location.id)"
                          " WHERE applied <> 1 AND dismissed <> 1 ORDER BY rank DESC;").fetchone()
        job_id = job[9]
    else:
        job = cur.execute("SELECT job.title,job.description,job.site,job.url,company.name,company.summary,"
                          "company.url,location.name, job.rank FROM ((job"
                          " INNER JOIN company ON job.company=company.id)"
                          " INNER JOIN location ON job.location=location.id)"
                          " WHERE job.id = ?;", (job_id,)).fetchone()

    next = cur.execute("SELECT job.id FROM ((job"
                       " INNER JOIN company ON job.company=company.id)"
                       " INNER JOIN location ON job.location=location.id)"
                       " WHERE applied <> 1 AND dismissed <> 1 AND rank <= ? AND job.id <> ? ORDER BY rank DESC;",
                       (job[8], job_id)).fetchone()[0]
    con.close()
    return render_template("job.html", title=job[0], description=escape(job[1]).replace("\n", "<br>"), site=job[2],
                           url=job[3], company=job[4], company_summary=escape(job[5]).replace("\n", "<br>"),
                           company_url=job[6], location=job[7], next=next, id=job_id)


@app.route("/apply/<int:job_id>/<int:next>")
async def apply(job_id, next):
    con = sqlite3.connect("../job_ranker.sqlite3")
    cur = con.cursor()
    cur.execute("UPDATE job SET applied=1 WHERE id = ?", (job_id,))
    con.commit()
    con.close()
    return redirect(f"/view/{next}")


@app.route("/dissmiss/<int:job_id>/<int:next>")
async def dissmiss(job_id, next):
    con = sqlite3.connect("../job_ranker.sqlite3")
    cur = con.cursor()
    cur.execute("UPDATE job SET dismissed=1 WHERE id = ?", (job_id,))
    con.commit()
    con.close()
    return redirect(f"/view/{next}")


@app.route("/scrape")
async def scrape():
    return "<p>not complete yet.</p>"


app.run()

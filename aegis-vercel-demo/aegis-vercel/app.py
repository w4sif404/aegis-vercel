from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from pathlib import Path
from werkzeug.utils import secure_filename
import os
import uuid

from storage import get_state, set_state, reset_state, log_event

BASE = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE / "templates"),
    static_folder=str(BASE / "static"),
)
app.secret_key = os.environ.get("DEMO_SECRET", "LOCAL-DEMO-ONLY-change-me")

ALLOWED = {".html", ".txt"}
MAX_HEADLINE_LEN = 120


@app.context_processor
def globals():
    state = get_state()
    return {"compromised": state.get("compromised", False)}


@app.route("/")
def index():
    state = get_state()
    if state.get("compromised"):
        return render_template(
            "defaced.html",
            headline=state.get("headline") or "SYSTEM COMPROMISED",
        )
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/security")
def security():
    return render_template("security.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/blog")
def blog():
    return render_template("blog.html")


@app.route("/status")
def status():
    return render_template("status.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    state = get_state()

    if request.method == "POST":
        f = request.files.get("file")
        headline = (request.form.get("headline") or "").strip()[:MAX_HEADLINE_LEN]

        if not f or not f.filename:
            flash("No file selected.")
            return redirect(url_for("admin"))

        # INTENTIONALLY VULNERABLE DEMO:
        # This endpoint accepts an HTML/TXT file as "proof" and flips a flag
        # that makes the homepage render the defacement template. It never
        # executes, serves, or reflects the uploaded file's contents — so the
        # "vulnerability" being taught is the MISSING AUTHENTICATION /
        # AUTHORIZATION on a content-deployment endpoint, which is realistic
        # and common, without this demo app actually being exploitable for
        # stored XSS, RCE, or anything that reaches outside this one flag.
        name = secure_filename(f.filename)
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED:
            flash("Demo uploader accepts only .html or .txt files.")
            log_event(f"blocked upload filename={name}")
            return redirect(url_for("admin"))

        log_event(f"accepted demo upload filename={name}")
        set_state(
            compromised=True,
            headline=headline,
            uploaded_name=f"{uuid.uuid4().hex}_{name}",
        )
        log_event("DEMO STATE: homepage switched to COMPROMISED")
        flash("Demo upload accepted. Homepage is now in COMPROMISED mode.")
        return redirect(url_for("admin"))

    return render_template("admin.html", state=state)


@app.route("/demo/reset", methods=["GET", "POST"])
def reset_demo():
    reset_state()
    log_event("DEMO STATE: restored original homepage")
    return redirect(url_for("index"))


@app.route("/demo/status")
def demo_status():
    state = get_state()
    return jsonify({
        "mode": "COMPROMISED" if state.get("compromised") else "ORIGINAL",
        "purpose": "Authorized local/university cybersecurity demonstration",
    })


@app.route("/robots.txt")
def robots():
    return (
        "User-agent: *\nDisallow: /admin\nDisallow: /demo/\nSitemap: /sitemap.xml\n",
        200,
        {"Content-Type": "text/plain"},
    )


@app.route("/sitemap.xml")
def sitemap():
    return (
        """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>/</loc></url>
<url><loc>/about</loc></url>
<url><loc>/services</loc></url>
<url><loc>/security</loc></url>
<url><loc>/status</loc></url>
</urlset>""",
        200,
        {"Content-Type": "application/xml"},
    )


@app.route("/.well-known/security.txt")
def security_txt():
    return (
        "Contact: mailto:security@aegis.local\n"
        "Expires: 2027-12-31T23:59:59Z\n"
        "Preferred-Languages: en\n",
        200,
        {"Content-Type": "text/plain"},
    )


@app.route("/api/docs")
def api_docs():
    return render_template("api_docs.html")


@app.route("/api/company")
def api_company():
    return jsonify({
        "company": "Aegis Cyber Systems",
        "version": "2.4.1-demo",
        "environment": "vercel-training",
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

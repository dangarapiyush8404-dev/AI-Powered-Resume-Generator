from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

try:
    from backend.models import db, User, StudentProfile
except ModuleNotFoundError:
    from models import db, User, StudentProfile

import io
import os
import re
import base64
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from urllib.request import urlopen

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    Image = None
    ImageDraw = None
    ImageOps = None

static_path = os.path.join(os.path.dirname(__file__), "..", "front end")
app = Flask(__name__, static_folder=static_path, static_url_path="/static")
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Create DB
with app.app_context():
    db.create_all()

# --- AI-driven role prediction and ATS optimization helpers ---
ROLE_MARKET_SKILLS = {
    "Data Scientist": [
        "Python",
        "Machine Learning",
        "Statistics",
        "SQL",
        "Data Analysis",
        "Pandas",
        "Scikit-learn",
        "TensorFlow",
        "Data Visualization",
        "Modeling",
    ],
    "Software Engineer": [
        "Python",
        "Java",
        "C++",
        "Algorithms",
        "Data Structures",
        "API Development",
        "Git",
        "Docker",
        "Unit Testing",
        "System Design",
    ],
    "Product Manager": [
        "Roadmapping",
        "Stakeholder Management",
        "User Research",
        "Agile",
        "Prioritization",
        "Go-to-market",
        "Analytics",
        "Communication",
        "Requirements Gathering",
        "Strategy",
    ],
    "UX Designer": [
        "User Research",
        "Wireframing",
        "Prototyping",
        "UI Design",
        "Figma",
        "Design Systems",
        "User Testing",
        "Interaction Design",
        "Accessibility",
        "Visual Design",
    ],
    "Digital Marketing Specialist": [
        "SEO",
        "Content Marketing",
        "Google Analytics",
        "Campaign Management",
        "Social Media",
        "Email Marketing",
        "PPC",
        "Brand Strategy",
        "Conversion Optimization",
        "Market Research",
    ],
}


def normalize_skill_token(text):
    if not text:
        return ""
    cleaned = re.sub(r"[^a-z0-9\+\-#\. ]+", "", text.lower())
    return cleaned.strip()


def extract_skill_set(skill_text):
    if not skill_text:
        return set()

    parts = re.split(r"[\n,;/|]+", skill_text)
    normalized = {
        normalize_skill_token(part)
        for part in parts
        if normalize_skill_token(part)
    }
    return {skill for skill in normalized if len(skill) > 1}


ROLE_SKILL_SETS = {
    role: {normalize_skill_token(skill) for skill in skills}
    for role, skills in ROLE_MARKET_SKILLS.items()
}

ROLE_FALLBACK_KEYWORDS = {
    "Data Scientist": [
        "data",
        "machine learning",
        "statistics",
        "analytics",
        "pandas",
        "numpy",
        "tensorflow",
        "ml",
        "ai",
        "modeling",
    ],
    "Software Engineer": [
        "python",
        "java",
        "c++",
        "api",
        "docker",
        "git",
        "testing",
        "backend",
        "frontend",
        "development",
    ],
    "Product Manager": [
        "product",
        "roadmap",
        "agile",
        "stakeholder",
        "strategy",
        "research",
        "prioritization",
        "launch",
        "requirement",
        "analytics",
    ],
    "UX Designer": [
        "ux",
        "ui",
        "wireframe",
        "prototype",
        "figma",
        "design",
        "usability",
        "user research",
        "accessibility",
        "testing",
    ],
    "Digital Marketing Specialist": [
        "seo",
        "content",
        "social media",
        "analytics",
        "campaign",
        "email",
        "ppc",
        "branding",
        "market research",
        "conversion",
    ],
}


def fallback_predict_roles(skills_text):
    normalized_text = normalize_skill_token(skills_text)
    predictions = []
    for role, keywords in ROLE_FALLBACK_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in normalized_text)
        score = matches / len(keywords) if keywords else 0
        predictions.append({
            "role": role,
            "score": round(score, 2),
            "confidence": round(score * 100, 1),
            "matched_skills": sorted([kw for kw in keywords if kw in normalized_text]),
            "matched_count": matches,
            "required_count": len(keywords),
            "required_skills": sorted(ROLE_MARKET_SKILLS.get(role, [])),
            "missing_skills": sorted(
                [skill for skill in ROLE_MARKET_SKILLS.get(role, []) if normalize_skill_token(skill) not in extract_skill_set(skills_text)]
            ),
        })
    predictions.sort(key=lambda item: (item["score"], item["matched_count"]), reverse=True)
    return [prediction for prediction in predictions if prediction["score"] > 0]


def predict_job_roles(skills_text):
    user_skills = extract_skill_set(skills_text)
    predictions = []
    for role, required_skills in ROLE_SKILL_SETS.items():
        matched = sorted(user_skills & required_skills)
        score = len(matched) / len(required_skills) if required_skills else 0
        predictions.append({
            "role": role,
            "score": round(score, 2),
            "confidence": round(score * 100, 1),
            "matched_skills": matched,
            "matched_count": len(matched),
            "required_count": len(required_skills),
            "required_skills": sorted(ROLE_MARKET_SKILLS[role]),
            "missing_skills": sorted(
                [skill for skill in ROLE_MARKET_SKILLS[role] if normalize_skill_token(skill) not in user_skills]
            ),
        })

    predictions.sort(key=lambda item: (item["score"], item["matched_count"]), reverse=True)
    filtered = [prediction for prediction in predictions if prediction["score"] > 0 or prediction["matched_count"] > 0]
    if filtered:
        return filtered
    fallback = fallback_predict_roles(skills_text)
    return fallback or predictions


def build_gap_analysis(skills_text, top_roles=None):
    if top_roles is None:
        top_roles = predict_job_roles(skills_text)

    gaps = []
    user_skills = extract_skill_set(skills_text)
    for role_insight in top_roles[:3]:
        missing_count = len(role_insight["missing_skills"])
        total = role_insight["required_count"]
        gap_ratio = missing_count / total if total else 0
        if gap_ratio <= 0.33:
            gap_level = "Low"
        elif gap_ratio <= 0.66:
            gap_level = "Medium"
        else:
            gap_level = "High"

        gaps.append({
            "role": role_insight["role"],
            "missing_skills": role_insight["missing_skills"],
            "matched_skills": role_insight["matched_skills"],
            "gap_level": gap_level,
            "gap_ratio": round(gap_ratio, 2),
        })
    return gaps


def build_role_optimized_resume(data, role_insight):
    data = dict(data)
    data["profession"] = f"{role_insight['role']} | ATS Optimized"

    current_skills = extract_skill_set(data.get("skills", ""))
    target_skills = {normalize_skill_token(s) for s in role_insight["required_skills"]}
    merged_skills = sorted(current_skills | target_skills)
    data["skills"] = "\n".join(merged_skills)

    summary = data.get("summary", "").strip()
    if summary:
        prefix = (
            f"Resume optimized for {role_insight['role']} roles with proven strength in "
            f"{', '.join(role_insight['matched_skills'] or role_insight['required_skills'][:3])}. "
        )
        if prefix.strip().lower() not in summary.lower():
            data["summary"] = prefix + summary
    else:
        data["summary"] = (
            f"Resume optimized for {role_insight['role']} roles with core skills in "
            f"{', '.join(role_insight['required_skills'][:4])}."
        )

    if data.get("experience"):
        data["experience"] = enhance_experience_text(data["experience"], role_insight)

    if data.get("projects"):
        data["projects"] = enhance_project_text(data["projects"], role_insight)

    data["optimization_notes"] = build_optimization_notes(role_insight)
    return data


def enhance_experience_text(text, role_insight):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return text

    bullets = []
    keywords = role_insight["matched_skills"] or role_insight["required_skills"][:3]
    for line in lines:
        cleaned = line.lstrip("-• ")
        bullets.append(f"• {cleaned}")

    bullets.append(
        f"• Strengthened experience with {', '.join(keywords)} to improve role-fit and ATS matching."
    )
    bullets.append(
        "• Delivered measurable results by aligning projects with key industry keywords and technical requirements."
    )
    return "\n".join(bullets)


def enhance_project_text(text, role_insight):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return text

    keywords = role_insight["matched_skills"] or role_insight["required_skills"][:3]
    bullets = []
    for line in lines:
        cleaned = line.lstrip("-• ")
        bullets.append(f"• {cleaned}")

    bullets.append(
        f"• Highlighted project impact with {', '.join(keywords)} and ATS-friendly achievement language."
    )
    return "\n".join(bullets)


def build_optimization_notes(role_insight):
    if not role_insight:
        return []
    recommended = role_insight["missing_skills"][:4]
    return [
        f"Add keywords: {', '.join(recommended)}.",
        "Use strong action verbs in experience statements.",
        "Keep bullet points concise, measurable, and role-specific.",
        "Include both technical skills and domain keywords from job descriptions.",
    ]


@app.route("/")
def home():
    return {"message": "Backend Running Successfully!", "status": 200}

@app.route("/app")
def frontend_app():
    return app.send_static_file("index.html")

@app.route("/api/health")
def health():
    return {"message": "Backend Running!"}

@app.route("/api/save-profile", methods=["POST"])
def save_profile():
    data = request.json

    profile = StudentProfile(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        address=data.get("address", ""),
        summary=data.get("summary", ""),
        skills=data.get("skills", ""),
        language=data.get("language", ""),
        projects=data.get("projects", ""),
        education=data.get("education", ""),
        experience=data.get("experience", ""),
        photo_url=data.get("photo_url", "")
    )

    db.session.add(profile)
    db.session.commit()

    return jsonify({"message": "Profile saved!", "id": profile.id})


# ⭐ Resume Generation Route
def build_resume_buffer(data):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(595, 842))  # A4 points

    theme = data.get("theme", "rose")
    theme_colors = {
        "blue": (0.15, 0.3, 0.68),
        "teal": (0.03, 0.55, 0.44),
        "rose": (0.75, 0.33, 0.56),
    }
    accent = theme_colors.get(theme, theme_colors["rose"])
    accent_light = tuple(min(1.0, c + 0.25) for c in accent)

    # Left panel + right panel
    p.setFillColorRGB(*accent)
    p.rect(0, 0, 200, 842, fill=True, stroke=False)
    p.setFillColorRGB(1, 1, 1)
    p.rect(200, 0, 395, 842, fill=True, stroke=False)

    # Page border
    p.setStrokeColorRGB(0.15, 0.3, 0.68)
    p.setLineWidth(4)
    p.rect(8, 8, 595 - 16, 842 - 16, fill=False, stroke=True)

    # Top name/photo block on right side
    p.setFillColorRGB(*accent_light)
    p.setStrokeColorRGB(*accent)
    p.setLineWidth(2)
    p.roundRect(210, 720, 360, 96, 10, fill=True, stroke=True)

    # Circular photo placeholder overlapping the left edge of the name block
    p.setFillColorRGB(1, 1, 1)
    p.setStrokeColorRGB(0.85, 0.85, 0.85)
    p.setLineWidth(1)
    p.circle(96, 765, 60, fill=True, stroke=True)

    photo_drawn = False
    photo_url = data.get("photo_url")
    if photo_url:
        try:
            image_bytes = None
            if photo_url.startswith("http"):
                image_bytes = urlopen(photo_url, timeout=10).read()
            elif photo_url.startswith("data:image/"):
                m = re.match(r"^data:image/(png|jpeg|jpg);base64,(.+)$", photo_url, re.IGNORECASE)
                if m:
                    image_bytes = base64.b64decode(m.group(2))
            else:
                with open(photo_url, "rb") as f:
                    image_bytes = f.read()

            if image_bytes:
                if Image is not None and ImageOps is not None and ImageDraw is not None:
                    try:
                        img = Image.open(io.BytesIO(image_bytes))
                        img = ImageOps.fit(img, (120, 120), Image.LANCZOS, centering=(0.5, 0.5))
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")

                        mask = Image.new("L", (120, 120), 0)
                        draw = ImageDraw.Draw(mask)
                        draw.ellipse((0, 0, 119, 119), fill=255)
                        img.putalpha(mask)

                        bg = Image.new("RGBA", (120, 120), (255, 255, 255, 0))
                        bg.paste(img, (0, 0), img)
                        image_reader = ImageReader(bg)
                    except Exception:
                        logging.exception("PIL processing failed")
                        image_reader = ImageReader(io.BytesIO(image_bytes))
                else:
                    image_reader = ImageReader(io.BytesIO(image_bytes))

                # Place photo into top block placeholder
                p.drawImage(image_reader, 36, 705, width=120, height=120, preserveAspectRatio=False, mask="auto")
                p.setStrokeColorRGB(0.85, 0.85, 0.85)
                p.setLineWidth(1)
                p.circle(96, 765, 60, fill=False, stroke=True)
                photo_drawn = True
        except Exception:
            logging.exception("Failed to draw photo in PDF")

    if not photo_drawn:
        name = data.get("name", "")
        initials = ""
        if name:
            parts = [w.strip() for w in name.split() if w.strip()]
            if len(parts) >= 2:
                initials = (parts[0][0] + parts[1][0]).upper()
            elif len(parts) == 1:
                initials = parts[0][0].upper()

        if initials:
            p.setFont("Helvetica-Bold", 28)
            p.setFillColorRGB(0.15, 0.3, 0.68)
            p.drawCentredString(205, 784, initials)

    # Name and title inside top block
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(390, 780, data.get("name", "Your Name"))
    p.setFont("Helvetica", 11)
    p.drawCentredString(390, 760, data.get("profession", "Aspiring Professional"))

    # Contact (left panel, under photo)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(20, 620, "Contact")
    p.setFont("Helvetica", 10)
    p.drawString(20, 604, f"✉  {data.get('email', '')}")
    p.drawString(20, 590, f"☎  {data.get('phone', '')}")
    p.drawString(20, 576, f"📍  {data.get('address', '')}")

    def wrap_left_text(text, max_width, font_name="Helvetica", font_size=9):
        words = text.split(" ")
        line = ""
        for w in words:
            candidate = (line + " " + w).strip()
            if p.stringWidth(candidate, font_name, font_size) > max_width:
                if line:
                    yield line
                line = w
            else:
                line = candidate
        if line:
            yield line

    # Left sections (Education + Skills) below name/contact
    def wrap_left_text(text, max_width, font_name="Helvetica", font_size=9):
        words = text.split(" ")
        line = ""
        for w in words:
            candidate = (line + " " + w).strip()
            if p.stringWidth(candidate, font_name, font_size) > max_width:
                if line:
                    yield line
                line = w
            else:
                line = candidate
        if line:
            yield line

    def draw_left_section(title, lines, y_start):
        p.setFillColorRGB(1, 1, 1)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(20, y_start, title)
        p.setLineWidth(1)
        p.line(20, y_start - 2, 170, y_start - 2)

        p.setFont("Helvetica", 9)
        y = y_start - 18
        for line in lines:
            text_line = line.strip()
            if not text_line:
                continue

            wrapped_lines = list(wrap_left_text(text_line, 140, "Helvetica", 9))
            for idx, wrapped_line in enumerate(wrapped_lines):
                if y < 60:
                    break
                if idx == 0:
                    p.drawString(24, y, f"• {wrapped_line}")
                else:
                    p.drawString(30, y, wrapped_line)
                y -= 12
            if y < 60:
                break
        return y - 10

    y_left = 520  # start sufficiently below contact section
    # Split by actual input lines so each user-entered line becomes one bullet
    y_left = draw_left_section("Education", data.get("education", "").splitlines(), y_left)
    y_left = draw_left_section("Skills", data.get("skills", "").splitlines(), y_left)
    y_left = draw_left_section("Language", data.get("language", "").splitlines(), y_left)

    # Right content sections
    right_x = 220
    y = 700  # start right column below top banner and profile block

    def wrap_text(text, max_width, font_name="Helvetica", font_size=11):
        words = text.split(" ")
        line = ""
        for w in words:
            candidate = (line + " " + w).strip()
            if p.stringWidth(candidate, font_name, font_size) > max_width:
                yield line
                line = w
            else:
                line = candidate
        if line:
            yield line

    for section_title, section_text in [
        ("About Me", data.get("summary", "")),
        ("Projects", data.get("projects", "")),
        ("Experience", data.get("experience", "")),
    ]:
        p.setFillColorRGB(*accent_light)
        p.rect(right_x - 8, y - 12, 368, 18, fill=True, stroke=False)
        p.setFillColorRGB(*accent)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(right_x, y - 10, section_title)

        y -= 25
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica", 11)

        for para in section_text.split("\n"):
            for line in wrap_text(para, 360):
                p.drawString(right_x, y, line)
                y -= 14
            y -= 8

        y -= 10
        if y < 120:
            p.showPage()
            y = 780

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


@app.route("/api/generate-resume", methods=["POST"])
def generate_resume():
    data = request.json or {}
    predicted = predict_job_roles(data.get("skills", ""))
    gaps = build_gap_analysis(data.get("skills", ""), predicted)

    if data.get("return_insights") or data.get("response_type") == "json":
        best = predicted[0] if predicted else None
        optimized_preview = None
        if best:
            optimized_preview = build_role_optimized_resume(data, best)

        return jsonify({
            "predicted_roles": predicted,
            "gap_analysis": gaps,
            "recommended_role": best["role"] if best else None,
            "recommended_keywords": best["matched_skills"] if best else [],
            "missing_keywords": best["missing_skills"] if best else [],
            "optimized_preview": optimized_preview,
        })

    if data.get("auto_optimize") or data.get("enable_ai"):
        if predicted:
            data = build_role_optimized_resume(data, predicted[0])

    buffer = build_resume_buffer(data)
    return send_file(buffer, as_attachment=True, download_name="resume.pdf", mimetype="application/pdf")


@app.route("/api/predict-roles", methods=["POST"])
def predict_roles():
    data = request.json or {}
    roles = predict_job_roles(data.get("skills", ""))
    return jsonify({"predicted_roles": roles})


@app.route("/api/skill-gap", methods=["POST"])
def skill_gap():
    data = request.json or {}
    roles = predict_job_roles(data.get("skills", ""))
    gaps = build_gap_analysis(data.get("skills", ""), roles)
    return jsonify({"gap_analysis": gaps})


@app.route("/api/analyze-profile", methods=["POST"])
def analyze_profile():
    data = request.json or {}
    skills = data.get("skills", "")
    roles = predict_job_roles(skills)
    gaps = build_gap_analysis(skills, roles)
    best = roles[0] if roles else None
    optimized = build_role_optimized_resume(data, best) if best else data
    return jsonify({
        "predicted_roles": roles,
        "gap_analysis": gaps,
        "recommended_role": best["role"] if best else None,
        "recommended_confidence": best["confidence"] if best else None,
        "recommended_keywords": best["matched_skills"] if best else [],
        "missing_keywords": best["missing_skills"] if best else [],
        "optimization_notes": optimized.get("optimization_notes", []),
        "optimized_preview": {
            "summary": optimized.get("summary"),
            "skills": optimized.get("skills"),
            "experience": optimized.get("experience"),
            "projects": optimized.get("projects"),
        },
    })


@app.route("/api/student/profile/<int:profile_id>/insights", methods=["GET"])
def get_profile_insights(profile_id):
    profile = StudentProfile.query.get(profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    skills = profile.skills or ""
    roles = predict_job_roles(skills)
    gaps = build_gap_analysis(skills, roles)
    return jsonify({
        "profile_id": profile.id,
        "name": profile.name,
        "predicted_roles": roles,
        "gap_analysis": gaps,
    })


@app.route("/api/student/profiles", methods=["GET"])
def list_profiles():
    profiles = StudentProfile.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "email": p.email,
        "phone": p.phone,
        "address": p.address,
        "summary": p.summary,
        "skills": p.skills,
        "projects": p.projects,
        "education": p.education,
        "experience": p.experience,
        "language": p.language,
        "photo_url": p.photo_url,
    } for p in profiles])


@app.route("/api/student/profile/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    profile = StudentProfile.query.get(profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify({
        "id": profile.id,
        "name": profile.name,
        "email": profile.email,
        "phone": profile.phone,
        "address": profile.address,
        "summary": profile.summary,
        "skills": profile.skills,
        "language": profile.language,
        "projects": profile.projects,
        "education": profile.education,
        "experience": profile.experience,
        "photo_url": profile.photo_url,
    })


@app.route("/api/student/profile/<int:profile_id>/generate-optimized-resume", methods=["GET"])
def generate_optimized_resume_from_profile(profile_id):
    profile = StudentProfile.query.get(profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    data = {
        "name": profile.name,
        "email": profile.email,
        "phone": profile.phone,
        "address": profile.address,
        "summary": profile.summary,
        "skills": profile.skills,
        "language": profile.language,
        "projects": profile.projects,
        "education": profile.education,
        "experience": profile.experience,
        "photo_url": profile.photo_url,
    }

    predicted = predict_job_roles(profile.skills or "")
    if predicted:
        data = build_role_optimized_resume(data, predicted[0])

    buffer = build_resume_buffer(data)
    filename = f"resume_optimized_{profile.id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@app.route("/api/student/profile/<int:profile_id>/generate-resume", methods=["GET"])
def generate_resume_from_profile(profile_id):
    profile = StudentProfile.query.get(profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    data = {
        "name": profile.name,
        "email": profile.email,
        "phone": profile.phone,
        "address": profile.address,
        "summary": profile.summary,
        "skills": profile.skills,
        "language": profile.language,
        "projects": profile.projects,
        "education": profile.education,
        "experience": profile.experience,
        "photo_url": profile.photo_url,
    }

    buffer = build_resume_buffer(data)
    filename = f"resume_{profile.id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
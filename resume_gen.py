import os

def generate_resume(data):
    folder = "resumes"
    os.makedirs(folder, exist_ok=True)

    file_path = f"{folder}/resume_{data['name'].replace(' ', '_')}.txt"

    with open(file_path, "w") as f:
        f.write("=== AUTO GENERATED RESUME ===\n\n")
        f.write(f"Name: {data['name']}\n")
        f.write(f"Email: {data['email']}\n")
        f.write(f"Phone: {data.get('phone')}\n")
        f.write(f"Degree: {data.get('degree')}\n")
        f.write(f"Branch: {data.get('branch')}\n")
        f.write(f"CGPA: {data.get('cgpa')}\n\n")
        f.write(f"Skills: {data.get('skills')}\n\n")
        f.write(f"Predicted Domain: {data.get('domain')}\n")

    return file_path
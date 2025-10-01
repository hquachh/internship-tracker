"""
Generate Synthetic Emails:
    - build diverse synthetic submitted emails
    - 40+ body templates for realistic variation
    - randomize companies, roles, greetings, closings, ids, dates
    - insert into sqlite database with synthetic flag
"""

import uuid
import random
import datetime
from src.config.db_utils import insert_email

# company and role pools
companies = [
    "Google", "Tesla", "Lockheed Martin", "Meta", "Amazon", "OpenAI",
    "Northrop Grumman", "Nvidia", "Palantir", "Microsoft", "Raytheon",
    "IBM", "Boeing", "SpaceX", "Goldman Sachs", "Citadel", "Deloitte",
    "Airbnb", "Stripe", "Anthropic", "General Electric", "Airbus",
    "Bloomberg", "Apple", "Uber", "Lyft", "Intel", "AMD"
]

roles = [
    "Software Engineer Intern", "Machine Learning Intern",
    "Data Science Intern", "Quantitative Analyst Intern",
    "AI Research Intern", "Cybersecurity Intern",
    "Cloud Engineering Intern", "Product Management Intern",
    "Systems Engineering Intern", "Computer Vision Intern",
    "Robotics Intern", "Embedded Systems Intern", "Research Intern"
]

# variable slots
greetings = ["Dear Candidate,", "Hello Harrison,", "Hi Applicant,", "Dear Applicant,", ""]
closings = [
    "Regards, Talent Acquisition", "Sincerely, Recruiting Team",
    "Best, HR Department", "This is an automated message, do not reply", ""
]
followups = [
    "Our recruiting team will review your application in the coming weeks.",
    "We will only contact shortlisted applicants.",
    "Please expect to hear back within 2–3 weeks.",
    "Due to high volume, response times may vary.",
    "Thank you for your patience during the process."
]

# expanded body templates (40+)
templates = [
    # short
    "{greet} Thank you for applying to {company}. Your application for {role} has been received. {follow} {close}",
    "{greet} Application confirmed: {company} – {role}. {close}",
    "{greet} We have logged your application for {role} at {company}. {follow} {close}",
    "{greet} Your submission for the {role} position at {company} is confirmed. {close}",
    "{greet} This is to notify you that your {company} – {role} application is in our system. {close}",
    "{greet} Confirmation: We’ve received your application to {company}. {close}",
    "{greet} The {company} recruitment system shows your {role} application was submitted. {close}",
    "{greet} Thank you for submitting your interest in {role} at {company}. {close}",
    # medium
    "{greet} This email confirms receipt of your application for {role} at {company}. {follow} {close}",
    "{greet} Your application to {company} for the {role} internship has been successfully submitted. {follow} {close}",
    "{greet} We acknowledge receipt of your application to {company}. It is now being reviewed by our hiring team. {close}",
    "{greet} Your profile has been successfully added to the candidate pool for {role} at {company}. {close}",
    "{greet} Dear applicant, this message confirms your submission to {company} for {role}. No further action is required at this time. {close}",
    "{greet} We have successfully received your application for {role} at {company}. This is an automated acknowledgment. {close}",
    "{greet} Thank you for your interest in {company}. Your application for {role} is complete and ready for review. {close}",
    "{greet} This is an automated message from {company}: your application for {role} was received on our system. {close}",
    # long
    "{greet} Thank you for applying to {company} for the {role} position. This email serves as official confirmation that your application has been submitted successfully. {follow} {close}",
    "{greet} We are pleased to confirm receipt of your application for {role} at {company}. Your submission has been logged into our recruiting database. {follow} {close}",
    "{greet} Dear Applicant, we appreciate your interest in {company}. Your application for {role} has been successfully received. {follow} {close}",
    "{greet} This message confirms that your application for {role} at {company} is now complete in our career system. {close}",
    "{greet} Dear Harrison, thank you for submitting your application to {company}. We are writing to let you know your materials for the {role} internship were received. {close}",
    "{greet} Thank you for your interest in joining {company}. Your application for {role} has been submitted successfully. {follow} {close}",
    "{greet} We confirm that your application to {company} for {role} has been entered into our recruitment pipeline. {follow} {close}",
    "{greet} Your application for {role} at {company} has been submitted. We appreciate your patience as our hiring process progresses. {close}",
    # html
    "<p>{greet} We have received your application for <b>{role}</b> at <b>{company}</b>. Thank you for applying.</p><p>{follow}</p><p>{close}</p>",
    "<div style='font-size:14px'>{greet} Application confirmed: {company} – {role}. {close}</div>",
    "<p>Dear Candidate,<br>Your submission to {company} for {role} was successful.<br>{follow}<br>{close}</p>",
    "<html><body><p>This is to confirm that your application for <em>{role}</em> at {company} has been logged into our career portal.</p><p>{close}</p></body></html>",
    "<span>Confirmation: {company} has received your application for {role}. Our system shows your status as submitted.</span>",
    "<p>Your application for {role} – {company} has been recorded.<br>Thank you for considering us.</p>",
    # extra-info
    "Your application ID #{rand_id} for {role} at {company} has been received. {close}",
    "Submission timestamp: {today_date}. Candidate: Harrison Quach. Application: {company} – {role}. Status: Submitted. {close}",
    "This is an acknowledgment of your application for {role} at {company}. Tracking number: #{rand_id}. {close}",
    "Our records show that your application for {role} at {company} was successfully submitted on {today_date}. {close}",
    "Your submission to {company} for {role} has been assigned to our recruiting workflow. Confirmation ID: {rand_id}. {close}",
    "System Notification: Application received. Employer: {company}. Position: {role}. Date: {today_date}. {close}",
    "We have logged your application to {company} for {role}. Confirmation code: #{rand_id}. {close}",
    "This message verifies that your resume has been submitted to {company} for {role}. Submission reference: {rand_id}. {close}",
    "Dear Applicant, this is a receipt for your application to {company} for {role}. Submission time: {today_date}. ID: {rand_id}. {close}",
    "Thank you for applying to {company}. Your application for {role} has been stored with confirmation code {rand_id}. {close}"
]

def generate_email():
    company = random.choice(companies)
    role = random.choice(roles)
    greet = random.choice(greetings)
    close = random.choice(closings)
    follow = random.choice(followups)
    rand_id = str(random.randint(100000, 999999))
    today_date = datetime.date.today().strftime("%B %d, %Y")
    template = random.choice(templates)

    body = template.format(
        company=company, role=role,
        greet=greet, close=close, follow=follow,
        rand_id=rand_id, today_date=today_date
    ).strip()

    subject_options = [
        f"Application Confirmation – {company} {role}",
        f"Your application to {company} for {role}",
        f"{company} – {role} application received",
        f"Submission confirmed: {company} {role}"
    ]
    subject = random.choice(subject_options)
    sender = f"careers@{company.lower().replace(' ', '')}.com"

    return {
        "id": f"synthetic_{uuid.uuid4().hex}",
        "subject": subject,
        "sender": sender,
        "body": body,
        "is_starred": True,
        "label": "Submitted",
        "synthetic": 1
    }

def main(n=600):
    for _ in range(n):
        email = generate_email()
        insert_email(email)
    print(f"Inserted {n} synthetic emails.")

if __name__ == "__main__":
    main()

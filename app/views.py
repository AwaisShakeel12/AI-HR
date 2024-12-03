from django.shortcuts import redirect, render
from django.core.mail import send_mail,  get_connection
from django.conf import settings
from project.settings import get_email_settings
import easyimap as e
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import LLMChain

from .llm_model import get_gemini_response, create_resume_fun
from .prompts import score_prompt, full_review
import os 

import pdf2image
import io
import base64

import google.generativeai as genai
from fpdf import FPDF

import google.generativeai as genai
import os
from django.contrib.auth import login, logout, authenticate
from django.contrib import auth
from django.contrib import messages


from .models import *


genai.configure(api_key='')
model = genai.GenerativeModel('gemini-1.5-flash')
poppler_path = r'C:\Users\Awais Shakeel\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin'
poppler_path = r'D:\Release-24.08.0-0\poppler-24.08.0\Library\bin'

# Global variables to store extracted data
attachments = None
response = None




def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        re_enter_password = request.POST['password1']
        email = request.POST['email']
        app_password = request.POST['app_password']



        if password == re_enter_password:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'username already exsist')
                return redirect('register')
            if User.objects.filter(email=email).exists():
                messages.info(request, 'email already exsist')
                return redirect('register')
            else:
                
                user = User.objects.create_user(username=username, email=email, password=password,  app_password=app_password)
                user.save()

                user_login = auth.authenticate(username=username,password=password)
                auth.login(request, user_login)
                return redirect('home')
              
        else:

            messages.info(request, 'invalid data')
            return redirect('register')
    return render(request, 'register2.html')




def login(request):

    if request.user.is_authenticated:
        return redirect('home')
   
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'username or password inccorect')

    return render(request, 'login.html')



def logout(request):
    auth.logout(request)
    return redirect('login')




        
        
        
        

def hiring_page(request):

    cleaned_text = ''
    if request.method == 'POST':
        company = request.POST['company']
        job_title = request.POST['job_title']
        experience = request.POST['experience']
        education = request.POST['education']
        job_type = request.POST['job_type']
        salary = request.POST['salary']
        skills = request.POST['skills']
        prefer_skill = request.POST['prefer_skill']
        benifits = request.POST['benifits']

        
        job_dec = f"""
        You are an experienced HR. Your task is to create an effective Porfessional job description for a given position at a company. 
        Please use the details provided below and ensure the job description is professional, clear, and formatted appropriately.
        
        Job Title: {job_title} at out comapnay at   Company: {company} for a  Job Type: {job_type}.
        we require a candidate with the experience of Experience: {experience}.
        requirements : 
        
        Education : {education}
        Required Skills: {skills}
        Preferred Skills: {prefer_skill}
        
        salary:
        Salary: {salary}
        benefits:
        Benefits: {benifits}
        
        create a effective professioanl job description.
        dont create from yourself , only use available data.
        """
        
    
        
        
        description_prompt = ChatPromptTemplate.from_template(job_dec)
        llm = ChatGroq(model='llama-3.1-70b-versatile', groq_api_key='')
        chain = LLMChain(llm=llm, prompt=description_prompt)
        
        response = chain.invoke({"input": 'create a job deceription'})  # Pass the input as expected by the template
        # print("Raw Response:", response),
        text = response.get('text', '') # Extract the 'text' field from the response
        cleaned_text = text.replace("{", "").replace("}", "").strip()  # Remove brackets and extra spaces
        cleaned_text = cleaned_text.replace("**", "")  # Remove any bold markdown formatting
        cleaned_text = cleaned_text.replace(". ", ".\n")  # Ad
        cleaned_text
        
        descriptions = JobDescription.objects.create(description=cleaned_text)
        descriptions.save()
        
        return redirect('job_create')
        
        
        
    return render(request, 'home2.html', {'cleaned_text':cleaned_text})


def job_create(request):
   
    latest_job = JobDescription.objects.all().order_by('-id').first()
    if not latest_job:
        return render(request, 'job_create2.html', {'error': 'No job descriptions found in the database.'})
    
    job_description = latest_job.description
    
    if request.method == 'POST':
        date = request.POST['date']
        time = request.POST['time']
        hiring = request.POST['hiring'] == 'on'
        
        
        interview_date = InterviewDate.objects.create(date=date, time=time)
        interview_date.save()
        
        if hiring:
            return redirect('myemails')
    
    return render(request, 'job_create2.html', {'job_description':job_description})





last_processed_email_id = None  # Global variable to track the last processed email ID
def myemails(request):
    job_description = JobDescription.objects.all().order_by('-id').first()
    interview_date = InterviewDate.objects.all().order_by('-id').first()
    if not job_description:
        return render(request, 'job_create2.html', {'error': 'No job descriptions found in the database.'})
    
    dates = interview_date.date
    times = interview_date.time
    
    job_description = job_description.description
    global attachments, response, last_processed_email_id

    user = request.user.email
    password = request.user.app_password

    mylist = []  # List to hold email data
    attachments = []  # Reset global attachments

    # Connect to email server
    server = e.connect("imap.gmail.com", user, password)
    email_ids = server.listids()

    # Fetch the latest email ID
    latest_email_id = email_ids[0] if email_ids else None

    # Check if the latest email is already processed
    if latest_email_id == last_processed_email_id:
        # Render the email list without processing
       
        context = {'mylist': mylist}
        return render(request, 'myemails2.html', context)

    # Update the last processed email ID
    last_processed_email_id = latest_email_id

    for email_id in email_ids[:1]:  # Fetch the latest email
        email = server.mail(email_id)

        # Extract attachments
        if email.attachments:
            for attachment in email.attachments:
                if len(attachment) >= 2:  # Ensure valid attachment structure
                    filename = attachment[0]
                    content = attachment[1]
                    attachments.append({
                        'filename': filename,
                        'content': content,
                    })

        # Extract sender's email
        if '<' in email.from_addr and '>' in email.from_addr:
            sender_email = email.from_addr.split('<')[1].split('>')[0]  # Extract the part between '<' and '>'
        else:
            sender_email = email.from_addr

        mylist.append({
            'from_addr': sender_email,
            'title': email.title,
            'date': email.date,
            'body': email.body,
            'attachments': attachments,
        })

        # Use LLM to analyze the email
        Email_Check = """
        You are an HR professional. Your task is to analyze the provided email content and respond with one of the following words based on the email {body}:

        1. If the email is from a **job seeker** looking for opportunities, respond with only one word **'Yes'**.
        2. If the email is **not from a job seeker**, respond with only one word **'No'  only 'No' **.
        3. If the email is from a **job seeker replying about availability** and they are available, respond  with only one word  **'Available'**.
        4. If the email is from a **job seeker replying about availability** and they are not available, respond with only one word  **'Unavailable'**.

        ### Rules for output:
        - Respond with **only one word**: 'Yes', 'No', 'Available', or 'Unavailable'.
        - Ensure the response strictly follows the first condition that matches the email type.
          NO markdown backticks
        - NO explanations or comments
        - Maintain proper indentation
        - Do not include any surrounding text or formatting

        Analyze the email carefully to determine its type and respond accordingly.

        """
       

        prompt = ChatPromptTemplate.from_template(Email_Check)
        llm = ChatGroq(model='llama-3.1-70b-versatile', groq_api_key='')
        chain = LLMChain(llm=llm, prompt=prompt)

        response = chain.run({"subject": email.title, "body": email.body})
        print(response)
        if response == 'Yes' and attachments:
            print('yes --- condition on goo...')
            job_description
            attachment = attachments[0]  # Process the first attachment
            pdf_content = input_pdf_setup(attachment['content'])
            score = int(get_gemini_response(job_description, pdf_content, score_prompt))
            review = get_gemini_response(job_description, pdf_content, full_review).strip().lower()

            if score > 60 and review == 'satisfy':
                print('send email')
                send_mail(
                    subject="Interview Invitation",
                    message=f"Thank you for applying to our position. We are pleased to invite you for an interview scheduled on {dates} at {times}. Kindly let us know if this date and time work for you, and we look forward to your response.",
                    from_email=user,
                    recipient_list=[sender_email],
                    fail_silently=False
                )
                return render(request,'ats2.html', {'mylist':mylist, 'response':response,'score':score,'review':review })    
                
                
            else:
                print('sorry')
                send_mail(
                    subject="Application Update",
                    message='Thank you for taking the time to apply for the position. After careful consideration, we regret to inform you that we are unable to move forward with your application at this time. We appreciate your interest and wish you success in your future endeavors.',
                    from_email=user,
                    recipient_list=[sender_email],
                    fail_silently=False
                )
                
            return render(request,'ats2.html', {'mylist':mylist, 'response':response,'score':score,'review':review })    
        
        if response == 'No':
            print('No Skipping')
        
        if response == 'Available':
            print('available --- condition on goo...')
            send_mail(
                subject="Interview Scheduled",
                message=f"Thank you for confirming your interest in the position. We are pleased to inform you that your interview has been scheduled for today, {dates}, at {times}. Please ensure you are prepared and available at the designated time. We look forward to speaking with you!",
                from_email=user,
                recipient_list=[sender_email],
                fail_silently=False
            )
            interview = Interview.objects.create(email=sender_email, time=times, date=dates)
            interview.save()
            return redirect('send')
        if response == 'Unavailable':
            print( 'not availble')   

    # Render the email list
    context = {'mylist': mylist}
    return render(request, 'myemails2.html', context)




def input_pdf_setup(upload_file):
    if upload_file:
        # Convert PDF to image
        images = pdf2image.convert_from_bytes(upload_file, poppler_path=poppler_path)
        first_page = images[0]
        
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()

        pdf_parts = [
            {
                'mime_type': 'image/jpeg',
                'data': base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError('No file uploaded')


def ats(request):
    return render(request, 'ats2.html')      

def send(request):
    # interviews = Interview.objects.all().order_by('-id').first()
    latest_interview = Interview.objects.all().order_by('-id').first()  # Fetch the latest interview

    if latest_interview:
        print(latest_interview.email)
    else:
        print("No interviews found.")
    return render(request, 'send2.html', {'latest_interview':latest_interview})
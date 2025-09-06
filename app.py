import streamlit as st
import io
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoUploader

# --- App Configuration ---
st.set_page_config(
    page_title="SOLID NORTH | Medical Review",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Data ---
ALL_SUBJECTS = [
    'Anatomy', 'Biochemistry and Molecular Biology', 'Physiology', 'Clinical Epidemiology and Basic Research', 'Family and Community Medicine I',
    'Microbiology, Parasitology and Immunology', 'Pathology', 'Pharmacology, Anesthesia, and Pain Management', 'Psychiatry', 'Surgery I', 'Pediatrics I', 'Internal Medicine I', 'Family and Community Medicine II',
    'Surgery II', 'Pediatrics II', 'Internal Medicine II', 'Obstetrics and Gynecology', 'Family and Community Medicine III', 'Neurology', 'Otolaryngology', 'Radiology', 'Ophthalmology', 'Legal Medicine, Medical Jurisprudence, and Forensic Science',
    'Clinical Clerkship in Surgery', 'Clinical Clerkship in Pediatrics', 'Clinical Clerkship in Internal Medicine', 'Clinical Clerkship in Obstetrics and Gynecology', 'Clinical Clerkship in Family and Community Medicine', 'Clinical Clerkship in Psychiatry', 'Clinical Clerkship in Neurology', 'Clinical Clerkship in Ophthalmology', 'Clinical Clerkship in Otolaryngology', 'Clinical Clerkship in Anesthesia', 'Clinical Clerkship in Laboratory', 'Clinical Clerkship in Radiology'
]

SUBJECTS_BY_YEAR = {
    'First Year': ['Anatomy', 'Biochemistry and Molecular Biology', 'Physiology', 'Clinical Epidemiology and Basic Research', 'Family and Community Medicine I'],
    'Second Year': ['Microbiology, Parasitology and Immunology', 'Pathology', 'Pharmacology, Anesthesia, and Pain Management', 'Psychiatry', 'Surgery I', 'Pediatrics I', 'Internal Medicine I', 'Family and Community Medicine II'],
    'Third Year': ['Surgery II', 'Pediatrics II', 'Internal Medicine II', 'Obstetrics and Gynecology', 'Family and Community Medicine III', 'Neurology', 'Otolaryngology', 'Radiology', 'Ophthalmology', 'Legal Medicine, Medical Jurisprudence, and Forensic Science'],
    'Fourth Year': ['Clinical Clerkship in Surgery', 'Clinical Clerkship in Pediatrics', 'Clinical Clerkship in Internal Medicine', 'Clinical Clerkship in Obstetrics and Gynecology', 'Clinical Clerkship in Family and Community Medicine', 'Clinical Clerkship in Psychiatry', 'Clinical Clerkship in Neurology', 'Clinical Clerkship in Ophthalmology', 'Clinical Clerkship in Otolaryngology', 'Clinical Clerkship in Anesthesia', 'Clinical Clerkship in Laboratory', 'Clinical Clerkship in Radiology']
}

# --- Google Drive & Sheets Integration ---
@st.cache_resource
def get_gdrive_creds():
    """Authenticates with Google using Streamlit Secrets."""
    try:
        return Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/drive"],
        )
    except Exception as e:
        st.error(f"Error authenticating with Google: {e}")
        return None

def get_gdrive_service():
    """Returns an authenticated Drive service object."""
    creds = get_gdrive_creds()
    if creds:
        return build('drive', 'v3', credentials=creds)
    return None

@st.cache_data(ttl=600) # Cache file downloads for 10 minutes
def download_file_from_drive(_service, file_id):
    """Downloads a file's content from Google Drive."""
    try:
        request = _service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoUploader(file_content, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        st.toast("Download ready!")
        return file_content.getvalue()
    except Exception as e:
        st.error(f"Failed to download file: {e}")
        return None

def upload_to_drive(service, file_obj, title):
    """Uploads a file object to a specific Google Drive folder."""
    folder_id = st.secrets.get("gdrive_folder_id", "")
    if not folder_id:
        st.error("Google Drive folder ID is not configured in secrets.")
        return None
        
    file_metadata = {'name': title, 'parents': [folder_id]}
    media = MediaIoUploader(io.BytesIO(file_obj.getvalue()), mimetype=file_obj.type)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')


# --- Helper Functions ---
def display_subjects_grid(subjects_list, key_prefix=""):
    """Displays a list of subjects in a responsive grid."""
    cols = st.columns(4)
    for i, subject in enumerate(subjects_list):
        with cols[i % 4]:
            if st.button(subject, key=f"{key_prefix}_{subject}_{i}", use_container_width=True):
                st.toast(f"Starting quiz for {subject}...")

# --- Page Rendering Functions ---
def dashboard_page():
    st.header("Dashboard")
    st.write("Browse subjects by year level.")
    
    tabs = st.tabs(list(SUBJECTS_BY_YEAR.keys()))
    
    for i, year_name in enumerate(SUBJECTS_BY_YEAR.keys()):
        with tabs[i]:
            display_subjects_grid(SUBJECTS_BY_YEAR[year_name], key_prefix=f"dash_{year_name}")

def quiz_page():
    st.header("Quiz Center")
    search_term = st.text_input("Search for a subject to start a quiz...", key="quiz_search")
    
    filtered_subjects = [s for s in ALL_SUBJECTS if search_term.lower() in s.lower()]
    display_subjects_grid(filtered_subjects, key_prefix="quiz")

def mock_exams_page():
    st.header("Mock Exams")
    search_term = st.text_input("Search for a subject to start a mock exam...", key="mock_exam_search")

    filtered_subjects = [s for s in ALL_SUBJECTS if search_term.lower() in s.lower()]
    display_subjects_grid(filtered_subjects, key_prefix="mock")

def reviewers_page():
    st.header("Reviewer Library")

    if 'reviewers' not in st.session_state:
        st.session_state.reviewers = [
            {'title': 'Comprehensive Anatomy Notes', 'subject': 'Anatomy', 'uploader': 'Dr. Maria Santos', 'file_id': 'DUMMY_ID_1'},
            {'title': 'Key Concepts in Physiology', 'subject': 'Physiology', 'uploader': 'Dr. John Doe', 'file_id': 'DUMMY_ID_2'},
        ]
        
    with st.expander("Upload a New Reviewer"):
        with st.form("upload_form", clear_on_submit=True):
            title = st.text_input("Reviewer Title")
            subject = st.selectbox("Subject", options=ALL_SUBJECTS)
            uploaded_file = st.file_uploader("Upload PDF File", type=['pdf'])
            submitted = st.form_submit_button("Upload")
            
            if submitted and title and subject and uploaded_file:
                drive_service = get_gdrive_service()
                if drive_service:
                    with st.spinner("Uploading file to Google Drive..."):
                        file_id = upload_to_drive(drive_service, uploaded_file, f"{title} - {subject}.pdf")
                        if file_id:
                            st.session_state.reviewers.insert(0, {'title': title, 'subject': subject, 'uploader': st.session_state.user_name, 'file_id': file_id})
                            st.success(f"'{title}' uploaded successfully!")
                        else:
                            st.error("File upload failed.")

    search_term = st.text_input("Search reviewers by title or subject...", key="reviewer_search")
    st.markdown("---")
    
    filtered_reviewers = [
        r for r in st.session_state.reviewers 
        if search_term.lower() in r['title'].lower() or search_term.lower() in r['subject'].lower()
    ]
    
    if not filtered_reviewers:
        st.info("No reviewers found.")
    else:
        drive_service = get_gdrive_service()
        for i, reviewer in enumerate(filtered_reviewers):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{reviewer['title']}**")
                    st.markdown(f"*{reviewer['subject']}*")
                    st.caption(f"Uploaded by: {reviewer['uploader']}")
                with col2:
                    if drive_service and not reviewer['file_id'].startswith('DUMMY_ID'):
                        file_content = download_file_from_drive(drive_service, reviewer['file_id'])
                        if file_content:
                            st.download_button(
                                label="Download",
                                data=file_content,
                                file_name=f"{reviewer['title']}.pdf",
                                mime="application/pdf",
                                key=f"download_{i}",
                                use_container_width=True
                            )
                    else:
                         st.button("Download", key=f"download_{i}", disabled=True, use_container_width=True, help="This is sample data. Real uploaded files will be downloadable.")


def profile_page():
    st.header("User Profile")

    if 'user_name' not in st.session_state: st.session_state.user_name = "Dr. Juan Dela Cruz"
    if 'user_email' not in st.session_state: st.session_state.user_email = "juandelacruz.md@email.com"

    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("https://placehold.co/150x150/005A9C/FFFFFF?text=JD", use_column_width=True)
        with col2:
            st.subheader(st.session_state.user_name)
            st.write(st.session_state.user_email)
            with st.expander("Edit Profile"):
                with st.form("profile_form"):
                    new_name = st.text_input("Name", value=st.session_state.user_name)
                    new_email = st.text_input("Email", value=st.session_state.user_email)
                    new_password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm Password", type="password")
                    
                    if st.form_submit_button("Save Changes"):
                        if new_password and new_password != confirm_password: st.error("Passwords do not match.")
                        else:
                            st.session_state.user_name = new_name
                            st.session_state.user_email = new_email
                            st.success("Profile updated successfully!")
                            if new_password: st.info("Password updated.")
                            st.rerun()

    st.subheader("Overall Progress")
    exams_taken = 12 # Example value
    progress_percent = int((exams_taken / len(ALL_SUBJECTS)) * 100)
    st.progress(progress_percent, text=f"{progress_percent}% Complete ({exams_taken} of {len(ALL_SUBJECTS)} subjects)")

# --- Main App Logic ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("SOLID NORTH Medical Review Center")
    with st.form("login_form"):
        st.text_input("Email")
        st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            st.session_state.logged_in = True
            st.rerun()
else:
    with st.sidebar:
        st.title("SOLID NORTH")
        page = st.radio("Navigation", ["Dashboard", "Quiz", "Mock Exams", "Reviewers", "Profile"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if page == "Dashboard": dashboard_page()
    elif page == "Quiz": quiz_page()
    elif page == "Mock Exams": mock_exams_page()
    elif page == "Reviewers": reviewers_page()
    elif page == "Profile": profile_page()


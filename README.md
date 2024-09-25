
# Calendar PDF Generator from ICS File

This is a Streamlit web app that generates calendar PDFs from ICS files. The app allows users to upload `.ics` files, select a start and end date, choose a timezone, and generate downloadable PDF calendars for the selected period.

## Features
- **ICS File Upload**: Upload your `.ics` file containing event data.
- **Date Range Selection**: Pick a start and end date for the calendar generation.
- **Timezone Selection**: Choose your preferred timezone for correct event scheduling.
- **Downloadable PDF**: Download the generated calendar in PDF format.

## Requirements
To run this app, the following Python packages are required:
- `streamlit`
- `pytz`
- `icalendar`
- `python-dateutil`
- `reportlab`

These packages are listed in the `requirements.txt` file and will be automatically installed when deployed using Streamlit Cloud.

## How to Run Locally
To run this app locally, follow these steps:
1. Clone the repository:
   ```
   git clone https://github.com/your-username/your-repository-name.git
   ```
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   streamlit run app.py
   ```

## Deployment on Streamlit Cloud
To deploy this app for free on Streamlit Cloud:
1. Push your repository to GitHub.
2. Go to [Streamlit Cloud](https://streamlit.io/cloud) and link your GitHub account.
3. Deploy the app by selecting your repository and branch.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


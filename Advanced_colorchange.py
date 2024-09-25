import os
import pytz  
from datetime import datetime, timedelta
from dateutil import rrule
from dateutil.rrule import rruleset, rrulestr
from icalendar import Calendar
import calendar as cal_module
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import random
import streamlit as st
from io import BytesIO
from textwrap import wrap

def random_color():
    return colors.Color(random.random(), random.random(), random.random())

def generate_calendar_pdf(events, overrides, year, month, timezone, venue_colors, is_bw):
    page_width, page_height = landscape(A4)
    margin = 0.5 * inch
    title_height = 0.5 * inch
    day_label_height = 0.3 * inch
    usable_width = page_width - 2 * margin
    usable_height = page_height - 2 * margin - title_height - day_label_height
    num_columns = 7
    num_rows = 6
    cell_width = usable_width / num_columns
    cell_height = usable_height / num_rows

    cell_widths = [cell_width] * num_columns
    total_width = sum(cell_widths)
    if total_width < usable_width:
        cell_widths[-1] += usable_width - total_width

    events_by_day = {}

    cal = cal_module.Calendar(firstweekday=6)

    cal_matrix = cal.monthdayscalendar(year, month)

    month_start = datetime(year, month, 1, tzinfo=timezone)
    if month == 12:
        month_end = datetime(year + 1, 1, 1, tzinfo=timezone) - timedelta(seconds=1)
    else:
        month_end = datetime(year, month + 1, 1, tzinfo=timezone) - timedelta(seconds=1)

    for event in events:
        event_start = event['DTSTART'].dt
        event_end = event.get('DTEND', event_start).dt

        if isinstance(event_start, datetime) and isinstance(event_end, datetime):
            pass
        elif isinstance(event_start, datetime):
            event_end = event_start + timedelta(hours=1)
        else:
            continue

        if event_start.tzinfo is None:
            event_start = timezone.localize(event_start)
        else:
            event_start = event_start.astimezone(timezone)

        if event_end.tzinfo is None:
            event_end = timezone.localize(event_end)
        else:
            event_end = event_end.astimezone(timezone)

        if event.get('RRULE'):
            rules = rruleset()

            rrule_str = event['RRULE'].to_ical().decode('utf-8')
            rule = rrulestr(rrule_str, dtstart=event_start)
            rules.rrule(rule)

            exdates = event.get('EXDATE')
            if exdates:
                if hasattr(exdates, 'dts'):
                    for exdate in exdates.dts:
                        rules.exdate(exdate.dt.astimezone(timezone))
                else:
                    for exdate in exdates:
                        if hasattr(exdate, 'dts'):
                            for date in exdate.dts:
                                rules.exdate(date.dt.astimezone(timezone))

            rdates = event.get('RDATE')
            if rdates:
                for rdate in rdates.dts:
                    rules.rdate(rdate.dt.astimezone(timezone))

            occurrences = rules.between(month_start, month_end, inc=True)
            for occ in occurrences:
                event_date = occ.date()
                day = event_date.day
                event_summary = event.get('SUMMARY', 'No Title')
                event_location = event.get('LOCATION', 'No Location')
                event_time = occ.strftime('%H:%M')

                event_details = f"{event_time} - {event_summary} @ {event_location}"
                if day in events_by_day:
                    events_by_day[day].append(event_details)
                else:
                    events_by_day[day] = [event_details]

        else:
            event_date = event_start.date()
            if month_start <= event_start <= month_end:
                event_summary = event.get('SUMMARY', 'No Title')
                event_location = event.get('LOCATION', 'No Location')
                event_time = event_start.strftime('%H:%M')

                event_details = f"{event_time} - {event_summary} @ {event_location}"
                day = event_date.day
                if day in events_by_day:
                    events_by_day[day].append(event_details)
                else:
                    events_by_day[day] = [event_details]

    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=landscape(A4))

    pdf.setFont("Helvetica-Bold", 16)
    title_y_position = page_height - margin - title_height / 2
    pdf.drawCentredString(page_width / 2, title_y_position, f"{cal_module.month_name[month]} {year}")

    days_of_week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    pdf.setFont("Helvetica-Bold", 12)
    x_positions = [margin + sum(cell_widths[:i]) + cell_widths[i] / 2 for i in range(num_columns)]
    y_day_label = page_height - margin - title_height - day_label_height / 2
    for x, day_name in zip(x_positions, days_of_week):
        pdf.drawCentredString(x, y_day_label, day_name)

    def wrap_text(text, max_width, font_size):
        avg_char_width = font_size * 0.5
        max_chars = int(max_width / avg_char_width)
        return wrap(text, width=max_chars)

    pdf.setFont("Helvetica", 8)

    grid_start_x = margin
    grid_start_y = page_height - margin - title_height - day_label_height

    for week_idx, week in enumerate(cal_matrix):
        y = grid_start_y - week_idx * cell_height
        for day_idx, day in enumerate(week):
            x = grid_start_x + sum(cell_widths[:day_idx])
            cell_w = cell_widths[day_idx]

            pdf.setStrokeColor(colors.black)
            pdf.rect(x, y - cell_height, cell_w, cell_height)

            if day != 0:
                pdf.setFillColor(colors.black)
                pdf.drawString(x + 2, y - 12, str(day))

                if day in events_by_day:
                    events_list = events_by_day[day]
                    y_offset = 22
                    for event in events_list:
                        wrapped_event = wrap_text(event, max_width=cell_w - 4, font_size=8)

                        event_location = event.split("@")[-1].strip()

                        if is_bw:
                            pdf.setFillColor(colors.black)
                        else:
                            pdf.setFillColor(venue_colors.get(event_location, colors.black))

                        for line in wrapped_event:
                            if y - y_offset > y - cell_height:
                                pdf.drawString(x + 2, y - y_offset, line)
                                y_offset += 10
                            else:
                                pdf.drawString(x + 2, y - cell_height + 2, "...")
                                break

    pdf.save()
    pdf_buffer.seek(0)

    return pdf_buffer

def load_and_process_calendar_data(ics_file, timezone):
    calendar_data = Calendar.from_ical(ics_file.read())
    events = []
    overrides = {}
    venues = set()
    for component in calendar_data.walk():
        if component.name == "VEVENT":
            if component.get('LOCATION'):
                venues.add(component.get('LOCATION'))
            if component.get('RECURRENCE-ID'):
                rec_id = component['RECURRENCE-ID'].dt
                if isinstance(rec_id, datetime):
                    rec_id = rec_id.astimezone(timezone).replace(tzinfo=None)
                else:
                    continue
                overrides[rec_id] = component
            else:
                events.append(component)
    return events, overrides, venues

def main():
    st.title("Calendar PDF Generator from ICS File")
    
    ics_file = st.file_uploader("Upload your ICS file", type="ics")
    
    if ics_file is not None:
        start_date = st.date_input("Select start date", value=datetime.now().date())
        end_date = st.date_input("Select end date", value=datetime.now().date() + timedelta(days=365))

        color_mode = st.radio("Choose mode:", ["Black & White", "Color"])

        timezones = pytz.all_timezones
        selected_timezone = st.selectbox("Select Timezone", timezones, index=timezones.index("America/New_York"))
        timezone = pytz.timezone(selected_timezone)

        events, overrides, venues = load_and_process_calendar_data(ics_file, timezone)

        if "venue_colors" not in st.session_state:
            venue_colors = {venue: random_color() for venue in venues}
            st.session_state["venue_colors"] = venue_colors
        else:
            venue_colors = st.session_state["venue_colors"]

        if color_mode == "Color":
            st.write("Customize Venue Colors:")
            for venue in venues:
                current_color = venue_colors[venue]
                color_hex = '#%02X%02X%02X' % (int(current_color.red * 255), int(current_color.green * 255), int(current_color.blue * 255))
                chosen_color = st.color_picker(f"Pick a color for {venue}:", value=color_hex)
                venue_colors[venue] = colors.HexColor(chosen_color)

        start_year = start_date.year
        start_month = start_date.month
        end_year = end_date.year
        end_month = end_date.month

        current_year, current_month = start_year, start_month
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            pdf_buffer = generate_calendar_pdf(events, overrides, current_year, current_month, timezone, venue_colors, color_mode == "Black & White")

            st.download_button(
                label=f"Download calendar for {current_year}-{current_month:02d}",
                data=pdf_buffer,
                file_name=f"calendar_{current_year}_{current_month:02d}.pdf",
                mime="application/pdf"
            )

            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

if __name__ == "__main__":
    main()

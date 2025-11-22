# app.py
import streamlit as st
from db import Session, Seat, Room, init_db
import bcrypt
import pandas as pd
import csv
import os

st.set_page_config(page_title="Seating Plan", layout="wide")
init_db()

# PASTE your hash here from create_hash.py, e.g. ADMIN_PASSWORD_HASH = b'$2b$12$...'
ADMIN_PASSWORD_HASH = b'$2b$12$aFWRxMrXOziK.qeWKkUB1u8RTQwc/Lqpp.n1A4b9nnTh4QFx0gP0W'


def check_admin_password(plain_text):
    if not ADMIN_PASSWORD_HASH:
        return False
    return bcrypt.checkpw(plain_text.encode(), ADMIN_PASSWORD_HASH)

def get_session():
    return Session()

def student_lookup_page():
    st.title("Student Seat Lookup")
    st.write("Enter your enrolment number to find your room and seat.")
    enrol = st.text_input("Enrolment number", value="", placeholder="e.g., 23BCA010001")
    if st.button("Find my seat"):
        enrol = enrol.strip()
        if enrol == "":
            st.warning("Please enter an enrolment number.")
            return
        s = get_session()
        seat = s.query(Seat).filter_by(enrolment_no=enrol).first()
        if seat:
            room = s.query(Room).filter_by(id=seat.room_id).first()
            st.success(f"Room: **{room.room_code if room else 'Unknown'}**  ·  Seat: **{seat.seat_no}**")
            st.write("Student name:", seat.student_name or "-")
        else:
            st.error("Seat not found. Try different format or contact admin.")
        s.close()

def admin_page():
    st.title("Admin Dashboard")
    if 'admin_logged' not in st.session_state:
        st.session_state['admin_logged'] = False

    if not st.session_state['admin_logged']:
        pw = st.text_input("Admin password", type="password")
        if st.button("Login as admin"):
            if check_admin_password(pw):
                st.session_state['admin_logged'] = True
                st.success("Logged in as admin.")
            else:
                st.error("Wrong password.")
        return

    # Admin area
    st.success("You are admin. Use the controls below.")
    uploaded = st.file_uploader("Upload seating CSV", type=["csv"])
    if uploaded is not None:
        df = pd.read_csv(uploaded)
        st.subheader("Preview of uploaded CSV")
        st.dataframe(df.head())
        if st.button("Import uploaded CSV"):
            tmp = "uploaded_seating.csv"
            df.to_csv(tmp, index=False)
            import db
            db.import_csv(tmp)
            st.success("Imported uploaded CSV into DB.")

    # show rooms
    s = get_session()
    rooms = s.query(Room).order_by(Room.room_code).all()
    if not rooms:
        st.info("No rooms found in DB. Import a CSV first.")
    for room in rooms:
        with st.expander(f"Room: {room.room_code}", expanded=False):
            seats = s.query(Seat).filter_by(room_id=room.id).order_by(Seat.seat_no).all()
            if not seats:
                st.write("No seats for this room.")
                continue
            df = pd.DataFrame([{"Seat": seat.seat_no, "Enrolment": seat.enrolment_no or "", "Name": seat.student_name or "", "id": seat.id} for seat in seats])
            st.dataframe(df[["Seat","Enrolment","Name"]])
            # Quick assign area
            seat_choices = [str(seat.seat_no) for seat in seats]
            seat_choice = st.selectbox(f"Choose seat to edit in {room.room_code}", seat_choices, key=f"seat_select_{room.id}")
            new_enrol = st.text_input("New enrolment (leave empty to unassign)", key=f"enrol_input_{room.id}")
            new_name = st.text_input("Student name", key=f"name_input_{room.id}")
            if st.button("Assign / Update seat", key=f"assign_btn_{room.id}"):
                seat_obj = s.query(Seat).filter_by(room_id=room.id, seat_no=seat_choice).first()
                if seat_obj:
                    # Prevent duplicate enrolment
                    if new_enrol.strip():
                        existing = s.query(Seat).filter(Seat.enrolment_no == new_enrol.strip(), Seat.id != seat_obj.id).first()
                        if existing:
                            st.warning("This enrolment is already assigned to another seat. Unassign it there first.")
                        else:
                            seat_obj.enrolment_no = new_enrol.strip()
                            seat_obj.student_name = new_name.strip() or None
                            s.commit()
                            st.success("Seat updated.")
                    else:
                        # unassign
                        seat_obj.enrolment_no = None
                        seat_obj.student_name = None
                        s.commit()
                        st.success("Seat unassigned.")
                else:
                    st.error("Seat not found.")
    # Export buttons (per room)
    st.markdown("---")
    st.subheader("Export")
    for room in rooms:
        if st.button(f"Export {room.room_code} to CSV", key=f"export_csv_{room.id}"):
            seats = s.query(Seat).filter_by(room_id=room.id).all()
            out = f"export_{room.room_code}.csv"
            with open(out, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["room","seat_no","enrolment_no","student_name"])
                for seat in seats:
                    writer.writerow([room.room_code, seat.seat_no, seat.enrolment_no or "", seat.student_name or ""])
            with open(out, "rb") as f:
                st.download_button(f"Download {room.room_code} CSV", data=f, file_name=out, mime="text/csv")
    s.close()

def main():
    st.sidebar.title("Seating Plan")
    page = st.sidebar.radio("Choose", ["Student", "Admin"])
    if page == "Student":
        student_lookup_page()
    else:
        admin_page()

if __name__ == "__main__":
    main()

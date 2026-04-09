"""
QR/badge-based patient check-in and lookup workflow (non-biometric).

How it works:
1) Security gate scans a patient's QR/badge code.
2) If patient is new, terminal prompts for demographics once and saves them.
3) Future scans load the same patient profile instantly.
4) Every scan is logged with timestamp.

Run:
    python qr_patient_checkin.py --mode security
    python qr_patient_checkin.py --mode doctor
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import cv2

DISTRICTS = {
    "city of cape town": "City of Cape Town",
    "cape winelands": "Cape Winelands",
    "garden route": "Garden Route",
}
FACILITIES_BY_DISTRICT = {
    "City of Cape Town": {"Khayelitsha CHC", "Mitchell's Plain CDC", "Gugulethu CHC"},
    "Cape Winelands": {"Stellenbosch Clinic", "Paarl East Clinic", "Worcester Hospital"},
    "Garden Route": {"George Hospital", "Mossel Bay Clinic"},
}
DISEASE_GROUPS = {
    "ALRI",
    "HIV",
    "Injury",
    "Maternal",
    "Mental Health",
    "NCD",
    "Other",
    "TB",
}
ICD10_PATTERN = re.compile(r"^[A-TV-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QR/badge patient check-in and lookup.")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index")
    parser.add_argument(
        "--backend",
        choices=["auto", "msmf", "dshow"],
        default="auto",
        help="Camera backend on Windows",
    )
    parser.add_argument(
        "--mode",
        choices=["security", "doctor"],
        default="security",
        help="Workflow mode",
    )
    parser.add_argument("--patients-db", default="patients.json", help="Patient database file")
    parser.add_argument("--checkins-log", default="checkins.json", help="Check-in log file")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print data quality and burden summary from check-in log, then exit.",
    )
    return parser.parse_args()


def load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {path}")
    return data


def save_json_list(path: Path, data: list[dict]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def find_patient(patients: list[dict], patient_id: str) -> dict | None:
    for patient in patients:
        if str(patient.get("patient_id")) == patient_id:
            return patient
    return None


def prompt_value(
    label: str,
    validator,
    *,
    optional: bool = False,
    default: str | None = None,
) -> str | int | float | None:
    while True:
        shown_default = f" [{default}]" if default is not None else ""
        raw = input(f"{label}{shown_default}: ").strip()
        if raw == "" and default is not None:
            raw = default
        if raw == "" and optional:
            return None
        try:
            return validator(raw)
        except ValueError as exc:
            print(f"Invalid input: {exc}")


def validate_required_text(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Value is required.")
    return cleaned


def normalize_gender(value: str) -> str:
    v = value.strip().lower()
    mapping = {
        "f": "F",
        "female": "F",
        "m": "M",
        "male": "M",
        "o": "Other",
        "other": "Other",
        "u": "Unknown",
        "unknown": "Unknown",
    }
    if v not in mapping:
        raise ValueError("Use one of: F, M, Other, Unknown")
    return mapping[v]


def validate_age(value: str) -> int:
    age = int(value)
    if age < 0 or age > 120:
        raise ValueError("Age must be between 0 and 120.")
    return age


def validate_phone(value: str) -> str:
    cleaned = value.strip()
    if not re.fullmatch(r"[+\d][\d\s()-]{5,20}", cleaned):
        raise ValueError("Phone must look like a valid local/international number.")
    return cleaned


def normalize_district(value: str) -> str:
    key = value.strip().lower()
    if key not in DISTRICTS:
        options = ", ".join(sorted(DISTRICTS.values()))
        raise ValueError(f"District must be one of: {options}")
    return DISTRICTS[key]


def validate_facility_for_district(district: str, facility: str) -> str:
    cleaned = facility.strip()
    if not cleaned:
        raise ValueError("Facility name is required.")
    known = FACILITIES_BY_DISTRICT.get(district, set())
    if known and cleaned not in known:
        options = ", ".join(sorted(known))
        raise ValueError(f"Facility must match district '{district}'. Expected one of: {options}")
    return cleaned


def normalize_disease_group(value: str) -> str:
    cleaned = value.strip()
    for known in DISEASE_GROUPS:
        if cleaned.lower() == known.lower():
            return known
    options = ", ".join(sorted(DISEASE_GROUPS))
    raise ValueError(f"Disease group must be one of: {options}")


def validate_icd10(value: str) -> str:
    cleaned = value.strip().upper()
    if not ICD10_PATTERN.fullmatch(cleaned):
        raise ValueError("ICD-10 format should be like I10, J06.9, E11, B20.")
    return cleaned


def validate_optional_float(value: str, min_value: float, max_value: float) -> float:
    number = float(value)
    if number < min_value or number > max_value:
        raise ValueError(f"Value must be between {min_value} and {max_value}.")
    return round(number, 1)


def validate_optional_int(value: str, min_value: int, max_value: int) -> int:
    number = int(value)
    if number < min_value or number > max_value:
        raise ValueError(f"Value must be between {min_value} and {max_value}.")
    return number


def validate_visit_date(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Visit date must be YYYY-MM-DD.") from exc
    return parsed.strftime("%Y-%m-%d")


def age_band_from_age(age: int | str | None) -> str:
    if age is None:
        return "Unknown"
    try:
        parsed = int(age)
    except (TypeError, ValueError):
        return "Unknown"
    if parsed <= 4:
        return "0-4"
    if parsed <= 14:
        return "5-14"
    if parsed <= 49:
        return "15-49"
    if parsed <= 64:
        return "50-64"
    return "65+"


def next_visit_id(checkins: list[dict]) -> int:
    max_seen = 0
    for row in checkins:
        visit_id = row.get("visit_id")
        if isinstance(visit_id, int):
            max_seen = max(max_seen, visit_id)
        elif isinstance(visit_id, str) and visit_id.isdigit():
            max_seen = max(max_seen, int(visit_id))
    return max_seen + 1


def register_patient(patient_id: str) -> dict:
    print(f"New patient ID detected: {patient_id}")
    full_name = prompt_value("Enter full name", validate_required_text)
    age = prompt_value("Enter age", validate_age)
    sex = prompt_value("Enter sex (F/M/Other/Unknown)", normalize_gender)
    phone = prompt_value("Enter phone number", validate_phone, optional=True)
    return {
        "patient_id": patient_id,
        "full_name": full_name,
        "age": age,
        "sex": sex,
        "phone": phone or "unknown",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def collect_visit_details(mode: str, patient: dict | None, checkins: list[dict]) -> dict:
    visit_id = next_visit_id(checkins)
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    patient_age = patient.get("age") if patient else None
    patient_gender = patient.get("sex") if patient else None

    print("Capture visit details for analytics and reporting.")
    visit_date = prompt_value("Visit date (YYYY-MM-DD)", validate_visit_date, default=today)
    district = prompt_value("District", normalize_district)
    facility_name = prompt_value(
        "Facility name",
        lambda v: validate_facility_for_district(district, v),
    )
    icd10_code = prompt_value("ICD-10 code", validate_icd10)
    disease_group = prompt_value("Disease group", normalize_disease_group)
    bmi = prompt_value("BMI (optional)", lambda v: validate_optional_float(v, 8.0, 80.0), optional=True)
    systolic_bp = prompt_value(
        "Systolic BP (optional)",
        lambda v: validate_optional_int(v, 40, 300),
        optional=True,
    )
    diastolic_bp = prompt_value(
        "Diastolic BP (optional)",
        lambda v: validate_optional_int(v, 30, 220),
        optional=True,
    )

    return {
        "visit_id": visit_id,
        "visit_date": visit_date,
        "age": patient_age,
        "age_band": age_band_from_age(patient_age),
        "gender": patient_gender,
        "district": district,
        "facility_name": facility_name,
        "icd10_code": icd10_code,
        "disease_group": disease_group,
        "bmi": bmi,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "intake_source": mode,
    }


def print_checkin_summary(checkins: list[dict]) -> None:
    print("\nPHDC // Python Health Analytics Workbook")
    if not checkins:
        print("No check-in records found.")
        return

    visits = [row for row in checkins if "visit_date" in row or "disease_group" in row]
    total_visits = len(visits)
    unique_patients = len({str(row.get("patient_id")) for row in checkins if row.get("patient_id") is not None})
    facilities = len({row.get("facility_name") for row in visits if row.get("facility_name")})
    districts = len({row.get("district") for row in visits if row.get("district")})

    visit_dates = []
    for row in visits:
        value = row.get("visit_date")
        if isinstance(value, str):
            try:
                visit_dates.append(datetime.strptime(value, "%Y-%m-%d"))
            except ValueError:
                continue

    print(f"{total_visits:,} visits · {facilities} facilities · {districts} districts")
    print(f"Unique patients: {unique_patients}")
    if visit_dates:
        start = min(visit_dates).strftime("%b %Y")
        end = max(visit_dates).strftime("%b %Y")
        month_span = (max(visit_dates).year - min(visit_dates).year) * 12 + max(visit_dates).month - min(visit_dates).month + 1
        print(f"Date range: {start} – {end} ({month_span} months)")

    audited_columns = ["gender", "age", "bmi", "systolic_bp", "diastolic_bp"]
    print("\nData quality audit (missing values):")
    for column in audited_columns:
        missing = 0
        for row in visits:
            val = row.get(column)
            if val is None or val == "" or str(val).lower() == "unknown":
                missing += 1
        pct = (missing / total_visits * 100) if total_visits else 0.0
        print(f"- {column}: {missing} missing ({pct:.1f}%)")

    by_disease = Counter(row.get("disease_group") for row in visits if row.get("disease_group"))
    by_district = Counter(row.get("district") for row in visits if row.get("district"))
    print("\nVisits by disease group:")
    for disease, count in by_disease.most_common():
        print(f"- {disease}: {count}")
    print("\nVisits by district:")
    for district_name, count in by_district.most_common():
        print(f"- {district_name}: {count}")

    burden = defaultdict(Counter)
    for row in visits:
        age_band = row.get("age_band") or age_band_from_age(row.get("age"))
        disease_group = row.get("disease_group")
        if disease_group:
            burden[age_band][disease_group] += 1

    if burden:
        highest = ("Unknown", "Unknown", 0)
        print("\nDisease burden pivot table (visit counts):")
        for band in ["0-4", "5-14", "15-49", "50-64", "65+", "Unknown"]:
            if band not in burden:
                continue
            entries = ", ".join(f"{k}: {v}" for k, v in sorted(burden[band].items()))
            total = sum(burden[band].values())
            print(f"- {band} -> {entries} [total: {total}]")
            for disease, count in burden[band].items():
                if count > highest[2]:
                    highest = (band, disease, count)
        print(f"\nHighest burden cell: {highest[1]} in age band {highest[0]} ({highest[2]} visits)")


def draw_status(frame, mode: str, status: str, color: tuple[int, int, int]) -> None:
    cv2.putText(frame, f"Mode: {mode}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, status, (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(
        frame,
        "Show QR/badge | Press i = manual ID | Press q = quit",
        (20, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (220, 220, 220),
        1,
    )


def process_patient_id(
    patient_id: str,
    mode: str,
    patients: list[dict],
    checkins: list[dict],
    patients_db_file: Path,
    checkins_log_file: Path,
) -> tuple[str, tuple[int, int, int]]:
    now = datetime.now()
    patient = find_patient(patients, patient_id)

    if patient is None and mode == "security":
        patient = register_patient(patient_id)
        patients.append(patient)
        save_json_list(patients_db_file, patients)
        print(f"Registered patient: {patient['full_name']} ({patient_id})")

    if patient is None and mode == "doctor":
        print(f"Unknown patient ID in doctor mode: {patient_id}")
        return "Unknown patient ID", (0, 0, 255)

    visit_details = collect_visit_details(mode=mode, patient=patient, checkins=checkins)
    record = {
        "timestamp": now.isoformat(timespec="seconds"),
        "mode": mode,
        "patient_id": patient_id,
        "patient_name": patient["full_name"] if patient else "unknown",
        **visit_details,
    }
    checkins.append(record)
    save_json_list(checkins_log_file, checkins)

    if patient:
        print(
            f"[{mode.upper()}] {patient['full_name']} | "
            f"ID: {patient_id} | Age: {patient.get('age', 'unknown')} | "
            f"Sex: {patient.get('sex', patient.get('gender', 'unknown'))} | "
            f"Disease: {record.get('disease_group', 'n/a')} | District: {record.get('district', 'n/a')}"
        )
        return f"{patient['full_name']} ({patient_id})", (0, 255, 0)
    return f"Checked in ({patient_id})", (0, 255, 0)


def main() -> None:
    args = parse_args()
    patients_db_file = Path(args.patients_db)
    checkins_log_file = Path(args.checkins_log)

    patients = load_json_list(patients_db_file)
    checkins = load_json_list(checkins_log_file)
    if args.summary_only:
        print_checkin_summary(checkins)
        return

    if args.backend == "dshow":
        backend = cv2.CAP_DSHOW
    elif args.backend == "msmf":
        backend = cv2.CAP_MSMF
    else:
        backend = cv2.CAP_ANY

    cap = cv2.VideoCapture(args.camera, backend)
    if not cap.isOpened() and args.backend == "auto":
        cap.release()
        cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open webcam (index {args.camera}) with backend '{args.backend}'."
        )

    qr_detector = cv2.QRCodeDetector()
    last_scanned_data = ""
    last_scan_time = datetime.min

    print(f"Started {args.mode} workflow.")
    print(f"Patients DB: {patients_db_file.resolve()}")
    print(f"Check-in log: {checkins_log_file.resolve()}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Warning: Failed to read webcam frame.")
            break

        status = "Waiting for QR/badge..."
        status_color = (0, 255, 255)

        data, points, _ = qr_detector.detectAndDecode(frame)
        if not data:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            enhanced = cv2.equalizeHist(gray)
            data, points, _ = qr_detector.detectAndDecode(enhanced)

        if points is not None:
            pts = points.astype(int).reshape(-1, 2)
            for i in range(len(pts)):
                p1 = tuple(pts[i])
                p2 = tuple(pts[(i + 1) % len(pts)])
                cv2.line(frame, p1, p2, (255, 255, 0), 2)

        if data:
            now = datetime.now()
            # Debounce duplicate reads of the same code.
            if data == last_scanned_data and (now - last_scan_time).total_seconds() < 2:
                draw_status(frame, args.mode, "QR read (debounced)...", (160, 160, 160))
                cv2.imshow("QR Patient Check-in", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            patient_id = data.strip()
            status, status_color = process_patient_id(
                patient_id=patient_id,
                mode=args.mode,
                patients=patients,
                checkins=checkins,
                patients_db_file=patients_db_file,
                checkins_log_file=checkins_log_file,
            )

            last_scanned_data = data
            last_scan_time = now

        draw_status(frame, args.mode, status, status_color)
        cv2.imshow("QR Patient Check-in", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("i"):
            manual_id = input("Manual patient ID: ").strip()
            if manual_id:
                status, status_color = process_patient_id(
                    patient_id=manual_id,
                    mode=args.mode,
                    patients=patients,
                    checkins=checkins,
                    patients_db_file=patients_db_file,
                    checkins_log_file=checkins_log_file,
                )
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

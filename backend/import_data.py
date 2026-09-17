import os
import sys
import pandas as pd

# Allow importing models.py from the backend folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Project


# CSV location
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "mplad_projects.csv")


def import_projects():
    print("Reading CSV...")

    df = pd.read_csv(CSV_PATH)

    print(f"CSV contains {len(df)} projects.")

    with app.app_context():
        db.create_all()

        # Avoid importing duplicates
        existing_ids = {
            project.unique_work_number
            for project in Project.query.all()
        }

        new_projects = []

        for _, row in df.iterrows():

            work_number = str(row["unique_work_number"])

            if work_number in existing_ids:
                continue

            project = Project(
                unique_work_number=work_number,
                state=row["state"],
                constituency=row["constituency"],
                mp_name=row["mp_name"],
                work_category=row["work_category"],
                work_name=row["work_name"],
                sanction_amount=row["sanction_amount"],
                date_of_administrative_approval=row[
                    "date_of_administrative_approval"
                ],
                expected_completion_date=row[
                    "expected_completion_date"
                ],
                implementing_agency_name=row[
                    "implementing_agency_name"
                ],
                work_status=row["work_status"],
            )

            new_projects.append(project)

        db.session.add_all(new_projects)
        db.session.commit()

        total_projects = Project.query.count()

        print(f"Imported {len(new_projects)} new projects.")
        print(f"Total projects in database: {total_projects}")


if __name__ == "__main__":
    import_projects()
import csv
import json
import os
import requests
from requests import HTTPError

TICKET_NUMBER = "Ticket # Full 13 digits please! )"
AIRLINE = "Airline"
TICKET_VALUE = "Ticket Value "
AIRLINE_PENALTY = "Airline Penalty"
TICKET_DATE_OF_ISSUE = "Ticket DOI"
AIRLINE_CONFIRMATION = "Airline Confirmation #"
NOTES = "Notes about booking"


def row_is_irrelevant(row):
    return (
        "YELLOW" in row[TICKET_NUMBER]
        or "ORANGE" in row[TICKET_NUMBER]
        or not any(v for k, v in row.items() if k)
        or row.get("result") == "✔"
    )


class FailedCreditUploadException(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors


def _make_gql_call(operation, gql):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(os.environ["BACH_LOLA_TOKEN"]),
    }
    params = (("op", operation),)
    response = requests.post(
        "https://api.lola.com/api/graphql", headers=headers, params=params, json=gql
    )
    try:
        response.raise_for_status()
    except HTTPError:
        raise FailedCreditUploadException("HTTP Error", errors=response.text)
    response_json = response.json()
    if response_json["errors"]:
        raise FailedCreditUploadException(
            "GQL returned errors", errors=response_json["errors"]
        )
    return response_json


def _get_draft_credit(ticket_number):

    gql = {
        "query": """
                        query BookingCandidatesForFlightDraftCreditQuery {{
                            candidates(params: {{
                                ticket_number: "{ticket_number}",
                            }}) {{
                                booking_id
                                traveler_name
                                departure_airport_code
                                arrival_airport_code
                                departure_time
                                arrival_time
                                airline_code
                                airline_short_name
                                airline_confirmation
                                booking_traveler_profile_id
                                passenger_fare_id
                                owning_user_group_id
                                owning_user_group_name
                                ticket_mco_number
                                office_id
                                issue_date
                                flight_booking_info_id
                            }}
                        }}
                    """.format(
            ticket_number=ticket_number.strip().replace("-", "")
        )
    }
    return _make_gql_call("BookingCandidatesForFlightDraftCredit", gql)


def _upload_final_credit(credit, draft_credit):
    try:
        credit_value = int(
            float(credit["ticket_value"].replace("$", "").replace(",", "").strip())
            * 100.0
        )
    except ValueError:
        raise FailedCreditUploadException(
            f"Could not convert value for credit {credit['ticket_value']}",
            errors=["Could not translate ticket value"],
        )
    try:
        penalty_value = int(
            float(credit["airline_penalty"].replace("$", "").replace(",", "").strip())
            * 100.0
        )
    except ValueError:
        raise FailedCreditUploadException(
            f"Could not convert value for penalty {credit['airline_penalty']}",
            errors=["could not translate penalty"],
        )
    gql = {
        "query": """
            mutation CreateFlightBookingCredit {{
                create_flight_booking_credit(
                    credit_data: {{
                        booking_id: "{booking_id}",
                        booking_traveler_profile_id: "{booking_traveler_profile_id}",
                        owning_user_group_id: "{owning_user_group_id}",
                        passenger_fare_id: "{passenger_fare_id}",
                        flight_booking_info_id: "{flight_booking_info_id}",
                        issue_date: "{issue_date}",
                        credit: {credit},
                        penalty: {penalty},
                        notes: "{notes}",
                        ticket_mco_number: "{ticket_mco_number}",
                        airline_short_name: "{airline_short_name}",
                        airline_code: "{airline_code}",
                        airline_confirmation: "{airline_confirmation}"
                    }}
                ) {{
                    ok
                    flight_booking_credit {{
                        id,
                        booking_id,
                        booking_traveler_profile {{ id, first_name, last_name }},
                        owning_user_group {{ id, name }},
                        parent {{ id }},
                        passenger_fare {{ id, pnr }},
                        flight_booking_info {{ id, office_id }},
                        issue_date,
                        credit,
                        penalty,
                        notes,
                        ticket_mco_number,
                        airline_short_name,
                        airline_code,
                        airline_confirmation
                    }}
                }}
            }}
        """.format(
            booking_id=draft_credit["booking_id"],
            booking_traveler_profile_id=draft_credit["booking_traveler_profile_id"],
            owning_user_group_id=draft_credit["owning_user_group_id"],
            passenger_fare_id=draft_credit["passenger_fare_id"],
            flight_booking_info_id=draft_credit["flight_booking_info_id"],
            issue_date=draft_credit["issue_date"],
            credit=credit_value,
            penalty=penalty_value,
            notes=credit["notes"],
            ticket_mco_number=draft_credit["ticket_mco_number"],
            airline_short_name=draft_credit["airline_short_name"],
            airline_code=draft_credit["airline_code"],
            airline_confirmation=draft_credit["airline_confirmation"],
        )
    }
    return _make_gql_call("CreateFlightBookingCredit", gql)


def upload_credit(credit):
    # flight_booking_info_id
    # issue_date
    # penalty
    # notes
    # ticket_mco_number
    draft = _get_draft_credit(credit["ticket_number"])
    candidates = draft["data"]["candidates"]
    if not candidates:
        raise FailedCreditUploadException(
            "No Candidates Returned",
            errors=["Could not find lola booking for ticket number"],
        )
    if len(candidates) > 1:
        raise FailedCreditUploadException(
            "Ambiguous Ticket number",
            errors=["Found multiple bookings for this ticket"],
        )
    _upload_final_credit(credit, candidates[0])


def translate_row(row):
    return {
        "ticket_number": row[TICKET_NUMBER],
        "airline": row[AIRLINE],
        "ticket_value": row[TICKET_VALUE],
        "airline_penalty": row[AIRLINE_PENALTY],
        "date_of_issue": row[TICKET_DATE_OF_ISSUE],
        "airline_confirmation": row[AIRLINE_CONFIRMATION],
        "notes": row[NOTES],
    }


def main():
    with open("credits.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [row for row in reader]
        success = 0
        failed = 0
        irrelevant = 0
        for index, row in enumerate(rows):
            if row_is_irrelevant(row):
                irrelevant += 1
                row["result"] = "✔"
                row["errors"] = ""
            else:
                try:
                    upload_credit(translate_row(row))
                    row["result"] = "✔"
                    row["errors"] = ""
                    success += 1
                except FailedCreditUploadException as e:
                    failed += 1
                    row["result"] = "x"
                    row["errors"] = json.dumps(e.errors)
            print(
                f"{index + 1} of {len(rows)} rows complete ({(index+1)/len(rows)}%), {success/((index+1-irrelevant) or 1)} Success, {failed/((index+1-irrelevant)or 1)} Failed"
            )
        with open("result.csv", "w") as outfile:
            csv_writer = csv.DictWriter(outfile, rows[0].keys())
            csv_writer.writerow({key: key for key, value in rows[0].items()})
            for row in rows:
                csv_writer.writerow(row)


if __name__ == "__main__":
    main()

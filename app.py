from logging import exception

from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from flask import Flask, jsonify
from datetime import datetime, date

app = Flask(__name__)

MONGO_URI = "mongodb+srv://Tranzit:fluEqkVVOzm3EGUK@cluster0.7dmohmv.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["Tranzit"]
utenti_collection = db["utenti"]
# Collections relative ai treni di "Trenord"
routes_trenord_collection = db["routes_trenord"]
trips_trenord_collection = db["trips_trenord"]
stop_times_trenord_collection = db["stop_times_trenord"]
stops_trenord_collection= db["stops_trenord"]
agency_trenord_collection = db["agency_trenord"]
calendar_dates_trenord_collection = db["calendar_dates_trenord"]
feed_info_trenord_collection = db["feed_info_trenord"]
# Collections relative ai treni e i bus di "Eav"
routes_eav_collection = db["routes_eav"]
trips_eav_collection = db["trips_eav"]
stop_times_eav_collection = db["stop_times_eav"]
stops_eav_collection= db["stops_eav"]
agency_eav_collection = db["agency_eav"]
calendar_dates_eav_collection = db["calendar_dates_trenord"]
shapes_eav_collection = db["shapes_eav"]

@app.route("/")
def index():
    today = date.today().strftime("%Y-%m-%d")
    return render_template("index.html", today=today)

@app.route("/chiSiamo")
def chi_siamo():
    return render_template("chiSiamo.html")

@app.route("/accedi")
def accedi():
    utenti = list(utenti_collection.find())
    return render_template("accedi.html", utenti=utenti)

@app.route("/registrati")
def registrati():
    return render_template("registrati.html")

@app.route("/profiloUtente")
def profilo_utente():
    return render_template("profiloUtente.html")

@app.route("/statusMobilita")
def status_mobilita():
    return render_template("statusMobilita.html")

@app.route("/risultatiCodTreno")
def risultati_cod_treno():
    return render_template("risultatiCodTreno.html")

@app.route("/tabelloni")
def tabelloni():
    return render_template("tabelloni.html")

def get_stop_id_by_name(stop_name):
    stop = stops_trenord_collection.find_one({"stop_name": stop_name})
    if stop:
        return stop["stop_id"]
    stop_eav = stops_eav_collection.find_one({"stop_name": stop_name})
    if stop_eav:
        return stop_eav["stop_id"]
    return None

@app.route("/add_prenotazioni", methods=["GET", "POST"])
def add_prenotazioni():
    from_name = request.form.get("partenza")
    to_name = request.form.get("destinazione")
    trip_date = request.form.get("dataViaggio")

    if not from_name or not to_name or not trip_date:
        return "Errore: inserisci partenza, destinazione e data", 400

    try:
        date_obj = datetime.strptime(trip_date, "%Y-%m-%d")
        date_gtfs = date_obj.strftime("%Y%m%d")
    except ValueError:
        return "Formato data non valido", 400

    from_id = get_stop_id_by_name(from_name)
    to_id = get_stop_id_by_name(to_name)
    if not from_id or not to_id:
        return f"Stazione non trovata: {from_name if not from_id else ''} {to_name if not to_id else ''}", 404

    # Trova tutti i trip
    trips_trenord = list(trips_trenord_collection.find({}, {"trip_id":1, "route_id":1, "service_id":1, "trip_short_name":1, "_id":0}))
    trips_eav = list(trips_eav_collection.find({}, {"trip_id":1, "route_id":1, "service_id":1, "trip_short_name":1, "_id":0}))
    all_trips = trips_trenord + trips_eav

    # Prepara mapping trip_id -> calendar_dates collection
    calendar_dates_map = {trip["trip_id"]: calendar_dates_trenord_collection for trip in trips_trenord}
    calendar_dates_map.update({trip["trip_id"]: calendar_dates_eav_collection for trip in trips_eav})

    # Carica tutti gli stop_times
    all_stop_times = list(stop_times_trenord_collection.find({}, {"trip_id":1, "stop_id":1, "stop_sequence":1, "departure_time":1, "_id":0}))
    all_stop_times += list(stop_times_eav_collection.find({}, {"trip_id":1, "stop_id":1, "stop_sequence":1, "departure_time":1, "_id":0}))

    # Organizza stop_times per trip
    stop_times_by_trip = {}
    for st in all_stop_times:
        stop_times_by_trip.setdefault(st["trip_id"], []).append(st)

    results = []

    for trip in all_trips:
        trip_id = trip["trip_id"]
        service_id = trip["service_id"]
        times = stop_times_by_trip.get(trip_id, [])
        stops_seq = {st["stop_id"]: st for st in times}

        # Controlla che le stazioni siano presenti e nell'ordine corretto
        if from_id not in stops_seq or to_id not in stops_seq:
            continue
        if stops_seq[from_id]["stop_sequence"] >= stops_seq[to_id]["stop_sequence"]:
            continue

        # Seleziona la collection giusta di calendar_dates
        calendar_dates_coll = calendar_dates_map.get(trip_id)

        # Controllo calendar_dates
        exception = None
        if calendar_dates_coll is not None:
            exception = calendar_dates_coll.find_one({"service_id": service_id, "date": date_gtfs})

        if exception:
            if exception["exception_type"] == 2:
                continue  # servizio cancellato
            # exception_type == 1 -> continua
        else:
            # Controlla calendar.txt corrispondente
            service_coll = calendar_dates_trenord_collection if calendar_dates_coll == calendar_dates_trenord_collection else calendar_dates_eav_collection
            service = None
            if service_coll is not None:
                service = service_coll.find_one({"service_id": service_id})
            if service:
                if not (service["start_date"] <= date_gtfs <= service["end_date"]):
                    continue
                weekday = date_obj.weekday()
                weekdays_map = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
                if service[weekdays_map[weekday]] != 1:
                    continue


        results.append({
            "trip_short_name": int(trip["trip_short_name"]),
            "from_stop": from_name,
            "to_stop": to_name,
            "arrival_time": stops_seq[from_id].get("arrival_time", stops_seq[from_id].get("departure_time", "")),
            "departure_time": stops_seq[to_id]["departure_time"]
        })

    return render_template("treniTrovati.html", tickets=results, from_stop=from_name, to_stop=to_name, date=trip_date)

@app.route("/accedi_utenti", methods=["POST"])
def accedi_utenti():
    username = request.form.get("username")
    password = request.form.get("password")

    if username and password:
        utente_esistente = utenti_collection.find_one({"username": username})
        if utente_esistente:
            return redirect("/profiloUtente")
    else:
        return redirect("/accedi")

@app.route("/add_utenti", methods=["POST"])
def add_utenti():
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    utenti_collection.insert_one({"username": username, "password": password, "email": email})
    return redirect("/profiloUtente")

@app.route("/getStatusTreno", methods=["POST"])
def get_status_treno():
    codTreno = request.form.get("codiceTreno")
    if not codTreno:
        return "Errore: inserisci il codice del treno", 400
    codTreno = codTreno.strip()
    try:
        codTreno = int(codTreno)
    except ValueError:
        return f"Errore: Il codice '{codTreno}' non è un numero valido.", 400


    trip = trips_eav_collection.find_one({"trip_short_name": codTreno}, {"trip_id": 1, "_id": 0})
    if not trip:
        return f"Errore: Codice treno '{codTreno}' non trovato", 404

    trip_id = trip["trip_id"]

    stop_times_for_trip = list(stop_times_eav_collection.find(
        {"trip_id": trip_id},
        {"stop_id": 1, "arrival_time": 1, "departure_time": 1, "stop_sequence": 1, "_id": 0}
    ).sort("stop_sequence"))

    if not stop_times_for_trip:
        return f"Nessun orario trovato per il treno '{codTreno}'", 404

    stop_ids = [st['stop_id'] for st in stop_times_for_trip]
    stops_data = list(stops_eav_collection.find({"stop_id": {"$in": stop_ids}}, {"stop_id": 1, "stop_name": 1, "_id": 0}))

    stops_map = {stop['stop_id']: stop['stop_name'] for stop in stops_data}

    train_schedule = []
    for st in stop_times_for_trip:
        stop_id = st['stop_id']
        stop_name = stops_map.get(stop_id, "Nome fermata sconosciuto")

        train_schedule.append({
            "nome_fermata": stop_name,
            "orario_arrivo": st.get("arrival_time", "N/A"),
            "orario_partenza": st.get("departure_time", "N/A")
        })

    return render_template("risultatiCodTreno.html", schedule=train_schedule, codTreno=codTreno)


if __name__ == "__main__":
    app.run(debug=True)

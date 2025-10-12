
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from pymongo import MongoClient
from flask import Flask
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

MONGO_URI = "mongodb+srv://Tranzit:fluEqkVVOzm3EGUK@cluster0.7dmohmv.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["Tranzit"]
utenti_collection = db["utenti"]
# Collections relative ai treni e i bus di "Eav"
routes_eav_collection = db["routes_eav"]
trips_eav_collection = db["trips_eav"]
stop_times_eav_collection = db["stop_times_eav"]
stops_eav_collection= db["stops_eav"]
agency_eav_collection = db["agency_eav"]
calendar_dates_eav_collection = db["calendar_dates_eav"]
shapes_eav_collection = db["shapes_eav"]
biglietti_acq_collection = db['biglietti_acquistati']

@app.route("/")
def index():
    today = date.today().strftime("%Y-%m-%d")
    return render_template("index.html", today=today, username=session.get('username'))

@app.route("/chiSiamo")
def chi_siamo():
    return render_template("chiSiamo.html", username=session.get('username'))

@app.route("/accedi")
def accedi():
    if 'username' in session:
        return redirect(url_for('account'))

    return render_template("accedi.html", username=session.get('username'))

@app.route("/account")
def account():
    logged_in_user = utenti_collection.find_one({"username": session['username']})
    return render_template("account.html", user=logged_in_user, username=session.get('username'))

@app.route("/registrati")
def registrati():
    if 'username' in session:
        flash("Sei già connesso. Effettua il logout per creare un nuovo account.", "info")
        return redirect(url_for('account'))
    return render_template("registrati.html", username=session.get('username'))

@app.route("/statusMobilita")
def status_mobilita():
    return render_template("statusMobilita.html", username=session.get('username'))

@app.route("/risultatiCodTreno")
def risultati_cod_treno():
    return render_template("risultatiCodTreno.html", username=session.get('username'))

@app.route("/mieiPagamenti")
def my_payments():
    return render_template("mieiPagamenti.html", username=session.get('username'))

@app.route("/mieiViaggi")
def my_trips():
    if 'username' not in session:
        flash("Devi accedere per visualizzare i tuoi viaggi!", "warning")
        return redirect("/accedi")
    username_corrente = session['username']
    user_biglietti = list(biglietti_acq_collection.find({"username": username_corrente}).sort("data_viaggio", 1))
    return render_template("mieiViaggi.html", biglietti=user_biglietti, username=username_corrente)

def get_stop_id_by_name(stop_name):
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

    today_date_str = date.today().strftime("%Y-%m-%d")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    from_id = get_stop_id_by_name(from_name)
    to_id = get_stop_id_by_name(to_name)
    if not from_id or not to_id:
        return f"Stazione non trovata: {from_name if not from_id else ''} {to_name if not to_id else ''}", 404

    # Trova tutti i trip EAV
    all_trips = list(trips_eav_collection.find({}, {"trip_id": 1, "route_id": 1, "service_id": 1, "trip_short_name": 1, "_id": 0}))

    # Carica tutti gli stop_times EAV
    all_stop_times = list(stop_times_eav_collection.find({}, {"trip_id": 1, "stop_id": 1, "stop_sequence": 1, "departure_time": 1, "_id": 0}))

    all_routes = list(routes_eav_collection.find({}, {"route_id": 1, "agency_id": 1, "_id": 0}))
    routes_map = {route["route_id"]: route for route in all_routes}

    # Organizza stop_times per trip
    stop_times_by_trip = {}
    for st in all_stop_times:
        stop_times_by_trip.setdefault(st["trip_id"], []).append(st)

    results = []

    for trip in all_trips:
        trip_id = trip["trip_id"]
        service_id = trip["service_id"]
        route_id = trip["route_id"]
        times = stop_times_by_trip.get(trip_id, [])
        stops_seq = {st["stop_id"]: st for st in times}

        route_info = routes_map.get(route_id)

        if from_id not in stops_seq or to_id not in stops_seq:
            continue
        if stops_seq[from_id]["stop_sequence"] >= stops_seq[to_id]["stop_sequence"]:
            continue

        # Verifica che il servizio sia attivo per la data richiesta
        is_service_active = False
        exception = calendar_dates_eav_collection.find_one({"service_id": service_id, "date": int(date_gtfs)})
        if exception and exception["exception_type"] == 1:
            is_service_active = True

        agency_long_name = ""
        display_name = ""
        if route_info:
            agency_id = route_info.get("agency_id")
            if agency_id == "NA0004":
                agency_long_name = "TRENO"
                display_name = trip.get("trip_short_name", trip_id)
            elif agency_id == "EAVO":
                agency_long_name = "BUS"
                display_name = trip.get("route_short_name", trip_id)

        if is_service_active:
            from_stop_departure_time = stops_seq[from_id].get("departure_time")
            if trip_date == today_date_str and from_stop_departure_time:
                if from_stop_departure_time < current_time:
                    continue

            results.append({
                "trip_short_name": int(display_name),
                "agency_id": agency_long_name,
                "from_stop": from_name,
                "to_stop": to_name,
                "arrival_time": stops_seq[from_id].get("arrival_time", stops_seq[from_id].get("departure_time", "")),
                "departure_time": stops_seq[to_id]["departure_time"],
                "departure_from_origin_time": from_stop_departure_time
            })

    if results:
        results.sort(key=lambda x: x["departure_from_origin_time"])

    return render_template("treniTrovati.html", tickets=results, from_stop=from_name, to_stop=to_name, date=trip_date, username=session.get('username'))

@app.route("/accedi_utenti", methods=["POST"])
def accedi_utenti():
    username = request.form.get("username").strip()
    password = request.form.get("password").strip()

    if username and password:
        utente_esistente = utenti_collection.find_one({"username": username})

        if utente_esistente and check_password_hash(utente_esistente["password"], password):
            session['username'] = username
            session.permanent = True
            flash(f"Benvenuto, {username}! Accesso effettuato con successo.", "success")
            return redirect(url_for('index'))
        else:
            flash("Username o password non validi.", "danger")
            return redirect("/accedi")
    else:
        flash("Per favore, inserisci username e password", "warning")
        return redirect("/accedi")

@app.route("/add_utenti", methods=["POST"])
def add_utenti():
    username = request.form.get("username").strip()
    password = request.form.get("password").strip()
    email = request.form.get("email").strip()
    if not username or not password or not email:
        flash("Tutti i campi sono obbligatori.", "warning")
        return redirect("/registrati")
    if utenti_collection.find_one({"username": username}):
        flash("Username già esistente. Scegli un altro username.", "danger")
        return redirect("/registrati")
    if utenti_collection.find_one({"email": email}):
        flash("Email già registrata. Usa un'altra email.", "danger")
        return redirect("/registrati")
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    utenti_collection.insert_one({
        "username": username,
        "password": hashed_password,
        "email": email
    })
    flash("Registrazione completata con successo! Ora puoi effettuare l'accesso", "success")
    return redirect("/accedi")

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

    return render_template("risultatiCodTreno.html", schedule=train_schedule, codTreno=codTreno, username=session.get('username'))

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("Logout effettuato con successo.", "info")
    return redirect("/")

@app.route("/api/suggest_stops")
def suggest_stops():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])
    matching_stops = list(stops_eav_collection.find(
        {"stop_name": {"$regex": query, "$options": "i"}},
        {"stop_name": 1, "_id": 0}
    ).limit(10))
    suggestions = [stop["stop_name"] for stop in matching_stops]
    return jsonify(suggestions)

@app.route("/acquista_biglietto", methods=['POST'])
def acquista_biglietto():
    if 'username' not in session:
        flash("Devi accedere per poter acquistare i biglietti!", "danger")
        return redirect("/accedi")
    data = request.form
    trip_short_name = data.get('trip_short_name')
    trip_date = data.get('date')
    agency_id = data.get('agency_id')
    from_stop = data.get('from_stop')
    to_stop = data.get('to_stop')
    arrival_time = data.get('arrival_time')
    departure_time = data.get('departure_time')

    if not all([trip_short_name, trip_date, agency_id, from_stop, to_stop, arrival_time, departure_time]):
        flash(f"Errore: dati incompleti.", "danger")
        return redirect("/")

    nuovo_biglietto = {
        "username": session['username'],
        "codice_treno": trip_short_name,
        "data_viaggio": trip_date,
        "agency_id": agency_id,
        "from_stop": from_stop,
        "to_stop": to_stop,
        "arrival_time": arrival_time,
        "departure_time": departure_time
    }

    try:
        biglietti_acq_collection.insert_one(nuovo_biglietto)
        flash("Biglietto acquistato con successo!", "success")

    except Exception as e:
        flash("Errore durante l'acquisto: {e}", "danger")

    return redirect("/mieiViaggi")

@app.route("/account/update", methods=['POST'])
def modify_info():
    old_username = session.get('username')
    if not old_username:
        flash("Devi accedere per poter modificare le informazioni del tuo profilo!", "danger")
        return redirect("/accedi")

    new_username = request.form.get('username')
    new_email = request.form.get('emailDaMod')
    new_password = request.form.get('password')

    update_fields = {}
    if new_username and new_username.strip():
        new_username_stripped = new_username.strip()
        if new_username_stripped!=old_username and utenti_collection.find_one({"username": new_username_stripped}):
            flash(f"Lo username {new_username_stripped} è già in uso.", "danger")
            return redirect("/account")
        update_fields['username'] = new_username_stripped

        if new_password and new_password.strip():
            hashed_password = generate_password_hash(new_password.strip(), method='pbkdf2:sha256')
            update_fields['password'] = hashed_password

        if new_email and new_email.strip():
            new_email_stripped = new_email.strip()
            existing_email_user = utenti_collection.find_one({"email": new_username_stripped})
            if existing_email_user and existing_email_user['username'] != old_username:
                flash(f"{new_email_stripped} già in uso.", "danger")
                return redirect("/account")
        update_fields['email'] = new_email_stripped

        if update_fields:
            filter_query = {"username": old_username}
            update_operation = {"$set": update_fields}
            result = utenti_collection.update_one(filter_query, update_operation)

            if result.matched_count == 0:
                flash("Errore: impossibile trovare l'utente nel database", "danger")
            elif result.matched_count > 0:
                if 'username' in update_fields:
                    biglietti_acq_collection.update_many(
                        {"username": old_username},
                        {"$set": {"username": new_username}}
                    )
                    session['username'] = update_fields['username']
                    flash("Informazioni aggiornate con successo!", "success")
                else:
                    flash("Nessun cambiamento rilevato", "info")
            else:
                flash("Nessun campo valido fornito per un aggiornamento", "warning")
    return redirect("/account")

if __name__ == "__main__":
    app.run(debug=True)

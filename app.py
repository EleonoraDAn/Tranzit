from flask import (render_template, # funzione per renderizzare le pagine HTML (template)
                   request, # oggetto per accedere ai dati delle richieste web (es. dati dei form)
                   redirect, # funzione per reindirizzare l'utente a un altro URL
                   session, # oggetto per gestire i dati specifici dell'utente tra le richieste (sessioni)
                   flash, # funzione per mostrare messaggi temporanei all'utente
                   jsonify) # funzione per serializzare dati Python in formato JSON, tipicamente per API
from pymongo import MongoClient # driver python per connettersi e interagire con i database MongoDB
from flask import Flask # classe utilizzata per creare l'istanza dell'applicazione web
from datetime import datetime, date # classi per lavorare con date e orari (usate per la formattazione e logica temporale)

from pymongo.errors import PyMongoError
from werkzeug.security import (generate_password_hash, # funzione per creare un hash sicuro della password prima di salvarla nel DB
                               check_password_hash) # funzione per confrontare una password in chiaro con un hash salvato
import os # modulo per interagire con il sistema operativo (utilizzato con la variabile d'ambiente "FLASK_SECRET_KEY")

# creazione dell'istanza dell'applicazione Flask
app = Flask(__name__)

# configurazione della chiave segreta per la gestione delle sessioni e dei messaggi Flash
# Viene usata la variabile d'ambiente 'FLASK_SECRET_KEY'
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# configurazione del database (si usa MongoDB Atlas)
MONGO_URI = "mongodb+srv://Tranzit:fluEqkVVOzm3EGUK@cluster0.7dmohmv.mongodb.net/"
# configurazione per la connessione
client = MongoClient(MONGO_URI)
db = client["Tranzit"] # seleziona il db da utilizzare
utenti_collection = db["utenti"]
# Collections relative ai treni e ai bus di "Eav"
routes_eav_collection = db["routes_eav"]
trips_eav_collection = db["trips_eav"]
stop_times_eav_collection = db["stop_times_eav"]
stops_eav_collection= db["stops_eav"]
agency_eav_collection = db["agency_eav"]
calendar_dates_eav_collection = db["calendar_dates_eav"]
shapes_eav_collection = db["shapes_eav"]
# collection relativa ai biglietti acquistati dall'utente (visibili in "mieiViaggi")
biglietti_acq_collection = db['biglietti_acquistati']

# +++ ROUTE DELL'APPLICAZIONE +++
# 1. Home
@app.route("/")
def index():
    today = date.today().strftime("%Y-%m-%d")
    return render_template("index.html", today=today, username=session.get('username'))

# 2. Chi Siamo
@app.route("/chiSiamo")
def chi_siamo():
    return render_template("chiSiamo.html", username=session.get('username'))

# 3. Accedi
@app.route("/accedi")
def accedi():
    if 'username' in session:
        return redirect("/account")
    return render_template("accedi.html", username=session.get('username'))

# 4. Account
@app.route("/account")
def account():
    logged_in_user = utenti_collection.find_one({"username": session['username']})
    return render_template("account.html", user=logged_in_user, username=session.get('username'))

# 5. Registrati
@app.route("/registrati")
def registrati():
    if 'username' in session:
        flash("Sei già connesso. Effettua il logout per creare un nuovo account.", "info")
        return redirect("/account")
    return render_template("registrati.html", username=session.get('username'))

# 6. Status Mobilità
@app.route("/statusMobilita")
def status_mobilita():
    return render_template("statusMobilita.html", username=session.get('username'))

# 7. Risultati (il titolo della pagina html è il codice del treno inserito dall'utente)
@app.route("/risultatiCodTreno")
def risultati_cod_treno():
    return render_template("risultatiCodTreno.html", username=session.get('username'))

# 8. Miei viaggi
@app.route("/mieiViaggi")
def my_trips():
    if 'username' not in session:
        flash("Devi accedere per visualizzare i tuoi viaggi!", "warning")
        return redirect("/accedi")
    username_corrente = session['username']
    user_biglietti = list(biglietti_acq_collection.find({"username": username_corrente}).sort("data_viaggio", 1))
    return render_template("mieiViaggi.html", biglietti=user_biglietti, username=username_corrente)

# Funzione per restituire il codice delle stazioni ("stop_id" da "stop_name")
def get_stop_id_by_name(stop_name):
    stop_eav = stops_eav_collection.find_one({"stop_name": stop_name})
    if stop_eav:
        return stop_eav["stop_id"]
    return None

# Azione richiamata dal bottone "Cerca" nella "Home"
"""Cercano i biglietti con: 
- data scelta dall'utente;
- stazioni di partenza e di destinazione scelte dall'utente. 
I biglietti risultato hanno un orario di partenza successivo a quello di sistema. I risultati sono ordinati per orario di partenza.
"""
@app.route("/add_prenotazioni", methods=["GET", "POST"])
def add_prenotazioni():
    """
    Logica per la ricerca dei biglietti di treni/bus, utilizzando i dati
    GTFS memorizzati in MongoDB
    """
    # 1. Recupero dei dati in input (dati del form)
    from_name = request.form.get("partenza")
    to_name = request.form.get("destinazione")
    trip_date = request.form.get("dataViaggio")

    # verifica dei dati in input
    if not from_name or not to_name or not trip_date:
        return "Errore: inserisci partenza, destinazione e data", 400

    # conversione della data desiderata dall'utente nel formato GTFS
    try:
        date_obj = datetime.strptime(trip_date, "%Y-%m-%d")
        date_gtfs = date_obj.strftime("%Y%m%d")
    except ValueError:
        return "Formato data non valido", 400

    # dati di tempo attuali per filtrare i viaggi passati in data odierna
    today_date_str = date.today().strftime("%Y-%m-%d")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    # 2. Ottenimento degli "stop_id" delle stazioni di partenza e di destinazione, usando la funzione descritta dalla riga 86 a 90.
    from_id = get_stop_id_by_name(from_name)
    to_id = get_stop_id_by_name(to_name)
    if not from_id or not to_id:
        return f"Stazione non trovata: {from_name if not from_id else ''} {to_name if not to_id else ''}", 404

    # 3. Carica i dati GTFS
    # trova tutti i trip EAV
    all_trips = list(trips_eav_collection.find({}, {"trip_id": 1, "route_id": 1, "service_id": 1, "trip_short_name": 1, "_id": 0}))

    # carica tutti gli stop_times EAV (orari e sequenze delle fermate)
    all_stop_times = list(stop_times_eav_collection.find({}, {"trip_id": 1, "stop_id": 1, "stop_sequence": 1, "departure_time": 1, "_id": 0}))

    # mappa le route per info sull'agenzia (Treno o bus)
    all_routes = list(routes_eav_collection.find({}, {"route_id": 1, "agency_id": 1, "_id": 0}))
    routes_map = {route["route_id"]: route for route in all_routes}

    # organizza stop_times per trip_id per un accesso più rapido
    stop_times_by_trip = {}
    for st in all_stop_times:
        stop_times_by_trip.setdefault(st["trip_id"], []).append(st)

    results = []
    # iterazione sui trip e filtri di logica
    for trip in all_trips:
        trip_id = trip["trip_id"]
        service_id = trip["service_id"]
        route_id = trip["route_id"]
        # recupera gli "stop_times" per il trip corrente
        times = stop_times_by_trip.get(trip_id, [])
        stops_seq = {st["stop_id"]: st for st in times}

        route_info = routes_map.get(route_id)

        # Filtro 1: il trip deve includere sia la stazione di partenza che quella di destinazione
        if from_id not in stops_seq or to_id not in stops_seq:
            continue
        # Filteo 2: la sequenza di partenza deve precedere quella di destinazione
        if stops_seq[from_id]["stop_sequence"] >= stops_seq[to_id]["stop_sequence"]:
            continue

        # 5. Verifica che il servizio sia attivo per la data richiesta
        is_service_active = False
        exception = calendar_dates_eav_collection.find_one({"service_id": service_id, "date": int(date_gtfs)})
        if exception and exception["exception_type"] == 1: # "exception_type" è il campo chiave per capire se il servizio è attivo per una determinata data
            is_service_active = True
        # 6. Determinazione dell'agenzia e del nome da visualizzare nella pagina
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
        # 7. Finalizzazione e filtro orario in data odierna
        if is_service_active:
            from_stop_departure_time = stops_seq[from_id].get("departure_time")
            # se la data è oggi, filtra i viaggi la cui partenza è già avvenuta
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
                "departure_from_origin_time": from_stop_departure_time # per l'ordinamento
            })

    # 8. Ordinamento e rendering
    if results:
        # ordina i risultati per orario di partenza
        results.sort(key=lambda x: x["departure_from_origin_time"])
    # renderizza il template per i risultati trovati
    return render_template("treniTrovati.html", tickets=results, from_stop=from_name, to_stop=to_name, date=trip_date, username=session.get('username'))

# Azione richiamata quando si clicca il bottone "Accedi" nella pagina "Accedi"
@app.route("/accedi_utenti", methods=["POST"])
def accedi_utenti():
    username = request.form.get("username").strip()
    password = request.form.get("password").strip()

    if username and password:
        utente_esistente = utenti_collection.find_one({"username": username})
        # verifica l'esistenza dell'utente e della password (considerando l'hashing)
        if utente_esistente and check_password_hash(utente_esistente["password"], password):
            session['username'] = username
            session.permanent = True
            flash(f"Benvenuto, {username}! Accesso effettuato con successo.", "success")
            return redirect("/")
        else:
            flash("Username o password non validi.", "danger")
            return redirect("/accedi")
    else:
        flash("Per favore, inserisci username e password", "warning")
        return redirect("/accedi")

# Azione richiamata cliccando il bottone "Registrati" della pagina "Registrati"
@app.route("/add_utenti", methods=["POST"])
def add_utenti():
    username = request.form.get("username").strip()
    password = request.form.get("password").strip()
    email = request.form.get("email").strip()
    # validazione dei campi
    if not username or not password or not email:
        flash("Tutti i campi sono obbligatori.", "warning")
        return redirect("/registrati")
    # verifica che l'email e l'username non siano già in uso
    if utenti_collection.find_one({"username": username}):
        flash("Username già esistente. Scegli un altro username.", "danger")
        return redirect("/registrati")
    if utenti_collection.find_one({"email": email}):
        flash("Email già registrata. Usa un'altra email.", "danger")
        return redirect("/registrati")
    # hashing della password prima di salvarla
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    # inserimento del nuovo utente nella collezione chiamata "utenti_collection" del database
    utenti_collection.insert_one({
        "username": username,
        "password": hashed_password,
        "email": email
    })
    flash("Registrazione completata con successo! Ora puoi effettuare l'accesso", "success")
    return redirect("/accedi")

"""
Azione richiamata cliccando il bottone "Controlla" della pagina "Status Mobilità"
E' una route POST che serve per restituire tutte le fermate e gli orari di fermata del tragitto di un treno/bus
"""
@app.route("/getStatusTreno", methods=["POST"])
def get_status_treno():
    cod_treno = request.form.get("codiceTreno")

    # validazione e conversione del codice treno
    if not cod_treno:
        return "Errore: inserisci il codice del treno", 400
    cod_treno = cod_treno.strip()
    try:
        cod_treno = int(cod_treno)
    except ValueError:
        return f"Errore: Il codice '{cod_treno}' non è un numero valido.", 400

# 1. Trova il trip_id basandosi sul trip_short_name (ossia il "cod_treno")
    trip = trips_eav_collection.find_one({"trip_short_name": cod_treno}, {"trip_id": 1, "_id": 0})
    if not trip:
        return f"Errore: Codice treno '{cod_treno}' non trovato", 404

    trip_id = trip["trip_id"]
    # 2. Recupera tutti gli stop_times per quel trip_id, ordinati per sequenza
    stop_times_for_trip = list(stop_times_eav_collection.find(
        {"trip_id": trip_id},
        {"stop_id": 1, "arrival_time": 1, "departure_time": 1, "stop_sequence": 1, "_id": 0}
    ).sort("stop_sequence"))

    if not stop_times_for_trip:
        return f"Nessun orario trovato per il treno '{cod_treno}'", 404

    # 3. Recupera i nomi delle fermate ("stop_name") dai rispettivi "stop_id"
    stop_ids = [st['stop_id'] for st in stop_times_for_trip]
    stops_data = list(stops_eav_collection.find({"stop_id": {"$in": stop_ids}}, {"stop_id": 1, "stop_name": 1, "_id": 0}))

    stops_map = {stop['stop_id']: stop['stop_name'] for stop in stops_data}

    # 4. Costruisce la tabella degli orari
    train_schedule = []
    for st in stop_times_for_trip:
        stop_id = st['stop_id']
        stop_name = stops_map.get(stop_id, "Nome fermata sconosciuto")

        train_schedule.append({
            "nome_fermata": stop_name,
            "orario_arrivo": st.get("arrival_time", "N/A"),
            "orario_partenza": st.get("departure_time", "N/A")
        })

    # renderizza la pagina dei risultati
    return render_template("risultatiCodTreno.html", schedule=train_schedule, codTreno=cod_treno, username=session.get('username'))

# Azione richiamata quando si clicca "Logout" nella sidebar della pagina "Account"
@app.route("/logout")
def logout():
    session.pop('username', None) # rimuove lo username dalla sessione
    flash("Logout effettuato con successo.", "info")
    return redirect("/")

""" 
Endpoint API per i suggerimenti di autocompletamento delle fermate.
Viene usata per la lista di stazioni di partenza e di destinazione che compare quando scriviamo nel form della pagina "Home"
"""
@app.route("/api/suggest_stops")
def suggest_stops():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])
    # cerca nel database fermate il cui nome corrisponde parzialmente alla query (case-insensitive regex)
    matching_stops = list(stops_eav_collection.find(
        {"stop_name": {"$regex": query, "$options": "i"}},
        {"stop_name": 1, "_id": 0}
    ).limit(10)) # limite: 10 suggerimenti
    suggestions = [stop["stop_name"] for stop in matching_stops]
    return jsonify(suggestions)

# Azione richiamata dal form della pagina "treniTrovati"
@app.route("/acquista_biglietto", methods=['POST'])
def acquista_biglietto():
    # richiede l'accesso
    if 'username' not in session:
        flash("Devi accedere per poter acquistare i biglietti!", "danger")
        return redirect("/accedi")
    # recupera i dati dal form
    data = request.form
    trip_short_name = data.get('trip_short_name')
    trip_date = data.get('date')
    agency_id = data.get('agency_id')
    from_stop = data.get('from_stop')
    to_stop = data.get('to_stop')
    arrival_time = data.get('arrival_time')
    departure_time = data.get('departure_time')
    # validazione dei dati
    if not all([trip_short_name, trip_date, agency_id, from_stop, to_stop, arrival_time, departure_time]):
        flash(f"Errore: dati incompleti.", "danger")
        return redirect("/")

    # oggetto da salvare (ovvero il biglietto acquistato)
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
    # inserimento del biglietto nel database, nello specifico nella collezione "biglietti_acq_collection"
    try:
        biglietti_acq_collection.insert_one(nuovo_biglietto)
        flash("Biglietto acquistato con successo!", "success")

    except PyMongoError as e:
        flash(f"Errore durante l'acquisto: {e}", "danger")

    # reindirizza alla pagina "mieiViaggi", dove si troveranno tutti i biglietti acquistati
    return redirect("/mieiViaggi")

# Azione richiamata cliccando il bottone "Salva" della pagina "Account" per modificare le informazioni dell'account dell'utente
@app.route("/account/update", methods=['POST'])
def modify_info():
    old_username = session.get('username')
    if not old_username:
        flash("Devi accedere per poter modificare le informazioni del tuo profilo!", "danger")
        return redirect("/accedi")

# recupera i nuovi dati dell'utente dal form presente nella pagina
    new_username = request.form.get('username')
    new_email = request.form.get('emailDaMod')
    new_password = request.form.get('password')

    update_fields = {}

    # 1. Gestione dell'username
    if new_username and new_username.strip():
        new_username_stripped = new_username.strip()
        # verifica se il nuovo username è diverso da quello attuale e se è già in uso
        if new_username_stripped!=old_username and utenti_collection.find_one({"username": new_username_stripped}):
            flash(f"Lo username {new_username_stripped} è già in uso.", "danger")
            return redirect("/account")
        update_fields['username'] = new_username_stripped

        # 2. Gestione password
        if new_password and new_password.strip():
            hashed_password = generate_password_hash(new_password.strip(), method='pbkdf2:sha256') # esegue l'hashing della nuova password
            update_fields['password'] = hashed_password

        # 3. Gestione email
        if new_email and new_email.strip():
            new_email_stripped = new_email.strip()
            existing_email_user = utenti_collection.find_one({"email": new_username_stripped})
            # verifica se la nuova email è già in uso da un altro utente
            if existing_email_user and existing_email_user['username'] != old_username:
                flash(f"{new_email_stripped} già in uso.", "danger")
                return redirect("/account")
            update_fields['email'] = new_email_stripped

        # esegue l'aggiornamento SOLO se ci sono campi da modificare
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
                    session['username'] = update_fields['username'] # aggiorna la sessione
                    flash("Informazioni aggiornate con successo!", "success")
                else:
                    flash("Nessun cambiamento rilevato", "info")
            else:
                flash("Nessun campo valido fornito per un aggiornamento", "warning")
    return redirect("/account")

# Avvia il server "Flask" in modalità debug
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import subprocess
from collections import defaultdict
import random
from random import randint

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///turns.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Admin password (simple, static password for demonstration)
ADMIN_PASSWORD = 'pass'

# Initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

artist_houses = ['Soresi', 'Laramack', 'Isleif']

class GlobalResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    house = db.Column(db.String(80), nullable=False, unique=True)
    splendor = db.Column(db.Float, nullable=False)
    ap = db.Column(db.Float, nullable=False)
    wealth = db.Column(db.Float, nullable=False)
    culture = db.Column(db.Float, nullable=False)

class GlobalTurn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turn_number = db.Column(db.Integer, nullable=False, default=18)  # Initialize global turn to 18

def populate_global_resources():
    if GlobalResource.query.count() == 0:
        initial_resources = [
            {"House": "Laramack", "Spl": 320.5, "AP": 22, "Wealth": 0, "Culture": 11},
            {"House": "Lo", "Spl": 241.75, "AP": 24, "Wealth": 10.75, "Culture": 0},
            {"House": "Glamides", "Spl": 189.75, "AP": 25, "Wealth": 11, "Culture": 2},
            {"House": "Cenica", "Spl": 88, "AP": 21, "Wealth": 9.5, "Culture": 0},
            {"House": "Chimmeria", "Spl": 101.75, "AP": 24, "Wealth": 3.5, "Culture": 0},
            {"House": "Lowell", "Spl": 68.5, "AP": 25, "Wealth": 9.25, "Culture": 11},
            {"House": "Masseney", "Spl": 76, "AP": 25, "Wealth": 58, "Culture": 1},
            {"House": "Soresi", "Spl": 75.25, "AP": 24, "Wealth": 10, "Culture": 2},
            {"House": "Mirtilli", "Spl": 65.75, "AP": 19, "Wealth": 13, "Culture": 1},
            {"House": "Zinkowski", "Spl": 77.5, "AP": 22.75, "Wealth": 0, "Culture": 11},
            {"House": "Swietstead", "Spl": 99.25, "AP": 24, "Wealth": 12, "Culture": 7},
            {"House": "Raimesi", "Spl": 41.25, "AP": 26, "Wealth": 4, "Culture": 2},
            {"House": "Borophaginae", "Spl": 57, "AP": 24, "Wealth": 10.75, "Culture": 2},
            {"House": "Isleif", "Spl": 44, "AP": 22, "Wealth": 66, "Culture": 11},
            {"House": "Cadres of Charme", "Spl": 31, "AP": 20.5, "Wealth": 0, "Culture": 12},
            {"House": "Kruul", "Spl": 35.75, "AP": 22.25, "Wealth": 8, "Culture": 11},
            {"House": "Doquz", "Spl": 10, "AP": 24, "Wealth": 27, "Culture": 0},
            {"House": "Vopox", "Spl": 31, "AP": 19, "Wealth": 25, "Culture": 51}
        ]
        for resource in initial_resources:
            new_resource = GlobalResource(
                house=resource['House'],
                splendor=resource['Spl'],
                ap=resource['AP'],
                wealth=resource['Wealth'],
                culture=resource['Culture']
            )
            db.session.add(new_resource)
        db.session.commit()

# Define Turn model
class Turn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turn_number = db.Column(db.Integer, nullable=False)
    house = db.Column(db.String(80), nullable=False)
    splendor = db.Column(db.Float, nullable=False)
    ap = db.Column(db.Float, nullable=False)
    wealth = db.Column(db.Float, nullable=False)
    culture = db.Column(db.Float, nullable=False)
    actions = db.Column(db.Text, nullable=False)
    artist_bids = db.Column(db.Text, nullable=False)
    income = db.Column(db.Text, nullable=False)
    splendor_sources = db.Column(db.Text, nullable=False)
    bonus_spl = db.Column(db.Float, nullable=False)
    bonus_ap = db.Column(db.Float, nullable=False)
    bonus_wealth = db.Column(db.Float, nullable=False)
    bonus_culture = db.Column(db.Float, nullable=False)
    final_spl = db.Column(db.Float)
    final_ap = db.Column(db.Float)
    final_wealth = db.Column(db.Float)
    final_culture = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False, default='submitted')  # 'submitted' or 'released'
    lore = db.Column(db.Text, nullable=True)  # Add this line for lore


# Route to view global resources (public for all users)
@app.route('/')
def index():
    global_turn = GlobalTurn.query.first()
    if global_turn is None:
        global_turn_number = 18  # Default if no global turn is found
    else:
        global_turn_number = global_turn.turn_number
    global_resources = GlobalResource.query.all()
    return render_template('index.html', global_resources=global_resources, global_turn=global_turn_number)

# Route for submitting a turn (public for all users)
@app.route('/submit_turn', methods=['GET', 'POST'])
def submit_turn():
    # Get the current global turn number
    global_turn = GlobalTurn.query.first().turn_number

    if request.method == 'POST':
        house = request.form['house']
        splendor = float(request.form['splendor'])
        ap = float(request.form['ap'])
        wealth = float(request.form['wealth'])
        culture = float(request.form['culture'])
        lore = request.form.get('lore')  # Retrieve lore from form

        # Collect and process the multiple rows of data for actions
        total_ap_spent = 0
        total_wealth_spent = 0
        total_culture_spent = 0
        actions = []
        for action, ap_cost, wealth_cost, culture_cost, notes in zip(
                request.form.getlist('actions_action[]'),
                request.form.getlist('actions_ap_cost[]'),
                request.form.getlist('actions_wealth_cost[]'),
                request.form.getlist('actions_culture_cost[]'),
                request.form.getlist('actions_notes[]')):
            actions.append(f"{action}\t{ap_cost}\t{wealth_cost}\t{culture_cost}\t{notes}")
            total_ap_spent += float(ap_cost)
            total_wealth_spent += float(wealth_cost)
            total_culture_spent += float(culture_cost)
        actions_text = "\n".join(actions)

        # Initialize the artist_bids list
        artist_bids = []
        for target, ap_bid, wealth_bid, recipient, notes in zip(
                request.form.getlist('artist_bids_target[]'),
                request.form.getlist('artist_bids_ap_bid[]'),
                request.form.getlist('artist_bids_wealth_bid[]'),
                request.form.getlist('artist_bids_recipient[]'),
                request.form.getlist('artist_bids_notes[]')):
            artist_bids.append(f"{target}\t{ap_bid}\t{wealth_bid}\t{recipient}\t\t{notes}")
            total_ap_spent += float(ap_bid)
            total_wealth_spent += float(wealth_bid)
        artist_bids_text = "\n".join(artist_bids)

        # Process income
        total_income_ap = 0
        total_income_wealth = 0
        income = []
        for source, income_wealth, income_ap, notes in zip(
                request.form.getlist('income_source[]'),
                request.form.getlist('income_wealth[]'),
                request.form.getlist('income_ap[]'),
                request.form.getlist('income_notes[]')):
            income.append(f"{source}\t{income_wealth}\t{income_ap}\t{notes}")
            total_income_wealth += float(income_wealth)
            total_income_ap += float(income_ap)
        income_text = "\n".join(income)

        # Process splendor sources
        total_dynastic_spl = 0
        splendor_sources = []
        for source, dynastic, civic, client, tithed, notes in zip(
                request.form.getlist('splendor_sources_source[]'),
                request.form.getlist('splendor_sources_dynastic[]'),
                request.form.getlist('splendor_sources_civic[]'),
                request.form.getlist('splendor_sources_client[]'),
                request.form.getlist('splendor_sources_tithed[]'),
                request.form.getlist('splendor_sources_notes[]')):
            splendor_sources.append(f"{source}\t{dynastic}\t{civic}\t{client}\t{tithed}\t{notes}")
            total_dynastic_spl += float(dynastic)
        splendor_sources_text = "\n".join(splendor_sources)

        # Safely get the bonus resources from the form, using 0 if fields are empty
        bonus_spl = float(request.form['bonus_spl']) if request.form['bonus_spl'] else 0
        bonus_ap = float(request.form['bonus_ap']) if request.form['bonus_ap'] else 0
        bonus_wealth = float(request.form['bonus_wealth']) if request.form['bonus_wealth'] else 0
        bonus_culture = float(request.form['bonus_culture']) if request.form['bonus_culture'] else 0


        # Final resource calculation (including bonuses)
        final_ap = ap - total_ap_spent + total_income_ap + bonus_ap
        final_wealth = wealth - total_wealth_spent + total_income_wealth + bonus_wealth
        final_culture = culture - total_culture_spent + bonus_culture
        final_splendor = splendor + total_dynastic_spl + bonus_spl

        # Create new Turn object with turn_number
        new_turn = Turn(
            house=house,
            splendor=splendor,
            ap=ap,
            wealth=wealth,
            culture=culture,
            actions=actions_text,
            artist_bids=artist_bids_text,
            income=income_text,
            splendor_sources=splendor_sources_text,
            bonus_spl=bonus_spl,
            bonus_ap=bonus_ap,
            bonus_wealth=bonus_wealth,
            bonus_culture=bonus_culture,
            final_spl=final_splendor,
            final_ap=final_ap,
            final_wealth=final_wealth,
            final_culture=final_culture,
            lore=lore,
            turn_number=global_turn  # Associate with current global turn number
        )

        # Save the data into the database
        db.session.add(new_turn)
        db.session.commit()

        return redirect(url_for('view_turns'))

    # Query all houses from GlobalResource to populate the dropdown
    houses = GlobalResource.query.all()

    artists_by_city = defaultdict(list)
    available_artists = Artist.query.all()

    for artist in available_artists:
        artists_by_city[artist.city].append(artist)

    return render_template('submit_turn.html', artists_by_city=artists_by_city, houses=houses, global_turn=global_turn)
#    return render_template('submit_turn.html', available_artists=available_artists, houses=houses, global_turn=global_turn)


# Route for users to view released turns only (public)
@app.route('/view_turns')
def view_turns():
    turns = Turn.query.filter_by(status='released').all()
    artists_by_turn = defaultdict(dict)
    
    # Fetch all artists and group them by turn
    artists = Artist.query.all()
    for artist in artists:
        # Associate each artist with their specific turn number
        artists_by_turn[artist.turn_number][artist.name] = artist.cp

    return render_template('view_turns.html', turns=turns, artists_by_turn=artists_by_turn)


# Admin login
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return "Incorrect password", 403
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    # Query all turns
    turns = Turn.query.all()

    # Get the current global turn number
    global_turn = GlobalTurn.query.first().turn_number

    # Create a dictionary to hold artists associated with each turn number
    artists_by_turn = {}

    # For each turn, find the artists associated with that turn's turn_number
    for turn in turns:
        # Fetch artists based on the specific turn_number
        artists = Artist.query.filter_by(turn_number=turn.turn_number).all()
        # Store the artist name and CP in the dictionary for the specific turn_number
        artists_by_turn[turn.turn_number] = {artist.name: artist.cp for artist in artists}

    return render_template(
        'admin_dashboard.html', 
        turns=turns, 
        global_turn=global_turn, 
        artists_by_turn=artists_by_turn
    )


# Route for viewing the Artist Auction (public for all users)
@app.route('/artist_auction')
def artist_auction():
    # Retrieve the current global turn
    global_turn = GlobalTurn.query.first().turn_number

    # Query only the artists for the current global turn
    artists = Artist.query.filter_by(turn_number=global_turn).all()

    # Group artists by city
    artists_by_city = {}
    for artist in artists:
        if artist.city not in artists_by_city:
            artists_by_city[artist.city] = []
        artists_by_city[artist.city].append(artist)

    return render_template('artist_auction.html', artists_by_city=artists_by_city, global_turn=global_turn)


# Route to release a turn (only for admin)
@app.route('/admin/release_turn/<int:turn_id>', methods=['POST'])
def release_turn(turn_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    turn = Turn.query.get(turn_id)
    if turn and turn.status == 'submitted':
        turn.status = 'released'
        
        # Lock the turn_number to the current global turn
        global_turn = GlobalTurn.query.first().turn_number
        turn.turn_number = global_turn  # Lock turn_number at the moment of release

        # Update the GlobalResource for this house
        resource = GlobalResource.query.filter_by(house=turn.house).first()
        if resource:
            resource.splendor = turn.final_spl
            resource.ap = turn.final_ap
            resource.wealth = turn.final_wealth
            resource.culture = turn.final_culture
            db.session.commit()

    return redirect(url_for('admin_dashboard'))

# Route to logout the admin
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# Route for managing artists (admin only)
@app.route('/admin/manage_artists', methods=['GET', 'POST'])
def manage_artists():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    # Get the current global turn number
    global_turn = GlobalTurn.query.first().turn_number
    
    # Handle form submission to add new artists
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        cp = int(request.form['cp'])
        description = request.form['description']
        special_ability = request.form.get('special_ability')

        # Add the new artist to the database, associating with the current turn
        new_artist = Artist(
            name=name, 
            city=city, 
            cp=cp, 
            description=description, 
            special_ability=special_ability,
            turn_number=global_turn  # Associate new artist with the current turn
        )
        db.session.add(new_artist)
        db.session.commit()
        return redirect(url_for('manage_artists'))
    
    # Only display artists for the current turn
    artists = Artist.query.filter_by(turn_number=global_turn).all()
    
    # Group artists by city
    artists_by_city = {}
    for artist in artists:
        if artist.city not in artists_by_city:
            artists_by_city[artist.city] = []
        artists_by_city[artist.city].append(artist)

    return render_template('manage_artists.html', artists_by_city=artists_by_city, global_turn=global_turn)


# Route for editing an artist (admin only)
@app.route('/admin/edit_artist/<int:artist_id>', methods=['POST'])
def edit_artist(artist_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    # Fetch the artist by ID
    artist = Artist.query.get(artist_id)

    if artist:
        # Update the artist fields from the form
        artist.name = request.form['name']
        artist.cp = request.form['cp']
        artist.description = request.form['description']
        artist.special_ability = request.form.get('special_ability', '')

        # Commit the changes to the database
        db.session.commit()

    return redirect(url_for('manage_artists'))


class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    cp = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    special_ability = db.Column(db.String(255), nullable=True)
    turn_number = db.Column(db.Integer, nullable=False)  # Add this line



# Route to edit a specific turn (only for admin)
@app.route('/admin/edit_turn/<int:turn_id>', methods=['GET', 'POST'])
def edit_turn(turn_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    turn = Turn.query.get(turn_id)
    houses = GlobalResource.query.all()

    if request.method == 'POST':
        # Update turn fields from the form
        turn.house = request.form['house']
        turn.splendor = float(request.form['splendor']) if request.form['splendor'] else 0
        turn.ap = float(request.form['ap']) if request.form['ap'] else 0
        turn.wealth = float(request.form['wealth']) if request.form['wealth'] else 0
        turn.culture = float(request.form['culture']) if request.form['culture'] else 0
        turn.bonus_spl = float(request.form['bonus_spl']) if request.form['bonus_spl'] else 0
        turn.bonus_ap = float(request.form['bonus_ap']) if request.form['bonus_ap'] else 0
        turn.bonus_wealth = float(request.form['bonus_wealth']) if request.form['bonus_wealth'] else 0
        turn.bonus_culture = float(request.form['bonus_culture']) if request.form['bonus_culture'] else 0
        turn.lore = request.form['lore']  # Add lore to be updated

        # Rebuild actions, artist bids, income, and splendor sources
        actions = []
        for i in range(len(request.form.getlist('actions_action[]'))):
            action = request.form.getlist('actions_action[]')[i]
            ap_cost = request.form.getlist('actions_ap_cost[]')[i]
            wealth_cost = request.form.getlist('actions_wealth_cost[]')[i]
            culture_cost = request.form.getlist('actions_culture_cost[]')[i]
            notes = request.form.getlist('actions_notes[]')[i]
            actions.append(f"{action}\t{ap_cost}\t{wealth_cost}\t{culture_cost}\t{notes}")
        turn.actions = '\n'.join(actions)

        artist_bids = []
        for i in range(len(request.form.getlist('artist_bids_target[]'))):
            target = request.form.getlist('artist_bids_target[]')[i]
            ap_bid = request.form.getlist('artist_bids_ap_bid[]')[i]
            wealth_bid = request.form.getlist('artist_bids_wealth_bid[]')[i]
            recipient = request.form.getlist('artist_bids_recipient[]')[i]
            outcome = request.form.getlist('artist_bids_outcome[]')[i]
            notes = request.form.getlist('artist_bids_notes[]')[i]
            artist_bids.append(f"{target}\t{ap_bid}\t{wealth_bid}\t{recipient}\t{outcome}\t{notes}")
        turn.artist_bids = '\n'.join(artist_bids)

        income = []
        for i in range(len(request.form.getlist('income_source[]'))):
            source = request.form.getlist('income_source[]')[i]
            wealth = request.form.getlist('income_wealth[]')[i]
            ap = request.form.getlist('income_ap[]')[i]
            notes = request.form.getlist('income_notes[]')[i]
            income.append(f"{source}\t{wealth}\t{ap}\t{notes}")
        turn.income = '\n'.join(income)

        splendor_sources = []
        for i in range(len(request.form.getlist('splendor_sources_source[]'))):
            source = request.form.getlist('splendor_sources_source[]')[i]
            dynastic = request.form.getlist('splendor_sources_dynastic[]')[i]
            civic = request.form.getlist('splendor_sources_civic[]')[i]
            client = request.form.getlist('splendor_sources_client[]')[i]
            tithed = request.form.getlist('splendor_sources_tithed[]')[i]
            notes = request.form.getlist('splendor_sources_notes[]')[i]
            splendor_sources.append(f"{source}\t{dynastic}\t{civic}\t{client}\t{tithed}\t{notes}")
        turn.splendor_sources = '\n'.join(splendor_sources)

        # Recalculate final resources
        def safe_float(value):
            try:
                return float(value)
            except ValueError:
                return 0

        total_ap_spent = sum(safe_float(line.split('\t')[1]) for line in turn.actions.split('\n') if line and len(line.split('\t')) > 1)
        total_wealth_spent = sum(safe_float(line.split('\t')[2]) for line in turn.actions.split('\n') if line and len(line.split('\t')) > 2)
        total_culture_spent = sum(safe_float(line.split('\t')[3]) for line in turn.actions.split('\n') if line and len(line.split('\t')) > 3)

        total_ap_bid = sum(safe_float(line.split('\t')[1]) for line in turn.artist_bids.split('\n') if line and len(line.split('\t')) > 1)
        total_wealth_bid = sum(safe_float(line.split('\t')[2]) for line in turn.artist_bids.split('\n') if line and len(line.split('\t')) > 2)

        total_ap_income = sum(safe_float(line.split('\t')[2]) for line in turn.income.split('\n') if line and len(line.split('\t')) > 2)
        total_wealth_income = sum(safe_float(line.split('\t')[1]) for line in turn.income.split('\n') if line and len(line.split('\t')) > 1)

        total_dynastic_splendor = sum(safe_float(line.split('\t')[1]) for line in turn.splendor_sources.split('\n') if line and len(line.split('\t')) > 1)

        turn.final_ap = turn.ap - total_ap_spent - total_ap_bid + total_ap_income + turn.bonus_ap
        turn.final_wealth = turn.wealth - total_wealth_spent - total_wealth_bid + total_wealth_income + turn.bonus_wealth
        turn.final_culture = turn.culture - total_culture_spent + turn.bonus_culture
        turn.final_spl = turn.splendor + total_dynastic_splendor + turn.bonus_spl

        # Save the changes
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    artists_by_city = defaultdict(list)
    available_artists = Artist.query.all()

    for artist in available_artists:
        artists_by_city[artist.city].append(artist)


    return render_template('edit_turn.html', artists_by_city=artists_by_city, turn=turn,houses=houses)


@app.route('/view_house_turns/<house>')
def view_house_turns(house):
    # Query the database for released turns by the selected house
    turns = Turn.query.filter_by(house=house, status='released').all()

    # Render the house-specific turns using a custom HTML template
    return render_template('view_house_turns.html', turns=turns, house=house)

# Route to hide (unrelease) a turn (only for admin)
@app.route('/admin/hide_turn/<int:turn_id>', methods=['POST'])
def hide_turn(turn_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    turn = Turn.query.get(turn_id)
    if turn and turn.status == 'released':
        turn.status = 'submitted'
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/set_turn', methods=['GET', 'POST'])
def set_turn():
    if request.method == 'POST':
        new_turn = int(request.form['turn_number'])
        global_turn = GlobalTurn.query.first()
        global_turn.turn_number = new_turn
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    global_turn = GlobalTurn.query.first().turn_number
    return render_template('set_turn.html', global_turn=global_turn)

@app.route('/admin/edit_turn_number/<int:turn_id>', methods=['POST'])
def edit_turn_number(turn_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    new_turn_number = request.form['turn_number']
    turn = Turn.query.get(turn_id)
    if turn:
        turn.turn_number = new_turn_number
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

# Route to update the global turn number
@app.route('/update_global_turn', methods=['POST'])
def update_global_turn():
    global_turn = request.form['global_turn']

    # Update the global turn number in the database
    current_turn = GlobalTurn.query.first()
    if current_turn:
        current_turn.turn_number = global_turn
    else:
        new_turn = GlobalTurn(turn_number=global_turn)
        db.session.add(new_turn)

    db.session.commit()

    return redirect(url_for('admin_dashboard'))


@app.before_request
def initialize_global_turn():
    # Check if global turn is already initialized
    global_turn = GlobalTurn.query.first()
    if global_turn is None:
        new_global_turn = GlobalTurn(turn_number=18)
        db.session.add(new_global_turn)
        db.session.commit()

# Route to delete a turn (only for admin)
@app.route('/admin/delete_turn/<int:turn_id>', methods=['POST'])
def delete_turn(turn_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    turn = Turn.query.get(turn_id)
    if turn:
        db.session.delete(turn)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))


# Function to initialize the artists in the database and associate them with Turn 18
def initialize_artists():
    initial_artists = [
        {"name": "Aqueduct", "city": "Corpolla", "cp": 3, "description": "", "special_ability": "Instead of gaining culture, place a farm on a hill or mountain tile and start with 6 less AP next turn"},
        {"name": "Vulgar, Vulgar Art", "city": "Corpolla", "cp": 4, "description": "", "special_ability": ""},
        {"name": "Fig Leaf Vandal", "city": "Corpolla", "cp": 4, "description": "", "special_ability": ""},

        {"name": "Nova Paganism", "city": "Marafel", "cp": 1, "description": "", "special_ability": "When mustering troops, choose for them to count as Harmonious, Glorious, or Balanced strength."},
        {"name": "Neopaganism", "city": "Marafel", "cp": 3, "description": "", "special_ability": ""},
        {"name": "Self Knowledge", "city": "Marafel", "cp": 3, "description": "", "special_ability": "Instead of gaining culture, know the turn that a doomed character will die."},

        {"name": "Lagoon Platform", "city": "Fairend", "cp": 3, "description": "", "special_ability": ""},
        {"name": "Reflection", "city": "Fairend", "cp": 3, "description": "", "special_ability": "Instead of gaining culture, know the turn that a doomed character will die."},

        {"name": "Quoins", "city": "Garub", "cp": 3, "description": "", "special_ability": ""},
        {"name": "Gemstone Cameo", "city": "Garub", "cp": 3, "description": "", "special_ability": ""},
        {"name": "Imitation of the Martyrs", "city": "Garub", "cp": 3, "description": "", "special_ability": ""},

        {"name": "Lagoon Concerto", "city": "Laramack", "cp": 1, "description": "", "special_ability": ""},
        {"name": "Victory Anthem", "city": "Laramack", "cp": 4, "description": "", "special_ability": ""},

        {"name": "Pandemonium", "city": "Hlerheim", "cp": 1, "description": "", "special_ability": "Reduce riot chance, by example."},
        {"name": "Just a Cough", "city": "Hlerheim", "cp": 1, "description": "", "special_ability": "Instead of gaining culture, know the turn that a doomed character will die."},
        {"name": "Mural of Familiar Faces", "city": "Hlerheim", "cp": 6, "description": "", "special_ability": ""},
        {"name": "Artistic Innovation", "city": "Hlerheim", "cp": 7, "description": "", "special_ability": ""},

        {"name": "Lagoon Platform", "city": "Sabor", "cp": 1, "description": "", "special_ability": ""},

        {"name": "Know Thyself", "city": "Rookery", "cp": 5, "description": "", "special_ability": ""},
        {"name": "Mirror of Princes", "city": "Rookery", "cp": 1, "description": "", "special_ability": "Ask Sam one question about the hidden rules and get an honest answer"},

        {"name": "Patron Saint", "city": "Neckenden", "cp": 5, "description": "", "special_ability": ""},

        {"name": "Royal Subtext", "city": "Varheld", "cp": 2, "description": "", "special_ability": "On your next turn you may issue an edict for free"}
    ]

    # Add each artist to the database and associate them with Turn 18
    for artist_data in initial_artists:
        artist = Artist(
            name=artist_data['name'],
            city=artist_data['city'],
            cp=artist_data['cp'],
            description=artist_data['description'],
            special_ability=artist_data['special_ability'],
            turn_number=18  # Associate the artist with Turn 18
        )
        db.session.add(artist)

    # Commit the changes to save the artists
    db.session.commit()

    return "Artists for Turn 18 have been initialized!"

@app.route('/run_artist_auction', methods=['POST'])
def run_artist_auction():
    # Get the current global turn number
    global_turn = GlobalTurn.query.first().turn_number
    next_turn_number = global_turn + 1  # Prepare for the next turn

    # Dictionary to store bids per artist
    artist_bids = defaultdict(list)

    # Fetch all submitted turns for the current global turn
    turns = Turn.query.filter_by(turn_number=global_turn).all()

    # Fetch all artists for the current turn
    current_turn_artists = Artist.query.filter_by(turn_number=global_turn).all()
    artist_dict = {artist.name: artist for artist in current_turn_artists}

    auction_results = []

    # Process each turn and extract artist bids
    for turn in turns:
        for bid in turn.artist_bids.split('\n'):
            if bid.strip():
                bid_values = bid.split('\t')
                artist_name = bid_values[0]
                ap_bid = float(bid_values[1])
                wealth_bid = float(bid_values[2])
                recipient = bid_values[3]
                notes = bid_values[5]

                # Calculate total bid value before applying any modifiers
                bid_value = ap_bid + wealth_bid

                # Store the bid for the artist (without modification for the comparison)
                artist_bids[artist_name].append({
                    'house': turn.house,
                    'recipient': recipient,
                    'bid_value': bid_value,
                    'ap_bid': ap_bid,
                    'wealth_bid': wealth_bid,
                    'notes': notes,
                    'turn': turn,
                    'original_bid': bid  # Store original bid string to update later
                })

    # Track artists who have received bids
    artists_with_bids = set(artist_bids.keys())

    # Process each artist and determine the highest bid
    for artist_name, bids in artist_bids.items():
        # Apply the modifier for houses with the artist trait when determining the winner
        def adjusted_bid_value(bid):
            if bid['house'] in ['Soresi', 'Laramack', 'Isleif']:
                return bid['bid_value'] * 1.5  # Apply the 50% modifier
            return bid['bid_value']

        # Determine the highest bid using the adjusted bid value
        winning_bid = max(bids, key=lambda x: adjusted_bid_value(x))
        winning_turn = winning_bid['turn']
        winner_house = winning_bid['house']
        recipient_house = winning_bid['recipient']

        # Process each bid and mark "Won" or "Outbid"
        for bid in bids:
            if bid == winning_bid:
                bid['outcome'] = 'Won'
            else:
                bid['outcome'] = 'Outbid'
                # Reverse the AP and wealth spent for outbid bids
                bid['turn'].final_ap += bid['ap_bid']
                bid['turn'].final_wealth += bid['wealth_bid']

        # Update the artist bids for each turn (set "Won" or "Outbid")
        for turn in turns:
            updated_artist_bids = []
            for bid in bids:
                if bid['turn'] == turn:
                    updated_artist_bid = f"{artist_name}\t{bid['ap_bid']}\t{bid['wealth_bid']}\t{bid['recipient']}\t{bid['outcome']}\t{bid['notes']}"
                    updated_artist_bids.append(updated_artist_bid)

            # If the turn has artist bids, update it
            if updated_artist_bids:
                turn.artist_bids = "\n".join(updated_artist_bids)

        # Update the artist based on the d4 roll
        artist_outcome = "Returned to Academy"  # Default
        d4_roll = randint(1, 4)

        # Apply house modifier for rolling
        if winner_house in ['Soresi', 'Laramack', 'Isleif']:
            if d4_roll == 1:
                artist_outcome = "Expended"
        else:
            if d4_roll in [1, 2]:
                artist_outcome = "Expended"

        # Update the artist in the database based on the roll
        artist = artist_dict[artist_name]

        if artist_outcome == "Expended":
            # Do not remove the artist from the database, but do not carry it over to the next turn
            pass
        else:
            # Clone the artist for the next turn, increment CP if returned to the academy
            new_artist = Artist(
                name=artist.name,
                city=artist.city,
                cp=artist.cp + 1,  # Increase CP if returned to the academy
                description=artist.description,
                special_ability=None,  # Remove special ability
                turn_number=next_turn_number  # Associate with the next turn
            )
            db.session.add(new_artist)

        # Add the culture points of the artist to the recipient's bonus culture
        recipient_turn = Turn.query.filter_by(house=recipient_house, turn_number=global_turn).first()
        if recipient_turn:
            recipient_turn.bonus_culture += artist.cp  # Add the artist CP to bonus culture
            # Recalculate the final culture after adding the bonus culture
            recipient_turn.final_culture = recipient_turn.culture + recipient_turn.bonus_culture

        # Create an entry for the auction results
        auction_results.append({
            'artist': artist_name,
            'winner': winner_house,
            'recipient': recipient_house,
            'outcome': winning_bid['outcome'],
            'status': artist_outcome,
            'd4_roll': d4_roll  # Include the roll for display purposes
        })

    # Add artists who received no bids to the next turn's artist list
    for artist in current_turn_artists:
        if artist.name not in artists_with_bids:
            # Clone the artist for the next turn with the same CP and special ability
            new_artist = Artist(
                name=artist.name,
                city=artist.city,
                cp=artist.cp,  # Carry over the same CP
                description=artist.description,
                special_ability=artist.special_ability,  # Carry over the special ability
                turn_number=next_turn_number  # Associate with the next turn
            )
            db.session.add(new_artist)

    # Commit all changes to the database
    db.session.commit()

    # Render the auction summary page with results
    return render_template('auction_summary.html', auction_results=auction_results)


# Function to check if the artist table is empty and initialize if necessary
def check_and_initialize_artists():
    if Artist.query.count() == 0:  # Check if the artist table is empty
        print("No artists found, initializing...")
        initialize_artists()

# Manually create the database tables when the app starts
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        # Call the function to populate global_resources if empty
        populate_global_resources()
        check_and_initialize_artists()
    port = int(os.environ.get('PORT', 5000))  # Use PORT from environment, default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)

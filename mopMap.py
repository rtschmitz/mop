from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

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

# Manually create the database tables when the app starts
with app.app_context():
    db.create_all()

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
        for target, ap_bid, wealth_bid, recipient, outcome, notes in zip(
                request.form.getlist('artist_bids_target[]'),
                request.form.getlist('artist_bids_ap_bid[]'),
                request.form.getlist('artist_bids_wealth_bid[]'),
                request.form.getlist('artist_bids_recipient[]'),
                request.form.getlist('artist_bids_outcome[]'),
                request.form.getlist('artist_bids_notes[]')):
            artist_bids.append(f"{target}\t{ap_bid}\t{wealth_bid}\t{recipient}\t{outcome}\t{notes}")
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

        # Get the bonus resources from the form
        bonus_spl = float(request.form['bonus_spl'])
        bonus_ap = float(request.form['bonus_ap'])
        bonus_wealth = float(request.form['bonus_wealth'])
        bonus_culture = float(request.form['bonus_culture'])

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
    return render_template('submit_turn.html', houses=houses, global_turn=global_turn)


# Route for users to view released turns only (public)
@app.route('/view_turns')
def view_turns():
    turns = Turn.query.filter_by(status='released').all()
    return render_template('view_turns.html', turns=turns)

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

    turns = Turn.query.all()
    global_turn = GlobalTurn.query.first().turn_number  # Query the global turn number
    return render_template('admin_dashboard.html', turns=turns, global_turn=global_turn)

# Route for viewing the Artist Auction (public for all users)
@app.route('/artist_auction')
def artist_auction():
    # Query all artists from the database to display them in the auction
    artists = Artist.query.all()
    return render_template('artist_auction.html', artists=artists)


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

    if request.method == 'POST':
        city = request.form['city']
        name = request.form['name']
        cp = request.form['cp']
        description = request.form['description']
        special_ability = request.form['special_ability']

        # Add new artist to the database
        new_artist = Artist(
            city=city,
            name=name,
            cp=cp,
            description=description,
            special_ability=special_ability
        )
        db.session.add(new_artist)
        db.session.commit()
        return redirect(url_for('manage_artists'))

    # Query existing artists to edit
    artists = Artist.query.all()
    return render_template('manage_artists.html', artists=artists)

# Route for editing an artist (admin only)
@app.route('/admin/edit_artist/<int:artist_id>', methods=['POST'])
def edit_artist(artist_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    artist = Artist.query.get(artist_id)
    if artist:
        artist.city = request.form['city']
        artist.name = request.form['name']
        artist.cp = request.form['cp']
        artist.description = request.form['description']
        artist.special_ability = request.form['special_ability']
        db.session.commit()
    
    return redirect(url_for('manage_artists'))

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(100))
    cp = db.Column(db.Integer)  # Culture Points
    description = db.Column(db.Text)
    special_ability = db.Column(db.Text)


# Route to edit a specific turn (only for admin)
@app.route('/admin/edit_turn/<int:turn_id>', methods=['GET', 'POST'])
def edit_turn(turn_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    turn = Turn.query.get(turn_id)

    if request.method == 'POST':
        # Update turn fields from the form
        turn.house = request.form['house']
        turn.splendor = float(request.form['splendor'])
        turn.ap = float(request.form['ap'])
        turn.wealth = float(request.form['wealth'])
        turn.culture = float(request.form['culture'])
        turn.actions = request.form['actions']
        turn.artist_bids = request.form['artist_bids']
        turn.income = request.form['income']
        turn.splendor_sources = request.form['splendor_sources']
        turn.bonus_spl = float(request.form['bonus_spl'])
        turn.bonus_ap = float(request.form['bonus_ap'])
        turn.bonus_wealth = float(request.form['bonus_wealth'])
        turn.bonus_culture = float(request.form['bonus_culture'])
        turn.lore = request.form['lore']  # Add lore to be updated


        # Recalculate final resources
        # Parse actions and bids to calculate total costs
        total_ap_spent = sum(float(line.split('\t')[1]) for line in turn.actions.split('\n') if line.split('\t')[1] != '0')
        total_wealth_spent = sum(float(line.split('\t')[2]) for line in turn.actions.split('\n') if line.split('\t')[2] != '0')
        total_culture_spent = sum(float(line.split('\t')[3]) for line in turn.actions.split('\n') if line.split('\t')[3] != '0')

        total_ap_bid = sum(float(line.split('\t')[1]) for line in turn.artist_bids.split('\n') if line.split('\t')[1] != '0')
        total_wealth_bid = sum(float(line.split('\t')[2]) for line in turn.artist_bids.split('\n') if line.split('\t')[2] != '0')

        # Parse income to calculate income values
        total_ap_income = sum(float(line.split('\t')[2]) for line in turn.income.split('\n') if line.split('\t')[2] != '0')
        total_wealth_income = sum(float(line.split('\t')[1]) for line in turn.income.split('\n') if line.split('\t')[1] != '0')

        # Calculate total dynastic splendor from splendor sources
        total_dynastic_splendor = sum(float(line.split('\t')[1]) for line in turn.splendor_sources.split('\n') if line.split('\t')[1] != '0')

        # Update final resources
        turn.final_ap = turn.ap - total_ap_spent - total_ap_bid + total_ap_income + turn.bonus_ap
        turn.final_wealth = turn.wealth - total_wealth_spent - total_wealth_bid + total_wealth_income + turn.bonus_wealth
        turn.final_culture = turn.culture - total_culture_spent + turn.bonus_culture
        turn.final_spl = turn.splendor + total_dynastic_splendor + turn.bonus_spl

        # Save the changes
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_turn.html', turn=turn)

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

if __name__ == '__main__':
    with app.app_context():
        # Call the function to populate global_resources if empty
        populate_global_resources()
    port = int(os.environ.get('PORT', 5000))  # Use PORT from environment, default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)

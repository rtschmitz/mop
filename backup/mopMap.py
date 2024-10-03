from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///turns.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Admin password (simple, static password for demonstration)
ADMIN_PASSWORD = 'adminpassword123'

# Initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define global resources
global_resources = [
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
    {"House": "Vopox", "Spl": 31, "AP": 19, "Wealth": 25, "Culture": 51},
]

# Define Turn model
class Turn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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

# Manually create the database tables when the app starts
with app.app_context():
    db.create_all()

# Route to view global resources (public for all users)
@app.route('/')
def index():
    return render_template('index.html', global_resources=global_resources)

# Route for submitting a turn (public for all users)
@app.route('/submit_turn', methods=['GET', 'POST'])
def submit_turn():
    if request.method == 'POST':
        house = request.form['house']
        splendor = float(request.form['splendor'])
        ap = float(request.form['ap'])
        wealth = float(request.form['wealth'])
        culture = float(request.form['culture'])

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

        # Create new Turn object
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
            final_culture=final_culture
        )

        # Save the data into the database
        db.session.add(new_turn)
        db.session.commit()

        return redirect(url_for('view_turns'))

    return render_template('submit_turn.html')

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

# Admin dashboard (view all turns and release them)
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    turns = Turn.query.all()
    return render_template('admin_dashboard.html', turns=turns)

# Route to release a turn (only for admin)
@app.route('/admin/release_turn/<int:turn_id>')
def release_turn(turn_id):
    if not session.get('admin'):
        return redirect(url_for('admin'))

    turn = Turn.query.get(turn_id)
    if turn:
        turn.status = 'released'
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

# Route to logout the admin
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

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

        # Recalculate final resources
        # Same calculation logic used during submission
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_turn.html', turn=turn)

if __name__ == '__main__':
    app.run(host='169.231.96.145', port=5000, debug=True)


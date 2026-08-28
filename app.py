from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import mysql.connector
import connect
from pathlib import Path

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'te-waihora-fms-local'

start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
START_DATE = start_date.strftime('%Y-%m-%d')
pasture_growth_rate = 65    # kg DM/ha/day
stock_consumption_rate = 14 # kg DM/animal/day

db_connection = None


def initialize_db():
    """Initialize the database connection."""
    global db_connection
    if db_connection is None:
        db_connection = mysql.connector.connect(
            user=connect.dbuser,
            password=connect.dbpass,
            host=connect.dbhost,
            port=3306,
            database=connect.dbname,
            autocommit=True
        )


def getCursor():
    """Gets a new dictionary cursor for the database."""
    global db_connection
    if db_connection is None or not db_connection.is_connected():
        initialize_db()
    cursor = db_connection.cursor(dictionary=True)
    return cursor


# Initialize database connection
initialize_db()


def get_curr_date():
    """Return the simulated FMS date from session."""
    raw = session.get('curr_date', START_DATE)
    if isinstance(raw, str):
        return datetime.strptime(raw, '%Y-%m-%d').date()
    return raw


def calc_age_years(dob, on_date):
    """Age in whole years on a given date."""
    return on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))


def recalc_paddock_totals(cursor, paddock_id, area, dm_per_ha):
    total_dm = round(area * dm_per_ha, 2)
    cursor.execute(
        "UPDATE paddocks SET area = %s, dm_per_ha = %s, total_dm = %s WHERE id = %s",
        (area, dm_per_ha, total_dm, paddock_id),
    )


@app.template_filter('fms_date')
def fms_date_filter(value):
    if not value:
        return ''
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d').date()
    return value.strftime('%d %B %Y')


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/reset-date')
def reset_date():
    """Reset simulated date to the configured start date (today on local build)."""
    session['curr_date'] = START_DATE
    flash(f'Simulated date reset to {datetime.strptime(START_DATE, "%Y-%m-%d").strftime("%d %B %Y")}.', 'info')
    return redirect(request.referrer or url_for('home'))

@app.route("/reset")
def reset():
    """Reset data to original state."""
    THIS_FOLDER = Path(__file__).parent.resolve()
    with open(THIS_FOLDER / 'fms-reset.sql', 'r', encoding='utf-8') as f:
        mqstr = f.read()
        for qstr in mqstr.split(";"):
            if qstr.strip():
                cursor = getCursor()
                cursor.execute(qstr)
    session['curr_date'] = START_DATE
    flash('Database and simulated date have been reset.', 'success')
    return redirect(url_for('paddocks'))

@app.route('/mobs')
def mobs():
    cursor = getCursor()
    cursor.execute("""
        SELECT m.id, m.name, p.name AS paddock, COUNT(s.id) AS num_stock, AVG(s.weight) AS avg_weight
        FROM mobs m
        JOIN paddocks p ON m.paddock_id = p.id
        LEFT JOIN stock s ON m.id = s.mob_id
        GROUP BY m.id, m.name, p.name
        ORDER BY m.name
    """)
    mobs = cursor.fetchall()
    return render_template('mobs.html', mobs=mobs)

@app.route('/paddocks')
def paddocks():
    cursor = getCursor()
    cursor.execute("""
        SELECT p.id, p.name, p.area, p.dm_per_ha, p.total_dm,
               m.name AS mob_name,
               COUNT(s.id) AS num_stock
        FROM paddocks p
        LEFT JOIN mobs m ON m.paddock_id = p.id
        LEFT JOIN stock s ON s.mob_id = m.id
        GROUP BY p.id, p.name, p.area, p.dm_per_ha, p.total_dm, m.name
        ORDER BY p.name
    """)
    paddocks = cursor.fetchall()
    return render_template('paddocks.html', paddocks=paddocks)

@app.route('/stock')
def stock():
    cursor = getCursor()
    curr_date = get_curr_date()

    cursor.execute("""
        SELECT m.id, m.name, p.name AS paddock, COUNT(s.id) AS num_stock, AVG(s.weight) AS avg_weight
        FROM mobs m
        JOIN paddocks p ON m.paddock_id = p.id
        LEFT JOIN stock s ON m.id = s.mob_id
        GROUP BY m.id, m.name, p.name
        ORDER BY m.name
    """)
    mobs_info = cursor.fetchall()

    for mob in mobs_info:
        cursor.execute(
            "SELECT id, dob, weight FROM stock WHERE mob_id = %s ORDER BY id",
            (mob['id'],),
        )
        mob['animals'] = cursor.fetchall()
        for animal in mob['animals']:
            animal['age'] = calc_age_years(animal['dob'], curr_date)

    return render_template('stock.html', mobs=mobs_info)

@app.route('/move_mob', methods=['GET', 'POST'])
def move_mob():
    if request.method == 'POST':
        # Process the move mob form submission
        mob_id = request.form.get('mob_id')
        new_paddock_id = request.form.get('new_paddock_id')
        
        cursor = getCursor()
        cursor.execute("SELECT id FROM mobs WHERE paddock_id = %s", (new_paddock_id,))
        existing_mob = cursor.fetchone()
        
        if existing_mob:
            # Flash an error if the paddock already contains a mob
            flash('The selected paddock already contains a mob.', 'error')
            return redirect(url_for('paddocks'))
        
        try:
            cursor.execute("UPDATE mobs SET paddock_id = %s WHERE id = %s", (new_paddock_id, mob_id))
            flash(
                'Mob moved. Row colour reflects pasture level (DM/ha), not whether a mob is present. '
                'Empty paddocks recover grass when you Advance to next day.',
                'success',
            )
        except mysql.connector.Error as e:
            # Flash an error if there was a problem moving the mob
            flash(f'An error occurred while moving the mob: {e}', 'error')
            return redirect(url_for('paddocks'))
        return redirect(url_for('paddocks'))
    else:
        # GET request to show the move mob form
        cursor = getCursor()
        cursor.execute("SELECT id, name FROM mobs")
        mobs = cursor.fetchall()
        cursor.execute("SELECT id, name FROM paddocks")
        paddocks = cursor.fetchall()
        return render_template('move_mobs.html', mobs=mobs, paddocks=paddocks)

@app.route('/edit_paddocks', methods=['GET', 'POST'])
def edit_paddocks():
    if request.method == 'POST':
        cursor = getCursor()
        try:
            for key in request.form:
                if key.startswith('area_'):
                    paddock_id = int(key.replace('area_', ''))
                    new_area = float(request.form[key])
                    dm_key = f"dm_per_ha_{paddock_id}"
                    new_dm_per_ha = float(request.form[dm_key])
                    recalc_paddock_totals(cursor, paddock_id, new_area, new_dm_per_ha)

            new_paddock_name = request.form.get('new_paddock_name', '').strip()
            new_area = request.form.get('new_area')
            new_dm_per_ha = request.form.get('new_dm_per_ha')

            if new_paddock_name and new_area and new_dm_per_ha:
                area = float(new_area)
                dm_per_ha = float(new_dm_per_ha)
                total_dm = round(area * dm_per_ha, 2)
                cursor.execute(
                    "INSERT INTO paddocks (name, area, dm_per_ha, total_dm) VALUES (%s, %s, %s, %s)",
                    (new_paddock_name, area, dm_per_ha, total_dm),
                )
                flash('New paddock added.', 'success')
            else:
                flash('Paddock details updated.', 'success')
        except (ValueError, TypeError):
            flash('Please enter valid numbers.', 'error')
            return redirect(url_for('edit_paddocks'))
        except Exception as e:
            flash(f'Update failed: {e}', 'error')
            return redirect(url_for('edit_paddocks'))
        return redirect(url_for('paddocks'))
    else:
        # GET request to show the edit paddocks form
        cursor = getCursor()
        cursor.execute("SELECT * FROM paddocks ORDER BY name")
        paddocks = cursor.fetchall()
        return render_template('edit_paddocks.html', paddocks=paddocks)

@app.route('/advance_date', methods=['POST'])
def advance_date():
    curr = get_curr_date() + timedelta(days=1)
    session['curr_date'] = curr.strftime('%Y-%m-%d')

    cursor = getCursor()
    cursor.execute("""
        SELECT p.id, p.area, p.total_dm, COUNT(s.id) AS num_stock
        FROM paddocks p
        LEFT JOIN mobs m ON p.id = m.paddock_id
        LEFT JOIN stock s ON m.id = s.mob_id
        GROUP BY p.id, p.area, p.total_dm
    """)
    paddocks = cursor.fetchall()

    for paddock in paddocks:
        growth = paddock['area'] * pasture_growth_rate
        consumption = paddock['num_stock'] * stock_consumption_rate if paddock['num_stock'] else 0
        total_dm = max(paddock['total_dm'] + growth - consumption, 0)
        dm_per_ha = round(total_dm / paddock['area'], 2)
        cursor.execute(
            "UPDATE paddocks SET total_dm = %s, dm_per_ha = %s WHERE id = %s",
            (total_dm, dm_per_ha, paddock['id']),
        )

    flash(f'Date advanced to {curr.strftime("%d %B %Y")}. Pasture levels updated.', 'info')
    return redirect(url_for('paddocks'))

@app.route('/test_db')
def test_db():
    # Test the database connection
    cursor = getCursor()
    cursor.execute("SELECT VERSION()")
    result = cursor.fetchone()
    return f"Database Version: {result['VERSION()']}"

@app.route('/edit_animal/<int:animal_id>')
def edit_animal(animal_id):
    # Retrieve an animal's details for editing
    cursor = getCursor()
    cursor.execute("SELECT * FROM stock WHERE id = %s", (animal_id,))
    animal = cursor.fetchone()

    if animal is None:
        return "Animal not found"

    return render_template('edit_animal.html', animal=animal)

# Route for updating animal information
@app.route('/update_animal/<int:animal_id>', methods=['POST'])
def update_animal(animal_id):
    cursor = getCursor()
    data = request.form
    cursor.execute(
        "UPDATE stock SET dob = %s, weight = %s WHERE id = %s",
        (data['dob'], data['weight'], animal_id)
    )
    return redirect(url_for('stock'))

@app.route('/update_paddock/<int:paddock_id>', methods=['POST'])
def update_paddock(paddock_id):
    # Update paddock's area and DM/ha
    new_area = request.form.get('new_area')
    new_dm_per_ha = request.form.get('new_dm_per_ha')

    try:
        new_area = float(new_area)
        new_dm_per_ha = float(new_dm_per_ha)
    except ValueError:
        # Flash an error if the input is invalid
        flash('Area and DM/ha must be numbers.', 'error')
        return redirect(url_for('edit_paddocks'))

    cursor = getCursor()
    cursor.execute("UPDATE paddocks SET area = %s, dm_per_ha = %s, total_dm = %s WHERE id = %s",
                   (new_area, new_dm_per_ha, round(new_area * new_dm_per_ha, 2), paddock_id))
    # Flash a success message
    flash('Paddock updated successfully.', 'success')
    return redirect(url_for('edit_paddocks'))

@app.before_request
def before_request():
    session.setdefault('curr_date', START_DATE)
    global db_connection
    if db_connection is not None and not db_connection.is_connected():
        initialize_db()

@app.teardown_request
def teardown_request(exception=None):
    global db_connection
    if db_connection is not None and db_connection.is_connected():
        db_connection.close()
        db_connection = None

if __name__ == '__main__':
    app.run(debug=True)
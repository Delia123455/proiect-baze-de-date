from flask import Flask, render_template, request, redirect, abort
from db import get_db_connection

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('meniu_principal.html')

# PACIENTI
@app.route('/pacienti')
def pacienti():
    conn = get_db_connection()
    if conn is None:
        return "Eroare la conectarea la baza de date!"
    cursor = conn.cursor(dictionary=True)

    pacient_edit = None
    edit_id = request.args.get('edit')
    if edit_id:
        cursor.execute("SELECT * FROM pacienti WHERE id_pacient = %s", (edit_id,)) # interogare intra-tabel(clauza secundara)
        pacient_edit = cursor.fetchone()

    cursor.execute("SELECT * FROM pacienti") # interogare intra-tabel
    pacienti = cursor.fetchall()
    conn.close()
    return render_template('pacienti.html', pacienti=pacienti, pacient_edit=pacient_edit)


@app.route('/adauga_pacient', methods=['POST'])
def adauga_pacient():
    id_pacient = request.form.get('id_pacient') 

    nume = request.form.get('nume')
    prenume = request.form.get('prenume')
    varsta = request.form.get('varsta')
    adresa = request.form.get('adresa')
    nr_telefon = request.form.get('nr_telefon')
    email = request.form.get('email')

    conn = get_db_connection()
    cursor = conn.cursor()

    if id_pacient:
        cursor.execute("""
            UPDATE pacienti
            SET nume=%s, prenume=%s, varsta=%s, adresa=%s, nr_telefon=%s, email=%s
            WHERE id_pacient=%s
        """, (nume, prenume, varsta, adresa, nr_telefon, email, id_pacient))
    else:
        cursor.execute("""
            INSERT INTO pacienti (nume, prenume, varsta, adresa, nr_telefon, email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (nume, prenume, varsta, adresa, nr_telefon, email))

    conn.commit()
    conn.close()
    return redirect('/pacienti')


@app.route('/sterge_pacient/<int:id>')
def sterge_pacient(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pacienti WHERE id_pacient = %s", (id,))
        conn.commit()
        conn.close()
    except Exception as e:
        return f"Eroare la ștergere: {e}", 500
    return redirect('/pacienti')


# MEDICI
@app.route('/medici')
def medici():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM medici")
    medici = cursor.fetchall()
    conn.close()
    return render_template('medici.html', medici=medici)

@app.route('/adauga_medic', methods=['POST'])
def adauga_medic():
    grad = request.form.get('grad')
    nume = request.form.get('nume')
    prenume = request.form.get('prenume')
    nr_telefon = request.form.get('nr_telefon')
    departamente = request.form.get('departamente')
    if not all([grad, nume, prenume, nr_telefon, departamente]):
        return "Toate câmpurile sunt obligatorii!", 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO medici (grad, nume, prenume, nr_telefon, departamente)
        VALUES (%s, %s, %s, %s, %s)
    """, (grad, nume, prenume, nr_telefon, departamente))
    conn.commit()
    conn.close()
    return redirect('/medici')

@app.route('/editeaza_medic/<int:id>', methods=['POST'])
def editeaza_medic(id):
    grad = request.form.get('grad')
    nume = request.form.get('nume')
    prenume = request.form.get('prenume')
    nr_telefon = request.form.get('nr_telefon')
    departamente = request.form.get('departamente')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE medici SET grad=%s, nume=%s, prenume=%s, nr_telefon=%s, departamente=%s
        WHERE id_medic=%s
    """, (grad, nume, prenume, nr_telefon, departamente, id))
    conn.commit()
    conn.close()
    return redirect('/medici')

@app.route('/sterge_medic/<int:id>')
def sterge_medic(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM medici WHERE id_medic = %s", (id,))
    conn.commit()
    conn.close()
    return redirect('/medici')

# PROGRAMARI
@app.route('/programari')
def programari():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # interogare inter_tabele
    cursor.execute("""
        SELECT pr.id_programare, pr.data_programare, pr.ora_programare, pr.stare,
               p.id_pacient, p.nume AS nume_pacient, p.prenume AS prenume_pacient,
               m.id_medic, m.nume AS nume_medic, m.prenume AS prenume_medic,
               r.id_receipt, r.total_plata, r.status
        FROM programari pr
        JOIN pacienti_receipts_programari prp ON pr.id_programare = prp.programare_id
        JOIN pacienti p ON prp.pacient_id = p.id_pacient
        JOIN medici m ON pr.id_medic = m.id_medic
        JOIN receipts r ON prp.receipt_id = r.id_receipt
        ORDER BY pr.data_programare, pr.ora_programare
    """)                                                    
    programari = cursor.fetchall()

    cursor.execute("SELECT id_pacient, nume, prenume FROM pacienti ORDER BY nume, prenume")
    pacienti = cursor.fetchall()

    cursor.execute("SELECT id_medic, nume, prenume FROM medici ORDER BY nume, prenume")
    medici = cursor.fetchall()

    conn.close()
    return render_template('programari.html', programari=programari, pacienti=pacienti, medici=medici)


@app.route('/adauga_programare', methods=['POST'])
def adauga_programare():
    id_pacient = request.form.get('id_pacient')
    id_medic = request.form.get('id_medic')
    data = request.form.get('data_programare')
    ora = request.form.get('ora_programare')
    stare = request.form.get('stare')

    if not (id_pacient and id_medic and data and ora and stare):
        return "Toate câmpurile sunt obligatorii!", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT CONCAT(nume, ' ', prenume) FROM pacienti WHERE id_pacient = %s
    """, (id_pacient,))
    pacient_nume = cursor.fetchone()
    patient_name = pacient_nume[0] if pacient_nume else "Nedefinit"

    total_plata = 0
    status = 'neachitat'

    cursor.execute("""
        INSERT INTO receipts (patient_name, total_plata, status)
        VALUES (%s, %s, %s)
    """, (patient_name, total_plata, status))
    receipt_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO programari (data_programare, ora_programare, stare, id_medic)
        VALUES (%s, %s, %s, %s)
    """, (data, ora, stare, id_medic))
    id_programare = cursor.lastrowid

    cursor.execute("""
        INSERT INTO pacienti_receipts_programari (receipt_id, pacient_id, programare_id)
        VALUES (%s, %s, %s)
    """, (receipt_id, id_pacient, id_programare))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/programari')


@app.route('/editeaza_programare/<int:id>', methods=['POST'])
def editeaza_programare(id):
    data = request.form.get('data_programare')
    ora = request.form.get('ora_programare')
    stare = request.form.get('stare')
    id_pacient = request.form.get('id_pacient')
    id_medic = request.form.get('id_medic')

    if not (data and ora and stare and id_pacient and id_medic):
        return "Toate câmpurile sunt obligatorii!", 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE programari
        SET data_programare=%s, ora_programare=%s, stare=%s, id_medic=%s
        WHERE id_programare=%s
    """, (data, ora, stare, id_medic, id))

    cursor.execute("""
        SELECT receipt_id FROM pacienti_receipts_programari WHERE programare_id=%s
    """, (id,))
    receipt_row = cursor.fetchone()
    receipt_id = receipt_row[0] if receipt_row else None

    # Sterge vechea legatura
    cursor.execute("""
        DELETE FROM pacienti_receipts_programari WHERE programare_id=%s
    """, (id,))

    if receipt_id is None:
        cursor.execute("""
            SELECT CONCAT(nume, ' ', prenume) FROM pacienti WHERE id_pacient = %s
        """, (id_pacient,))
        pacient_nume = cursor.fetchone()
        patient_name = pacient_nume[0] if pacient_nume else "Nedefinit"
        total_plata = 0
        status = 'neachitat'
        cursor.execute("""
            INSERT INTO receipts (patient_name, total_plata, status) VALUES (%s, %s, %s)
        """, (patient_name, total_plata, status))
        receipt_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO pacienti_receipts_programari (receipt_id, pacient_id, programare_id)
        VALUES (%s, %s, %s)
    """, (receipt_id, id_pacient, id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/programari')


@app.route('/sterge_programare/<int:id>')
def sterge_programare(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM pacienti_receipts_programari WHERE programare_id = %s", (id,))
    cursor.execute("DELETE FROM programari WHERE id_programare = %s", (id,))

    conn.commit()
    conn.close()

    return redirect('/programari')

# RECEIPTS

@app.route('/plati')
def plati():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Selectam doar chitantele pentru pacientii existenti in tabelul pacienti
    query = """
        SELECT r.id_receipt, r.patient_name, r.total_plata, r.status
        FROM receipts r
        INNER JOIN pacienti p ON r.patient_name = p.nume
    """
    cursor.execute(query)
    receipts = cursor.fetchall()
    
    # Preluam toti pacientii pentru lista de selectie în formular
    cursor.execute("SELECT id_pacient, nume FROM pacienti")
    pacienti = cursor.fetchall()
    
    # Preluam toate interventiile pentru lista de selectie în formular
    cursor.execute("SELECT id_interventie, nume_boala FROM interventii")
    interventii = cursor.fetchall()
    
    conn.close()
    return render_template('receipts.html', receipts=receipts, pacienti=pacienti, interventii=interventii)


@app.route('/adauga_receipt', methods=['POST'])
def adauga_receipt():
    patient_id = request.form.get('patient_name')  
    total_plata = request.form.get('total_plata')
    status = request.form.get('status')
    interventie_id = request.form.get('interventie')  # doar pentru afișare, nu se salvează
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nume FROM pacienti WHERE id_pacient = %s", (patient_id,))
    pacient = cursor.fetchone()
    if pacient:
        nume_pacient = pacient[0]
    else:
        nume_pacient = "Necunoscut"
    
    cursor.execute("""
        INSERT INTO receipts (patient_name, total_plata, status)
        VALUES (%s, %s, %s)
    """, (nume_pacient, total_plata, status))
    
    conn.commit()
    conn.close()
    return redirect('/plati')


@app.route('/sterge_receipt/<int:id_receipt>', methods=['POST'])
def sterge_receipt(id_receipt):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM receipts WHERE id_receipt = %s", (id_receipt,))
    conn.commit()
    conn.close()
    return redirect('/plati')


# INTERVENTII
@app.route('/interventii', methods=['GET', 'POST'])
def interventii():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id_pacient, nume, prenume FROM pacienti ORDER BY nume, prenume") # interogare intra-tabel(clauza secundara)
    pacienti = cursor.fetchall()

    cursor.execute("SELECT id_medic, nume, prenume FROM medici ORDER BY nume, prenume") # interogare intra-tabel(clauza secundara)
    medici = cursor.fetchall()

    if request.method == 'POST':
        id_interventie = request.form.get('id_interventie')
        id_pacient = request.form.get('id_pacient')
        id_medic = request.form.get('id_medic')
        nume_boala = request.form.get('nume_boala')
        diagnostic = request.form.get('diagnostic')
        nivel_gravitate = request.form.get('nivel_gravitate')

        if id_interventie:  
            cursor.execute("""
                UPDATE interventii 
                SET id_pacient=%s, id_medic=%s, nume_boala=%s, diagnostic=%s, nivel_gravitate=%s
                WHERE id_interventie=%s
            """, (id_pacient, id_medic, nume_boala, diagnostic, nivel_gravitate, id_interventie))
        else: 
            cursor.execute("""
                INSERT INTO interventii (id_pacient, id_medic, nume_boala, diagnostic, nivel_gravitate)
                VALUES (%s, %s, %s, %s, %s)
            """, (id_pacient, id_medic, nume_boala, diagnostic, nivel_gravitate))

        conn.commit()

    cursor.execute("""
    SELECT                                                 
        i.id_interventie,
        i.nume_boala,
        i.diagnostic,
        i.nivel_gravitate,
        p.nume AS nume_pacient,
        p.prenume AS prenume_pacient,
        m.nume AS nume_medic,
        m.prenume AS prenume_medic
    FROM interventii i
    JOIN pacienti p ON i.id_pacient = p.id_pacient
    JOIN medici m ON i.id_medic = m.id_medic
    ORDER BY i.id_interventie DESC
""")                                                            # interogare inter-tabele                                                                                      
    interventii = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('interventii.html', interventii=interventii, pacienti=pacienti, medici=medici)


@app.route('/sterge_interventie/<int:id>', methods=['POST'])
def sterge_interventie(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interventii WHERE id_interventie = %s", (id,))
    conn.commit()
    conn.close()
    return redirect('/interventii')


if __name__ == '__main__':
    app.run(debug=True)
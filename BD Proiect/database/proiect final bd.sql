CREATE DATABASE centru_medical;
SHOW DATABASES;
SELECT DATABASE();
USE centru_medical;
SHOW TABLES;


CREATE TABLE interventii(
    id_interventie INT PRIMARY KEY AUTO_INCREMENT,
    id_pacient INT,
    id_medic INT,
    nume_boala VARCHAR(45) NOT NULL,
    diagnostic TEXT NOT NULL,
    nivel_gravitate VARCHAR(45) NOT NULL,
    FOREIGN KEY (id_pacient) REFERENCES pacienti(id_pacient) ON DELETE CASCADE,
    FOREIGN KEY (id_medic) REFERENCES medici(id_medic) ON DELETE CASCADE
);


CREATE TABLE receipts(
    id_receipt INT PRIMARY KEY AUTO_INCREMENT,
    patient_name VARCHAR(45) NOT NULL,
    total_plata INT NOT NULL,
    status VARCHAR(45) NOT NULL
);


CREATE TABLE medici(
    id_medic INT PRIMARY KEY AUTO_INCREMENT,
    grad VARCHAR(45),
    nume VARCHAR(45) NOT NULL,
    prenume VARCHAR(45) NOT NULL,
    nr_telefon VARCHAR(20) CHECK (CHAR_LENGTH(nr_telefon) >= 10),
    departamente VARCHAR(100) CHECK (departamente IN ('cardiologie', 'neurologie', 'pediatrie', 'dermatologie', 'oncologie',
    'infectioase', 'endocrinologie', 'psihiatrie', 'ATI'))
);


CREATE TABLE pacienti(
    id_pacient INT PRIMARY KEY AUTO_INCREMENT,
    id_interventie INT,
    id_medic INT,
    nume VARCHAR(45),
    prenume VARCHAR(45),
    varsta INT,
    adresa VARCHAR(45),
    nr_telefon VARCHAR(20) CHECK (CHAR_LENGTH(nr_telefon) >= 10),
    email VARCHAR(45) UNIQUE
);


CREATE TABLE programari(
    id_programare INT PRIMARY KEY AUTO_INCREMENT,
    data_programare DATE NOT NULL,
    ora_programare TIME NOT NULL,
    stare VARCHAR(20) CHECK (stare IN ('programata', 'anulata', 'finalizata')),
    id_medic INT,
    FOREIGN KEY (id_medic) REFERENCES medici(id_medic)
);

CREATE TABLE pacienti_receipts_programari (
    receipt_id INT,
    pacient_id INT,
    programare_id INT,
    CONSTRAINT cmp_pk PRIMARY KEY (receipt_id, pacient_id, programare_id),
    FOREIGN KEY (receipt_id) REFERENCES receipts(id_receipt) ON DELETE CASCADE,
    FOREIGN KEY (pacient_id) REFERENCES pacienti(id_pacient) ON DELETE CASCADE,
    FOREIGN KEY (programare_id) REFERENCES programari(id_programare) ON DELETE CASCADE
);


INSERT INTO medici(grad, nume, prenume, nr_telefon, departamente)
VALUES 
('Primar', 'Taricescu', 'Marcel', '0712345678', 'cardiologie'),
('Specialist', 'Dumitrache', 'Pavel', '0723456789', 'dermatologie'),
('Rezident', 'Pandache', 'Daniela', '0734567890', 'neurologie'),
('Primar', 'Alexandrescu', 'Laura', '0712345338', 'oncologie'),
('Specialist', 'Popescu', 'Octavian', '0723996719', 'infectioase'),
('Primar', 'Firmino', 'Roberto', '0712746278', 'ATI'),
('Specialist', 'Giovanni', 'Mario', '0723111789', 'pediatrie'),
('Specialist', 'Maroi', 'Marius', '0723456654', 'psihiatrie'),
('Rezident', 'Davidescu', 'Carmen', '0734771182', 'endocrinologie');

-- functie scalara: formateaza numele complet al medicului
SELECT id_pacient, CONCAT(nume, ' ', prenume) AS nume_complet,
       CHAR_LENGTH(nume) AS lungime_nume
FROM pacienti;

-- functie agregat: calc suma totala
SELECT SUM(total_plata) AS total_incasari
FROM receipts;

-- trigger
DELIMITER $$

CREATE TRIGGER trg_verifica_nivel_gravitate
BEFORE INSERT ON interventii
FOR EACH ROW
BEGIN
    IF NEW.nivel_gravitate < 1 OR NEW.nivel_gravitate > 5 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Nivelul de gravitate trebuie să fie între 1 și 5';
    END IF;
END$$

DELIMITER ;

-- sub-interogare
SELECT p.data_programare, p.ora_programare
FROM programari p
WHERE p.id_programare IN (
    SELECT prp.programare_id
    FROM pacienti_receipts_programari prp
    JOIN pacienti pa ON prp.pacient_id = pa.id_pacient
    WHERE pa.varsta > 50
);